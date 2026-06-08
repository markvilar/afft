"""
Batch compare Evologics USBL processed tracks: with vs. without extrinsics.

Scans an input directory for matched pairs of CSV files whose names end in
_usbl_evologics_with_extrinsics.csv and _usbl_evologics_without_extrinsics.csv.
For each pair a 2x2 figure is saved to the output directory:

    [0, 0]  Target track — with extrinsics
    [0, 1]  Target track — without extrinsics
    [1, 0]  Target Z in vessel frame — with extrinsics
    [1, 1]  Target Z in vessel frame — without extrinsics

Usage:
    uv run python scripts/python/batch_compare_evologics_tracks.py \\
        --input-dir /data/exos_01/acfr_usbl_resolution/acfr_evologics_messages_v1_comparison \\
        --output-dir /tmp/evologics_comparison
"""

from pathlib import Path

import click
import geopandas as gpd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pyproj import CRS


_WITH_SUFFIX: str = "_usbl_evologics_with_extrinsics.csv"
_WITHOUT_SUFFIX: str = "_usbl_evologics_without_extrinsics.csv"

_REQUIRED_COLS: list[str] = [
    "timestamp",
    "ship_latitude",
    "ship_longitude",
    "target_latitude",
    "target_longitude",
    "target_z_vessel",
    "usbl_extrinsics_locx",
    "usbl_extrinsics_locy",
    "usbl_extrinsics_locz",
    "usbl_extrinsics_rotx",
    "usbl_extrinsics_roty",
    "usbl_extrinsics_rotz",
]


@click.command()
@click.option(
    "--input-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing processed Evologics CSV files.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
    help="Directory to write comparison figures (PNG).",
)
def main(input_dir: Path, output_dir: Path) -> None:
    pairs: list[tuple[Path, Path]] = _find_pairs(input_dir)
    if not pairs:
        click.echo(f"No matched pairs found in {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for path_with, path_without in pairs:
        deployment: str = _deployment_label(path_with)
        click.echo(f"Processing {deployment} ...")
        try:
            dataframe_with: pd.DataFrame = _load(path_with)
            dataframe_without: pd.DataFrame = _load(path_without)
        except (FileNotFoundError, ValueError) as error:
            click.echo(f"  skipping: {error}")
            continue

        figure: Figure = _build_figure(
            dataframe_with, dataframe_without, deployment
        )
        output_path: Path = output_dir / f"{deployment}_evologics_comparison.png"
        figure.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(figure)
        click.echo(f"  saved -> {output_path}")


def _build_figure(
    dataframe_with: pd.DataFrame,
    dataframe_without: pd.DataFrame,
    deployment: str,
) -> Figure:
    figure, axes = plt.subplots(
        2,
        2,
        figsize=(18, 12),
        gridspec_kw={"height_ratios": [4, 1]},
        constrained_layout=True,
    )
    figure.suptitle(
        f"Evologics USBL — {deployment}\nWith vs. without extrinsics",
        fontsize=11,
    )

    label_with: str = _extrinsics_label(dataframe_with)
    label_without: str = _extrinsics_label(dataframe_without)

    utm_crs, origin = _compute_shared_utm_origin(
        [dataframe_with, dataframe_without]
    )

    _plot_track(
        axes[0, 0],
        dataframe_with,
        f"Target track — with extrinsics\n{label_with}",
        utm_crs,
        origin,
    )
    _plot_track(
        axes[0, 1],
        dataframe_without,
        f"Target track — without extrinsics\n{label_without}",
        utm_crs,
        origin,
    )
    _synchronize_map_limits(axes[0, 0], axes[0, 1])
    _plot_z_vessel(
        axes[1, 0], dataframe_with, "Target Z vessel — with extrinsics"
    )
    _plot_z_vessel(
        axes[1, 1], dataframe_without, "Target Z vessel — without extrinsics"
    )

    return figure


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _find_pairs(input_dir: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for path_with in sorted(input_dir.glob(f"*{_WITH_SUFFIX}")):
        path_without: Path = path_with.parent / path_with.name.replace(
            _WITH_SUFFIX, _WITHOUT_SUFFIX
        )
        if not path_without.exists():
            print(
                f"Warning: no without-extrinsics counterpart for {path_with.name}"
            )
            continue
        pairs.append((path_with, path_without))
    return pairs


def _load(path: Path) -> pd.DataFrame:
    dataframe: pd.DataFrame = pd.read_csv(
        path, parse_dates=["timestamp"], date_format="ISO8601"
    )
    missing: list[str] = [
        col for col in _REQUIRED_COLS if col not in dataframe.columns
    ]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    return dataframe


def _deployment_label(path_with: Path) -> str:
    return path_with.name.replace(_WITH_SUFFIX, "")


def _extrinsics_label(dataframe: pd.DataFrame) -> str:
    return (
        f"loc=({dataframe['usbl_extrinsics_locx'].iloc[0]:.3f}, "
        f"{dataframe['usbl_extrinsics_locy'].iloc[0]:.3f}, "
        f"{dataframe['usbl_extrinsics_locz'].iloc[0]:.3f}) m  "
        f"rot=({np.degrees(dataframe['usbl_extrinsics_rotx'].iloc[0]):.2f}, "
        f"{np.degrees(dataframe['usbl_extrinsics_roty'].iloc[0]):.2f}, "
        f"{np.degrees(dataframe['usbl_extrinsics_rotz'].iloc[0]):.2f})°"
    )


def _compute_shared_utm_origin(
    dataframes: list[pd.DataFrame],
) -> tuple[CRS, tuple[float, float]]:
    combined_targets: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            pd.concat([df["target_longitude"] for df in dataframes]),
            pd.concat([df["target_latitude"] for df in dataframes]),
        ),
        crs="EPSG:4326",
    )
    utm_crs: CRS = combined_targets.estimate_utm_crs()
    combined_utm: gpd.GeoDataFrame = combined_targets.to_crs(utm_crs)
    origin: tuple[float, float] = (
        float(combined_utm.geometry.x.mean()),
        float(combined_utm.geometry.y.mean()),
    )
    return utm_crs, origin


def _synchronize_map_limits(axis_a: Axes, axis_b: Axes) -> None:
    x_min = min(axis_a.get_xlim()[0], axis_b.get_xlim()[0])
    x_max = max(axis_a.get_xlim()[1], axis_b.get_xlim()[1])
    y_min = min(axis_a.get_ylim()[0], axis_b.get_ylim()[0])
    y_max = max(axis_a.get_ylim()[1], axis_b.get_ylim()[1])
    for axis in (axis_a, axis_b):
        axis.set_xlim(x_min, x_max)
        axis.set_ylim(y_min, y_max)


def _plot_track(
    axis: Axes,
    dataframe: pd.DataFrame,
    title: str,
    utm_crs: CRS,
    origin: tuple[float, float],
) -> None:
    elapsed: np.ndarray = (
        dataframe["timestamp"].astype(np.int64).to_numpy() / 1e9
    )
    elapsed = elapsed - elapsed.min()

    ship: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            dataframe["ship_longitude"], dataframe["ship_latitude"]
        ),
        crs="EPSG:4326",
    )
    target: gpd.GeoDataFrame = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(
            dataframe["target_longitude"], dataframe["target_latitude"]
        ),
        crs="EPSG:4326",
    )

    ship_utm: gpd.GeoDataFrame = ship.to_crs(utm_crs)
    target_utm: gpd.GeoDataFrame = target.to_crs(utm_crs)

    origin_x, origin_y = origin

    axis.plot(
        ship_utm.geometry.x - origin_x,
        ship_utm.geometry.y - origin_y,
        color="steelblue",
        linewidth=0.8,
        alpha=0.5,
        label="Ship track",
    )
    scatter = axis.scatter(
        target_utm.geometry.x - origin_x,
        target_utm.geometry.y - origin_y,
        c=elapsed,
        cmap="viridis",
        s=8,
        zorder=3,
        label="Target",
    )
    plt.colorbar(scatter, ax=axis, label="Elapsed (s)", fraction=0.03, pad=0.04)

    target_x = target_utm.geometry.x - origin_x
    target_y = target_utm.geometry.y - origin_y
    padding = (
        max(target_x.max() - target_x.min(), target_y.max() - target_y.min())
        * 0.05
    )
    axis.set_xlim(target_x.min() - padding, target_x.max() + padding)
    axis.set_ylim(target_y.min() - padding, target_y.max() + padding)

    axis.set_aspect("equal")
    axis.set_title(title, fontsize=8)
    axis.set_xlabel("East offset (m)")
    axis.set_ylabel("North offset (m)")
    axis.legend(fontsize=7, loc="upper left")


def _plot_z_vessel(axis: Axes, dataframe: pd.DataFrame, title: str) -> None:
    axis.plot(
        dataframe["timestamp"],
        dataframe["target_z_vessel"],
        color="seagreen",
        linewidth=0.9,
    )
    axis.invert_yaxis()
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axis.xaxis.set_major_locator(mdates.AutoDateLocator())
    axis.tick_params(axis="x", labelrotation=30, labelsize=7)
    axis.set_title(title, fontsize=8)
    axis.set_xlabel("Time (UTC)")
    axis.set_ylabel("Z vessel (m, down +ve)")


if __name__ == "__main__":
    main()
