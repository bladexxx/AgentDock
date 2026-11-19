"""Check the Sand3D bracket's GLB container and plate geometry."""

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct


FIXTURE_VERSION = "sand3d-bracket-2"
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
# The upstream example is 80 × 40 × 6 mm. Blender exports glTF with Y up.
EXPECTED_EXTENT_METRES = (0.080, 0.006, 0.040)
HOLE_CENTERS_X_METRES = (-0.025, 0.025)


def read_chunk(contents, offset, expected_type):
    length, kind = struct.unpack_from("<I4s", contents, offset)
    start = offset + 8
    end = start + length
    if kind != expected_type or not length or length % 4 or end > len(contents):
        raise ValueError(f"Invalid GLB {expected_type!r} chunk")
    return contents[start:end], end


def read_glb(contents):
    if struct.unpack_from("<4sII", contents) != (b"glTF", 2, len(contents)):
        raise ValueError("Expected a complete GLB 2 container")
    json_chunk, offset = read_chunk(contents, 12, b"JSON")
    binary, end = read_chunk(contents, offset, b"BIN\0")
    if end != len(contents):
        raise ValueError("Unexpected data after the bracket GLB's BIN chunk")
    doc = json.loads(json_chunk.decode("utf-8"))
    if doc["asset"]["version"] != "2.0" or doc.get("extensionsRequired"):
        raise ValueError("Expected a glTF 2.0 asset without required extensions")
    buffer, = doc["buffers"]
    length = natural(buffer["byteLength"])
    if "uri" in buffer or not 0 <= len(binary) - length <= 3 or any(binary[length:]):
        raise ValueError("Invalid embedded bracket buffer")
    return doc, binary[:length]


def natural(value):
    if type(value) is not int or value < 0:
        raise ValueError("Expected a nonnegative integer in glTF")
    return value


def accessor_values(doc, binary, accessor_index, shape, formats):
    accessor = doc["accessors"][natural(accessor_index)]
    if accessor["type"] != shape or accessor.get("normalized") or "sparse" in accessor:
        raise ValueError(f"Expected a plain {shape} mesh accessor")
    layout = struct.Struct(formats[accessor["componentType"]])
    view = doc["bufferViews"][natural(accessor["bufferView"])]
    start = natural(view.get("byteOffset", 0))
    length = natural(view["byteLength"])
    offset = natural(accessor.get("byteOffset", 0))
    count = natural(accessor["count"])
    if (
        natural(view["buffer"]) != 0
        or "byteStride" in view
        or not count
        or start + length > len(binary)
        or offset + count * layout.size > length
    ):
        raise ValueError("Mesh accessor exceeds or misuses its embedded buffer view")
    start += offset
    return list(layout.iter_unpack(binary[start:start + count * layout.size]))


def check_plate(doc, binary):
    scene = doc["scenes"][natural(doc.get("scene", 0))]
    plate_index, = scene["nodes"]
    plate = doc["nodes"][natural(plate_index)]
    if plate.get("name") != "plate" or any(
        key in plate for key in ("children", "matrix", "rotation", "translation", "skin")
    ):
        raise ValueError("Expected a single plate in the default scene")
    scale = plate.get("scale", [1, 1, 1])
    if not isinstance(scale, list) or len(scale) != 3 or not all(
        type(factor) in (int, float) and math.isfinite(factor) and factor > 0 for factor in scale
    ):
        raise ValueError("Expected a positive plate scale")
    primitive, = doc["meshes"][natural(plate["mesh"])]["primitives"]
    if primitive.get("mode", 4) != 4:
        raise ValueError("Expected a triangle plate mesh")
    positions = accessor_values(doc, binary, primitive["attributes"]["POSITION"], "VEC3", {5126: "<fff"})
    indices = accessor_values(doc, binary, primitive["indices"], "SCALAR", {5121: "<B", 5123: "<H", 5125: "<I"})
    if len(indices) < 3 or len(indices) % 3 or any(index >= len(positions) for index, in indices):
        raise ValueError("Invalid plate triangle indices")

    vertices = [tuple(value * factor for value, factor in zip(positions[index], scale))
                for index, in indices]
    if any(not math.isfinite(value) for p in vertices for value in p):
        raise ValueError("Non-finite plate vertex")
    triangles = list(zip(vertices[::3], vertices[1::3], vertices[2::3]))
    extents = [max(axis) - min(axis) for axis in zip(*vertices)]
    if not all(math.isclose(actual, expected, rel_tol=0, abs_tol=0.00001)
               for actual, expected in zip(extents, EXPECTED_EXTENT_METRES)):
        raise ValueError(f"Wrong plate dimensions in metres (X, Y, Z): {extents}")
    if not any(covers_xz(triangle, (0, 0)) for triangle in triangles):
        raise ValueError("Expected plate material between the holes")
    if any(covers_xz(triangle, (x, 0)) for triangle in triangles for x in HOLE_CENTERS_X_METRES):
        raise ValueError("Expected two through holes at 50 mm pitch")
    check_plate_surface(triangles)
    return {
        "name": "plate",
        "triangles": len(triangles),
        "extentMetres": extents,
        "holeCentersXMetres": HOLE_CENTERS_X_METRES,
    }


def connected_vertices(neighbours, start):
    seen = {start}
    pending = [start]
    while pending:
        for vertex in neighbours[pending.pop()]:
            if vertex not in seen:
                seen.add(vertex)
                pending.append(vertex)
    return seen


def check_plate_surface(triangles):
    # glTF can split vertices at shading seams. Weld coincident positions first.
    ids = {}
    edges = defaultdict(list)
    links = defaultdict(lambda: defaultdict(set))
    for triangle in triangles:
        a, b, c = [ids.setdefault(point, len(ids)) for point in triangle]
        p, q, r = triangle
        ux, uy, uz = (right - left for left, right in zip(p, q))
        vx, vy, vz = (right - left for left, right in zip(p, r))
        if not any((uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)):
            raise ValueError("Degenerate plate triangle")
        for vertex, start, end in ((a, b, c), (b, c, a), (c, a, b)):
            edges[tuple(sorted((start, end)))].append(start < end)
            links[vertex][start].add(end)
            links[vertex][end].add(start)

    if any(sorted(directions) != [False, True] for directions in edges.values()):
        raise ValueError("Expected an oriented closed surface for the plate")
    for link in links.values():
        if len(connected_vertices(link, next(iter(link)))) != len(link):
            raise ValueError("Expected one surface fan at each plate vertex")
    if len(connected_vertices(links, 0)) != len(ids):
        raise ValueError("Expected a connected closed surface for the plate")

    # A connected orientable closed surface with two tunnels has Euler characteristic -2.
    if len(ids) - len(edges) + len(triangles) != -2:
        raise ValueError("Expected two enclosed through holes in the plate")
    check_section(triangles, ids)


def check_section(triangles, ids):
    """Verify both clear thickness rays lie inside distinct bounded cutouts."""
    heights = {point[1] for point in ids}
    height = (min(heights) + max(heights)) / 2
    while height in heights:
        height = math.nextafter(height, math.inf)

    points = {}
    neighbours = defaultdict(set)
    for a, b, c in triangles:
        crossings = []
        for start, end in ((a, b), (b, c), (c, a)):
            if (start[1] < height) == (end[1] < height):
                continue
            edge = tuple(sorted((ids[start], ids[end])))
            if edge not in points:
                factor = (height - start[1]) / (end[1] - start[1])
                points[edge] = (start[0] + factor * (end[0] - start[0]),
                                start[2] + factor * (end[2] - start[2]))
            crossings.append(edge)
        if crossings:
            left, right = crossings
            neighbours[left].add(right)
            neighbours[right].add(left)

    # Closed oriented mesh edges yield loops in a section that avoids mesh vertices.
    remaining = set(points)
    contours = []
    while remaining:
        first = next(iter(remaining))
        contour = connected_vertices(neighbours, first)
        remaining.difference_update(contour)
        contours.append(contour)

    def containing(x):
        result = set()
        for index, contour in enumerate(contours):
            crossings = 0
            for start in contour:
                x1, z1 = points[start]
                for end in neighbours[start]:
                    x2, z2 = points[end]
                    if start < end and (z1 > 0) != (z2 > 0):
                        intersection = x1 - z1 * (x2 - x1) / (z2 - z1)
                        crossings += intersection > x
            if crossings % 2:
                result.add(index)
        return result

    outer = containing(0)
    hole_contours = [containing(x) for x in HOLE_CENTERS_X_METRES]
    if (len(contours) != 3 or len(outer) != 1 or hole_contours[0] == hole_contours[1]
            or any(len(hole) != 2 or not outer <= hole for hole in hole_contours)):
        raise ValueError("Expected two distinct enclosed through holes in the plate")


def covers_xz(triangle, point):
    """Whether a ray down the thickness axis intersects this projected triangle."""
    a, b, c = [(x, z) for x, _, z in triangle]

    def side(start, end, target):
        return ((end[0] - start[0]) * (target[1] - start[1])
                - (end[1] - start[1]) * (target[0] - start[0]))

    if abs(side(a, b, c)) < 1e-14:
        return False
    signs = (side(a, b, point), side(b, c, point), side(c, a, point))
    return min(signs) >= -1e-14 or max(signs) <= 1e-14


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path, help="bracket GLB exported by the container")
    args = parser.parse_args()
    result = {"fixtureVersion": FIXTURE_VERSION}
    try:
        with args.glb.open("rb") as file:
            contents = file.read(MAX_ARTIFACT_BYTES + 1)
        if len(contents) > MAX_ARTIFACT_BYTES:
            raise ValueError("GLB exceeds the fixture's 4 MiB limit")
        doc, binary = read_glb(contents)
        result["plate"] = check_plate(doc, binary)
    except (OSError, ValueError, TypeError, LookupError, AttributeError, OverflowError, RecursionError, struct.error) as error:
        print(json.dumps({**result, "result": "failed", "error": str(error)}))
        return 1
    print(json.dumps({**result, "result": "passed", "artifactSha256": hashlib.sha256(contents).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
