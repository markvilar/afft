"""
Compare Renav camera poses and transformed vehicle poses side by side.

For each deployment label found in both input directories, generates a figure
with a lat/lon map (UTM) on the left and six time series on the right:
depth, heading, pitch, roll, and the north/east offset (vehicle − camera in
UTM metres). Camera poses and vehicle poses are rendered in distinct colours.

Usage:
    uv run python scripts/python/compare_camera_vehicle_poses.py \\
        --camera-dir /path/to/renav_poses \\
        --vehicle-dir /path/to/vehicle_poses \\
        --output     /path/to/figures
"""

from pathlib import Path

import click
import geopandas as gpd
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from pyproj import CRS


_CAMERA_SUFFIX: str = "_renav_stereo_poses.csv"
_VEHICLE_SUFFIX: str = "_vehicle_poses.csv"

_CAMERA_COLOR: str = "#1f77b4"
_VEHICLE_COLOR: str = "#ff7f0e"
_OFFSET_COLOR: str = "#2ca02c"

_CAMERA_LABEL: str = "Camera"
_VEHICLE_LABEL: str = "Vehicle"

_REQUIRED_COLUMNS: list[str] = [
    "timestamp",
    "latitude",
    "longitude",
    "depth",
    "heading",
    "pitch",
    "roll",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.command()
@click.option(
    "--camera-dir",
    "camera_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing camera pose CSV files.",
)
@click.option(
    "--vehicle-dir",
    "vehicle_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing vehicle pose CSV files.",
)
@click.option(
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory to write per-deployment PNG figures.",
)
@click.option(
    "--camera-suffix",
    "camera_suffix",
    type=str,
    default=_CAMERA_SUFFIX,
    show_default=True,
    help="Suffix stripped from camera pose filenames to derive the deployment label.",
)
@click.option(
    "--vehicle-suffix",
    "vehicle_suffix",
    type=str,
    default=_VEHICLE_SUFFIX,
    show_default=True,
    help="Suffix stripped from vehicle pose filenames to derive the deployment label.",
)
@click.option(
    "--dpi",
    default=300,
    show_default=True,
    help="Output figure resolution in dots per inch.",
)
def main(
    camera_dir: Path,
    vehicle_dir: Path,
    output_dir: Path,
    camera_suffix: str,
    vehicle_suffix: str,
    dpi: int,
) -> None:
    """Compare camera and vehicle poses per deployment."""
    pairs: dict[str, tuple[Path, Path]] = _match_files(
        camera_dir, vehicle_dir, camera_suffix, vehicle_suffix
    )
    if not pairs:
        click.echo("No matching deployment files found.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Found {len(pairs)} matching deployment(s).")

    for label, (camera_path, vehicle_path) in sorted(pairs.items()):
        try:
            cameras: pd.DataFrame = _load(camera_path)
            vehicles: pd.DataFrame = _load(vehicle_path)
        except ValueError as error:
            click.echo(f"  skipping {label}: {error}")
            continue

        click.echo(
            f"  {label}: {len(cameras)} camera / {len(vehicles)} vehicle poses"
        )

        figure: Figure = _build_figure(label, cameras, vehicles)
        output_path: Path = output_dir / f"{label}_pose_comparison.png"
        figure.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close(figure)
        click.echo(f"    saved -> {output_path}")


# ---------------------------------------------------------------------------
# Figure construction
# ---------------------------------------------------------------------------


def _build_figure(
    label: str,
    cameras: pd.DataFrame,
    vehicles: pd.DataFrame,
) -> Figure:
    utm_crs: CRS
    origin: tuple[float, float]
    utm_crs, origin = _shared_utm_origin([cameras, vehicles])

    north_offset: pd.Series
    east_offset: pd.Series
    north_offset, east_offset = _compute_offset(cameras, vehicles, utm_crs)

    figure: Figure = plt.figure(figsize=(16, 14))
    figure.suptitle(label, fontsize=12, fontweight="bold")

    gs: gridspec.GridSpec = gridspec.GridSpec(
        6, 2, figure=figure, width_ratios=[1, 1.2], hspace=0.08, wspace=0.3
    )

    map_axis: Axes = figure.add_subplot(gs[:, 0])
    depth_axis: Axes = figure.add_subplot(gs[0, 1])
    heading_axis: Axes = figure.add_subplot(gs[1, 1], sharex=depth_axis)
    pitch_axis: Axes = figure.add_subplot(gs[2, 1], sharex=depth_axis)
    roll_axis: Axes = figure.add_subplot(gs[3, 1], sharex=depth_axis)
    north_offset_axis: Axes = figure.add_subplot(gs[4, 1], sharex=depth_axis)
    east_offset_axis: Axes = figure.add_subplot(gs[5, 1], sharex=depth_axis)

    _plot_map(map_axis, cameras, vehicles, utm_crs, origin)

    _plot_timeseries(depth_axis, cameras, vehicles, "depth", "Depth (m)")
    _plot_timeseries(heading_axis, cameras, vehicles, "heading", "Heading (°)")
    _plot_timeseries(pitch_axis, cameras, vehicles, "pitch", "Pitch (°)")
    _plot_timeseries(roll_axis, cameras, vehicles, "roll", "Roll (°)")

    _plot_offset(
        north_offset_axis,
        cameras["timestamp"],
        north_offset,
        "North offset (m)",
    )
    _plot_offset(
        east_offset_axis, cameras["timestamp"], east_offset, "East offset (m)"
    )

    for axis in [
        depth_axis,
        heading_axis,
        pitch_axis,
        roll_axis,
        north_offset_axis,
    ]:
        plt.setp(axis.get_xticklabels(), visible=False)

    pose_handles: list[Line2D] = [
        Line2D(
            [0], [0], color=_CAMERA_COLOR, linewidth=1.5, label=_CAMERA_LABEL
        ),
        Line2D(
            [0],
            [0],
            color=_VEHICLE_COLOR,
            linewidth=1.5,
            linestyle="--",
            label=_VEHICLE_LABEL,
        ),
        Line2D(
            [0],
            [0],
            color=_OFFSET_COLOR,
            linewidth=1.5,
            label="Vehicle − Camera offset",
        ),
    ]
    figure.legend(
        handles=pose_handles,
        loc="upper center",
        ncol=3,
        fontsize=9,
        bbox_to_anchor=(0.5, 0.98),
    )

    return figure


def _plot_map(
    axis: Axes,
    cameras: pd.DataFrame,
    vehicles: pd.DataFrame,
    utm_crs: CRS,
    origin: tuple[float, float],
) -> None:
    _plot_track(axis, cameras, _CAMERA_COLOR, utm_crs, origin)
    _plot_track(axis, vehicles, _VEHICLE_COLOR, utm_crs, origin)

    axis.set_aspect("equal")
    axis.set_title("Pose tracks (UTM, metres from centroid)", fontsize=9)
    axis.set_xlabel("East offset (m)")
    axis.set_ylabel("North offset (m)")
    axis.grid(True, linewidth=0.4, alpha=0.5)


def _plot_track(
    axis: Axes,
    dataframe: pd.DataFrame,
    color: str,
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

    axis.plot(east, north, color=color, linewidth=0.8, alpha=0.85)
    axis.scatter(
        east.iloc[0],
        north.iloc[0],
        color=color,
        marker="o",
        s=30,
        zorder=4,
    )


def _plot_timeseries(
    axis: Axes,
    cameras: pd.DataFrame,
    vehicles: pd.DataFrame,
    column: str,
    ylabel: str,
) -> None:
    axis.plot(
        cameras["timestamp"],
        cameras[column],
        color=_CAMERA_COLOR,
        linewidth=0.8,
        alpha=0.85,
    )
    axis.plot(
        vehicles["timestamp"],
        vehicles[column],
        color=_VEHICLE_COLOR,
        linewidth=0.8,
        alpha=0.85,
        linestyle="--",
    )
    axis.set_ylabel(ylabel, fontsize=8)
    axis.grid(True, linewidth=0.4, alpha=0.5)
    axis.tick_params(axis="both", labelsize=7)


def _plot_offset(
    axis: Axes,
    timestamps: pd.Series,
    offset: pd.Series,
    ylabel: str,
) -> None:
    axis.plot(
        timestamps, offset, color=_OFFSET_COLOR, linewidth=0.8, alpha=0.85
    )
    axis.axhline(0.0, color="black", linewidth=0.5, linestyle=":")
    axis.set_ylabel(ylabel, fontsize=8)
    axis.grid(True, linewidth=0.4, alpha=0.5)
    axis.tick_params(axis="both", labelsize=7)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_offset(
    cameras: pd.DataFrame,
    vehicles: pd.DataFrame,
    utm_crs: CRS,
) -> tuple[pd.Series, pd.Series]:
    camera_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(cameras["longitude"], cameras["latitude"]),
        crs="EPSG:4326",
    ).to_crs(utm_crs)
    vehicle_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            vehicles["longitude"], vehicles["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(utm_crs)

    north_offset: pd.Series = (
        vehicle_gdf.geometry.y - camera_gdf.geometry.y
    ).reset_index(drop=True)
    east_offset: pd.Series = (
        vehicle_gdf.geometry.x - camera_gdf.geometry.x
    ).reset_index(drop=True)
    return north_offset, east_offset


def _match_files(
    camera_dir: Path,
    vehicle_dir: Path,
    camera_suffix: str,
    vehicle_suffix: str,
) -> dict[str, tuple[Path, Path]]:
    camera_labels: dict[str, Path] = {
        path.name.removesuffix(camera_suffix): path
        for path in camera_dir.iterdir()
        if path.is_file() and path.name.endswith(camera_suffix)
    }
    vehicle_labels: dict[str, Path] = {
        path.name.removesuffix(vehicle_suffix): path
        for path in vehicle_dir.iterdir()
        if path.is_file() and path.name.endswith(vehicle_suffix)
    }
    common: set[str] = camera_labels.keys() & vehicle_labels.keys()
    return {
        label: (camera_labels[label], vehicle_labels[label]) for label in common
    }


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
