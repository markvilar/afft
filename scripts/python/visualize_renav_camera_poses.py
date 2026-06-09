"""
Visualize Renav stereo camera poses grouped by dive site.

Scans an input directory for CSV files matching the pattern
*_renav_stereo_poses.csv, groups them by site ID (the leading token of the
filename before the first date component), and writes one PNG per site to the
output directory.

Each figure contains a single map panel with all deployment tracks overlaid in
UTM metres, colour-coded by deployment.

Usage:
    uv run python scripts/python/visualize_renav_camera_poses.py \\
        --input /home/martin/data/acfr_camera_poses_renav_v2_parsed \\
        --output /home/martin/data/acfr_camera_poses_plots
"""

from pathlib import Path

import click
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from pyproj import CRS


_FILE_SUFFIX: str = "_renav_stereo_poses.csv"

_REQUIRED_COLUMNS: list[str] = [
    "timestamp",
    "latitude",
    "longitude",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--input",
    "input_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing *_renav_stereo_poses.csv files.",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory to write per-site PNG figures.",
)
@click.option(
    "--dpi",
    default=300,
    show_default=True,
    help="Output figure resolution in dots per inch.",
)
def main(input_dir: Path, output_dir: Path, dpi: int) -> None:
    """Render Renav camera pose maps grouped by dive site."""
    groups: dict[str, list[Path]] = _group_files_by_site(input_dir)
    if not groups:
        click.echo(f"No *{_FILE_SUFFIX} files found in {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for site_id, paths in sorted(groups.items()):
        click.echo(f"Site {site_id}: {len(paths)} deployment(s)")
        deployments: list[tuple[str, pd.DataFrame]] = []
        for path in sorted(paths):
            label: str = _deployment_label(path)
            try:
                dataframe: pd.DataFrame = _load(path)
            except ValueError as error:
                click.echo(f"  skipping {path.name}: {error}")
                continue
            deployments.append((label, dataframe))
            click.echo(f"  loaded {label} ({len(dataframe)} poses)")

        if not deployments:
            continue

        figure: Figure = _build_figure(site_id, deployments)
        output_path: Path = output_dir / f"{site_id}_renav_camera_poses.png"
        figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close(figure)
        click.echo(f"  saved -> {output_path}")


# ---------------------------------------------------------------------------
# Figure construction
# ---------------------------------------------------------------------------


def _build_figure(
    site_id: str,
    deployments: list[tuple[str, pd.DataFrame]],
) -> Figure:
    palette: list[tuple[float, float, float]] = sns.color_palette(
        "tab10", n_colors=len(deployments)
    )
    utm_crs, origin = _shared_utm_origin(
        [dataframe for _, dataframe in deployments]
    )

    figure, axis = plt.subplots(figsize=(9, 8), constrained_layout=True)
    figure.suptitle(
        f"Renav stereo camera poses — site {site_id}",
        fontsize=12,
        fontweight="bold",
    )

    for (label, dataframe), color in zip(deployments, palette):
        _plot_track(axis, dataframe, label, color, utm_crs, origin)

    _style_map_axis(axis)

    legend_handles: list[Line2D] = [
        Line2D([0], [0], color=color, linewidth=1.5, label=label)
        for (label, _), color in zip(deployments, palette)
    ]
    axis.legend(
        handles=legend_handles,
        fontsize=7,
        loc="upper left",
        title="Deployment",
        title_fontsize=7,
    )

    return figure


def _plot_track(
    axis: Axes,
    dataframe: pd.DataFrame,
    label: str,
    color: tuple[float, float, float],
    utm_crs: CRS,
    origin: tuple[float, float],
) -> None:
    geodataframe: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            dataframe["longitude"], dataframe["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(utm_crs)

    east: pd.Series = geodataframe.geometry.x - origin[0]
    north: pd.Series = geodataframe.geometry.y - origin[1]

    axis.plot(
        east,
        north,
        color=color,
        linewidth=0.8,
        alpha=0.85,
        label=label,
    )
    axis.scatter(
        east.iloc[0],
        north.iloc[0],
        color=color,
        marker="o",
        s=30,
        zorder=4,
    )


def _style_map_axis(axis: Axes) -> None:
    axis.set_aspect("equal")
    axis.set_title("Camera pose tracks (UTM, metres from centroid)", fontsize=9)
    axis.set_xlabel("East offset (m)")
    axis.set_ylabel("North offset (m)")
    axis.grid(True, linewidth=0.4, alpha=0.5)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _group_files_by_site(input_dir: Path) -> dict[str, list[Path]]:
    groups: dict[str, list[Path]] = {}
    for path in input_dir.glob(f"*{_FILE_SUFFIX}"):
        site_id: str = path.name.split("_")[0]
        groups.setdefault(site_id, []).append(path)
    return groups


def _deployment_label(path: Path) -> str:
    parts: list[str] = path.name.replace(_FILE_SUFFIX, "").split("_")
    # parts: [site_id, YYYYMMDD, HHMMSS]
    if len(parts) >= 3:
        date_string: str = parts[1]
        return f"{date_string[:4]}-{date_string[4:6]}-{date_string[6:]}"
    return path.stem


def _load(path: Path) -> pd.DataFrame:
    dataframe: pd.DataFrame = pd.read_csv(
        path, parse_dates=["timestamp"], date_format="ISO8601"
    )
    missing: list[str] = [
        column
        for column in _REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    if dataframe["latitude"].abs().max() > 90:
        click.echo(
            f"  warning: latitude out of range in {path.name} — swapping lat/lon"
        )
        dataframe = dataframe.rename(
            columns={"latitude": "longitude", "longitude": "latitude"}
        )
    return dataframe


def _shared_utm_origin(
    dataframes: list[pd.DataFrame],
) -> tuple[CRS, tuple[float, float]]:
    all_points: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            pd.concat([dataframe["longitude"] for dataframe in dataframes]),
            pd.concat([dataframe["latitude"] for dataframe in dataframes]),
        ),
        crs="EPSG:4326",
    )
    utm_crs: CRS = all_points.estimate_utm_crs()
    all_utm: gpd.GeoDataFrame = all_points.to_crs(utm_crs)
    origin: tuple[float, float] = (
        float(all_utm.geometry.x.mean()),
        float(all_utm.geometry.y.mean()),
    )
    return utm_crs, origin


if __name__ == "__main__":
    main()
