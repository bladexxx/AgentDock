"""One-shot CLI for the documented Sand3D bracket."""

from contextlib import redirect_stdout
import json
from pathlib import Path
import sys

import click

from cli_anything.sand3d.core.bracket import export_bracket


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Print a JSON summary.")
@click.pass_context
def main(ctx: click.Context, json_output: bool) -> None:
    """Build a Sand3D model and export a GLB."""
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output


@main.command()
@click.option("-o", "--output", type=click.Path(path_type=Path, dir_okay=False),
              default=Path("bracket.glb"), show_default=True, help="GLB output path.")
@click.option("--w", type=click.FloatRange(min=0, min_open=True), default=80.0, show_default=True,
              help="Plate width in millimetres.")
@click.option("--d", type=click.FloatRange(min=0, min_open=True), default=40.0, show_default=True,
              help="Plate depth in millimetres.")
@click.option("--t", type=click.FloatRange(min=0, min_open=True), default=6.0, show_default=True,
              help="Plate thickness in millimetres.")
@click.option("--hole-d", type=click.FloatRange(min=0, min_open=True), default=6.6, show_default=True,
              help="Hole diameter in millimetres.")
@click.option("--pitch", type=click.FloatRange(min=0, min_open=True), default=50.0, show_default=True,
              help="Hole pitch in millimetres.")
@click.pass_context
def bracket(ctx: click.Context, output: Path, w: float, d: float, t: float,
            hole_d: float, pitch: float) -> None:
    """Export the upstream example's two-hole mounting bracket."""
    try:
        # Blender's glTF exporter writes progress to stdout.
        with redirect_stdout(sys.stderr):
            summary = export_bracket(output, w, d, t, hole_d, pitch)
    except (OSError, RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if ctx.obj["json_output"]:
        click.echo(json.dumps(summary, sort_keys=True))
    else:
        click.echo(f"Wrote {summary['output']} ({summary['bytes']} bytes)")


if __name__ == "__main__":
    main()
