#!/usr/bin/env python3
"""
Compare two performance-test runs using two config files.

Only compares:
1. total CPU utilization summary
   - 50% percentile
   - 99% percentile
   - 99.9% percentile
   - Minimum
   - Maximum
2. total system memory usage
   - time-series overlay
   - ratio plot

This follows the run-loading structure of analyse_data.py.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import click
import numpy as np
import pandas as pd

import files
import plotting
import times
import utils
from times import time_range


EPS = 1e-12


def simplify_dict_name(dictionary: dict, default: str | None):
    unique_names = utils.get_unique_string_elements(list(dictionary.keys()), "_")
    for old, new in zip(list(dictionary.keys()), unique_names):
        key = default if len(new) == 0 else new
        dictionary[key] = dictionary.pop(old)
    return


def safe_slug(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)


def apply_time_window(df: pd.DataFrame, start_offset: float = 0.0, end_cut: float = 0.0) -> pd.DataFrame:
    if df.empty:
        return df

    t0 = float(df.index.min())
    t1 = float(df.index.max())

    start = t0 + start_offset
    end = t1 - end_cut

    if end <= start:
        return df.iloc[0:0].copy()

    return df.loc[(df.index >= start) & (df.index <= end)].copy()


def rebase_relative_time(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    out.index = out.index.astype(float) - float(out.index[0])
    return out


def restrict_to_common_relative_range(df1: pd.DataFrame, df2: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df1.empty or df2.empty:
        return df1.iloc[0:0], df2.iloc[0:0]

    end = min(float(df1.index.max()), float(df2.index.max()))
    if end <= 0:
        return df1.iloc[0:0], df2.iloc[0:0]

    df1 = df1.loc[(df1.index >= 0) & (df1.index <= end)].copy()
    df2 = df2.loc[(df2.index >= 0) & (df2.index <= end)].copy()
    return df1, df2


def interpolate_to_common_grid(
    s1: pd.Series,
    s2: pd.Series,
) -> tuple[np.ndarray, pd.Series, pd.Series]:
    if s1.empty or s2.empty:
        return np.array([]), pd.Series(dtype=float), pd.Series(dtype=float)

    start = max(float(s1.index.min()), float(s2.index.min()))
    end = min(float(s1.index.max()), float(s2.index.max()))
    if end <= start:
        return np.array([]), pd.Series(dtype=float), pd.Series(dtype=float)

    grid = np.union1d(
        s1.loc[(s1.index >= start) & (s1.index <= end)].index.values.astype(float),
        s2.loc[(s2.index >= start) & (s2.index <= end)].index.values.astype(float),
    )
    if len(grid) == 0:
        return np.array([]), pd.Series(dtype=float), pd.Series(dtype=float)

    y1 = np.interp(grid, s1.index.values.astype(float), s1.values.astype(float))
    y2 = np.interp(grid, s2.index.values.astype(float), s2.values.astype(float))

    return grid, pd.Series(y1, index=grid), pd.Series(y2, index=grid)


def ratio_series(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.where(np.abs(den) > EPS, np.nan)
    out = num / den
    return out.replace([np.inf, -np.inf], np.nan)


def cpu_usage(idle: float | np.ndarray, total: float | np.ndarray) -> float | np.ndarray:
    idle_arr = np.asarray(idle, dtype=float)
    total_arr = np.asarray(total, dtype=float)

    out = np.full_like(total_arr, np.nan, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        np.divide(idle_arr, total_arr, out=out, where=np.abs(total_arr) > EPS)
        out = 100.0 * (1.0 - out)

    if np.ndim(out) == 0:
        return float(out)
    return out


def fill_zeros_with_last(arr: np.ndarray, axis: int) -> np.ndarray:
    if len(arr.shape) == 1:
        return fill_zeros_with_last(np.expand_dims(arr, axis=1), 1).flatten()

    new = []
    for i in range(arr.shape[axis]):
        a = np.take(arr, i, axis=axis)
        prev = np.arange(len(a))
        prev[a == 0] = 0
        new.append(a[np.maximum.accumulate(prev)])
    new = np.array(new).T
    return new


def cpu_usage_rate(idle: pd.DataFrame | pd.Series, total: pd.DataFrame | pd.Series) -> np.ndarray:
    idle_delta = fill_zeros_with_last(abs(idle[1:].values - idle[:-1].values), axis=1)
    total_delta = fill_zeros_with_last(abs(total[1:].values - total[:-1].values), axis=1)
    return cpu_usage(idle_delta, total_delta)


def load_run_data_from_config(config_path: str) -> dict[str, Any]:
    test_args = files.read_config(config_path)

    tr = time_range(*test_args["time_range"])
    data = utils.search_hdf5_data(test_args["data_path"], test_args["dunedaq_version"])

    for d in data:
        if data[d]:
            data[d] = times.slice_time_range(files.read_hdf5(data[d]), tr)

    if len(test_args["host"]) == 1:
        def_name = test_args["host"][0].replace("-", "")
    else:
        def_name = None

    node_exporter = utils.search_dict(data, "node-exporter")
    simplify_dict_name(node_exporter, def_name)

    return {
        "test_args": test_args,
        "node_exporter": node_exporter,
    }


def derive_total_cpu_utilization(
    node_exporter_host_data: dict[pd.DataFrame],
) -> pd.Series | None:
    total_time_per_core = sum(utils.search_dict(node_exporter_host_data, "(?=.*CPU)(?!.*Usage)").values())
    if total_time_per_core.empty:
        return None

    idle_df = node_exporter_host_data.get("CPU idle (s)")
    if idle_df is None or idle_df.empty:
        return None

    cpu_time_total = total_time_per_core.sum(axis=1)
    cpu_time_idle = idle_df.sum(axis=1)

    usage_values = cpu_usage_rate(cpu_time_idle, cpu_time_total)

    total_usage = pd.Series(
        usage_values,
        index=cpu_time_total.index[1:],
        name="Total CPU Utilization (%)",
    )

    total_usage = total_usage.replace([np.inf, -np.inf], np.nan).dropna()
    if total_usage.empty:
        return None

    return total_usage.sort_index()


def summarize_total_cpu_utilization(cpu_usage_series: pd.Series) -> pd.Series | None:
    if cpu_usage_series is None or cpu_usage_series.empty:
        return None

    return pd.Series(
        {
            "50% percentile": cpu_usage_series.quantile(0.50),
            "99% percentile": cpu_usage_series.quantile(0.99),
            "99.9% percentile": cpu_usage_series.quantile(0.999),
            "Minimum": cpu_usage_series.min(),
            "Maximum": cpu_usage_series.max(),
        }
    )


def derive_total_memory_usage(
    node_exporter_host_data: dict[pd.DataFrame],
) -> pd.Series | None:
    mem_usg = node_exporter_host_data.get("Memory Usage (%)")
    if mem_usg is None or mem_usg.empty:
        return None

    if isinstance(mem_usg, pd.DataFrame):
        if mem_usg.shape[1] == 1:
            mem_usg = mem_usg.iloc[:, 0]
        else:
            mem_usg = mem_usg.mean(axis=1)

    mem_usg = mem_usg.replace([np.inf, -np.inf], np.nan).dropna()
    if mem_usg.empty:
        return None

    return mem_usg.sort_index()

def plot_total_cpu_summary_comparison(
    cpu1: pd.Series,
    cpu2: pd.Series,
    label1: str,
    label2: str,
    host: str,
    book,
):
    summary1 = summarize_total_cpu_utilization(cpu1)
    summary2 = summarize_total_cpu_utilization(cpu2)

    if summary1 is None or summary2 is None:
        return

    metrics = ["50% percentile", "99% percentile", "99.9% percentile", "Minimum", "Maximum"]

    s1 = summary1.reindex(metrics)
    s2 = summary2.reindex(metrics)

    x = np.arange(len(metrics))
    width = 0.38

    # grouped bar chart
    plotting.plt.figure()
    bars1 = plotting.plt.bar(x - width / 2, s1.values, width=width, label=label1)
    bars2 = plotting.plt.bar(x + width / 2, s2.values, width=width, label=label2)

    plotting.plt.xticks(x, metrics, rotation=20, ha="right")
    plotting.plt.ylabel("Total CPU utilization (%)")
    plotting.plt.title(f"Total CPU utilization summary — {host}")
    plotting.plt.ylim(0, 100)
    plotting.plt.legend(fontsize="small")
    plotting.plt.bar_label(bars1, fmt="%.2f", fontsize="x-small")
    plotting.plt.bar_label(bars2, fmt="%.2f", fontsize="x-small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.22)
    book.save()

    ratio = s2 / s1.where(np.abs(s1) > EPS, np.nan)
    ratio = ratio.replace([np.inf, -np.inf], np.nan)

    ratio_plot = ratio.reindex(metrics)
    valid_mask = ~ratio_plot.isna()
    if valid_mask.any():
        x_ratio = np.arange(len(metrics))

        plotting.plt.figure()
        bars = plotting.plt.bar(x_ratio[valid_mask], ratio_plot[valid_mask].values)

        plotting.plt.xticks(x_ratio, metrics, rotation=20, ha="right")
        plotting.plt.ylabel(f"Ratio ({label2} / {label1})")
        plotting.plt.title(f"CPU summary ratio ({label2} / {label1}) — {host}")
        plotting.plt.axhline(1.0, color="k", linestyle="--")
        plotting.plt.bar_label(bars, fmt="%.3f", fontsize="x-small")
        plotting.plt.subplots_adjust(top=0.88, bottom=0.22)
        book.save()


def plot_memory_usage_comparison(
    mem1: pd.Series,
    mem2: pd.Series,
    label1: str,
    label2: str,
    host: str,
    book,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
):
    df1 = mem1.to_frame("Memory Usage (%)")
    df2 = mem2.to_frame("Memory Usage (%)")

    df1 = apply_time_window(df1, first_file_time_start_offset, first_file_time_end_cut)
    df2 = apply_time_window(df2, second_file_time_start_offset, second_file_time_end_cut)

    if df1.empty or df2.empty:
        return

    df1 = rebase_relative_time(df1)
    df2 = rebase_relative_time(df2)

    if make_same_time_range:
        df1, df2 = restrict_to_common_relative_range(df1, df2)

    if df1.empty or df2.empty:
        return

    combined = pd.concat(
        [
            df1.rename(columns={"Memory Usage (%)": label1}),
            df2.rename(columns={"Memory Usage (%)": label2}),
        ],
        axis=1,
    )

    plotting.plot(
        combined.index,
        combined,
        combined.columns,
        "Relative time (s)",
        f"Total system memory usage — {host}",
    )
    plotting.plt.ylim(0, 100)
    plotting.plt.legend(fontsize="small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    book.save()

    _, s1i, s2i = interpolate_to_common_grid(df1.iloc[:, 0], df2.iloc[:, 0])
    if s1i.empty or s2i.empty:
        return

    ratio = ratio_series(s2i, s1i).dropna()
    if ratio.empty:
        return

    plotting.plot(
        ratio.index,
        ratio.values,
        None,
        "Relative time (s)",
        f"Memory usage ratio ({label2} / {label1}) — {host}",
    )
    plotting.plt.axhline(1.0, color="k", linestyle="--")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    book.save()


def compare_runs(
    first_config: str,
    second_config: str,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
    out_dir: str | None = None,
):
    plotting.set_plot_style()

    run1 = load_run_data_from_config(first_config)
    run2 = load_run_data_from_config(second_config)

    args1 = run1["test_args"]
    args2 = run2["test_args"]

    label1 = args1.get("test_name", Path(first_config).stem)
    label2 = args2.get("test_name", Path(second_config).stem)

    if out_dir is None:
        base = args1["plot_path"] if args1.get("plot_path") else utils.make_plot_dir(args1)
        out_dir = os.path.join(base, "comparison_plots")
    os.makedirs(out_dir, exist_ok=True)

    output_file = os.path.join(
        out_dir,
        f"cmp_{safe_slug(label1)}_vs_{safe_slug(label2)}.pdf",
    )

    common_hosts = sorted(set(run1["node_exporter"].keys()) & set(run2["node_exporter"].keys()))
    if not common_hosts:
        raise RuntimeError("No common hosts found between the two runs.")

    with plotting.PlotBook(output_file, True) as book:
        for host in common_hosts:
            host1 = run1["node_exporter"][host]
            host2 = run2["node_exporter"][host]

            cpu1 = derive_total_cpu_utilization(host1)
            cpu2 = derive_total_cpu_utilization(host2)
            if cpu1 is not None and cpu2 is not None:
                plot_total_cpu_summary_comparison(
                    cpu1,
                    cpu2,
                    label1,
                    label2,
                    host,
                    book,
                )

            mem1 = derive_total_memory_usage(host1)
            mem2 = derive_total_memory_usage(host2)
            if mem1 is not None and mem2 is not None:
                plot_memory_usage_comparison(
                    mem1,
                    mem2,
                    label1,
                    label2,
                    host,
                    book,
                    first_file_time_start_offset=first_file_time_start_offset,
                    second_file_time_start_offset=second_file_time_start_offset,
                    first_file_time_end_cut=first_file_time_end_cut,
                    second_file_time_end_cut=second_file_time_end_cut,
                    make_same_time_range=make_same_time_range,
                )

    click.echo(f"Saved comparison plotbook: {output_file}")


@click.command()
@click.argument("first_config", type=click.Path(exists=True, dir_okay=False))
@click.argument("second_config", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--first-file-time-start-offset",
    type=float,
    default=0.0,
    show_default=True,
    help="Seconds to skip from the start of the first run after applying config time_range.",
)
@click.option(
    "--second-file-time-start-offset",
    type=float,
    default=0.0,
    show_default=True,
    help="Seconds to skip from the start of the second run after applying config time_range.",
)
@click.option(
    "--first-file-time-end-cut",
    type=float,
    default=0.0,
    show_default=True,
    help="Seconds to cut from the end of the first run after applying config time_range.",
)
@click.option(
    "--second-file-time-end-cut",
    type=float,
    default=0.0,
    show_default=True,
    help="Seconds to cut from the end of the second run after applying config time_range.",
)
@click.option(
    "--make-same-time-range/--no-make-same-time-range",
    default=False,
    show_default=True,
    help="Restrict both memory traces to the common relative-time interval before computing ratios.",
)
@click.option(
    "--out-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default=None,
    help="Directory to write the comparison plotbook into.",
)
def main(
    first_config: str,
    second_config: str,
    first_file_time_start_offset: float,
    second_file_time_start_offset: float,
    first_file_time_end_cut: float,
    second_file_time_end_cut: float,
    make_same_time_range: bool,
    out_dir: str | None,
):
    compare_runs(
        first_config=first_config,
        second_config=second_config,
        first_file_time_start_offset=first_file_time_start_offset,
        second_file_time_start_offset=second_file_time_start_offset,
        first_file_time_end_cut=first_file_time_end_cut,
        second_file_time_end_cut=second_file_time_end_cut,
        make_same_time_range=make_same_time_range,
        out_dir=out_dir,
    )


if __name__ == "__main__":
    main()