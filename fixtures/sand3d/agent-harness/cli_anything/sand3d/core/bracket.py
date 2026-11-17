"""The upstream Sand3D bracket example as a one-shot GLB export."""

from pathlib import Path
import struct


def export_bracket(output: Path, w: float, d: float, t: float,
                   hole_d: float, pitch: float) -> dict:
    """Build the documented bracket with Sand3D verbs and export a real GLB."""
    import sand3d as s3d

    output = output.expanduser().resolve()
    if output.suffix.lower() != ".glb":
        raise ValueError("output path must end in .glb")
    output.parent.mkdir(parents=True, exist_ok=True)

    plate = s3d.extrude("plate", s3d.rect(w, d, r=4), t)
    s3d.hole(plate, hole_d, on=s3d.grid(2, 1, pitch, 0))
    s3d.fillet(plate, 1, edges="top")
    s3d.export(plate, output)

    with output.open("rb") as glb:
        header = glb.read(12)
    size = output.stat().st_size
    if len(header) != 12 or header[:4] != b"glTF" or struct.unpack_from("<II", header, 4) != (2, size):
        raise RuntimeError(f"Sand3D did not produce a valid GLB header: {output}")

    return {
        "output": str(output),
        "format": "glb",
        "bytes": size,
        "dimensions_mm": {"w": w, "d": d, "t": t, "hole_d": hole_d, "pitch": pitch},
    }
