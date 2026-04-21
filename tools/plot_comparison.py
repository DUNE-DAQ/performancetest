#!/usr/bin/env python3
"""
Compare two performance-test runs using two config files.

Compares:
1. total CPU utilization summary
   - 50% percentile
   - 99% percentile
   - 99.9% percentile
   - Minimum
   - Maximum
2. total system memory usage
   - time-series overlay
   - ratio plot
3. NIC RX throughput (total across all queues)
   - time-series overlay
   - ratio plot
4. total TPG rate produced and sent
   - time-series overlay (produced)
   - time-series overlay (sent)
   - ratio plots
5. percentage of packets missed
   - time-series overlay
   - ratio plot
6. percentage of packets dropped
   - time-series overlay
   - ratio plot

"""

from __future__ import annotations

import ast
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
    out.index = times.relative_time(out)/10.0
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

def _group_df_by_element(df: pd.DataFrame | None) -> dict[str, pd.Series]:
    """Group DataFrame columns by parsed 'element' or 'application' field."""
    if df is None or df.empty:
        return {}

    groups: dict[str, list[pd.Series]] = {}
    for col in df.columns:
        try:
            d = ast.literal_eval(str(col))
            if isinstance(d, dict):
                elem = d.get("element") or d.get("application")
                if elem:
                    groups.setdefault(str(elem), []).append(df[col])
        except (ValueError, SyntaxError):
            pass

    return {
        elem: sum(cols).replace([np.inf, -np.inf], np.nan).dropna().sort_index()
        for elem, cols in groups.items()
        if cols
    }

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

    # Collect all frontend_ethernet entries, keyed by app suffix.
    # Single app  -> {"default": panel_dict}
    # Two apps    -> {"app1": panel_dict, "app2": panel_dict}
    fe_raw = utils.search_dict(data, "frontend_ethernet")
    fe: dict[str, dict] = {}
    for k, v in fe_raw.items():
        if isinstance(v, dict):
            suffix = k[len("frontend_ethernet"):].lstrip("_") or "default"
            fe[suffix] = v

    # Collect all trigger_primitives / tp_handlers entries, keyed by app suffix.
    tp: dict[str, dict] = {}
    for base_key in ("trigger_primitives", "tp_handlers"):
        for k, v in utils.search_dict(data, base_key).items():
            if isinstance(v, dict):
                suffix = k[len(base_key):].lstrip("_") or "default"
                if suffix not in tp:
                    tp[suffix] = {}
                tp[suffix].update(v)

    return {
        "test_args": test_args,
        "node_exporter": node_exporter,
        "frontend_ethernet": fe,
        "trigger_primitives": tp,
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

def _parse_throughput_by_element(rx: pd.DataFrame) -> dict[str, list]:
    """Group throughput DataFrame columns by the 'element' (app) field.

    Column names are serialized Python dicts, e.g.
      '{"element": "ruapp-0", "subelement": "eth3", "queue": 0}'
    or older format:
      '{"application": "ruapp-0", "queue": 0}'

    Returns {element_name: [Series, ...]} — empty dict if columns are not parseable.
    """
    groups: dict[str, list] = {}
    for col in rx.columns:
        try:
            d = ast.literal_eval(str(col))
            if isinstance(d, dict):
                elem = d.get("element") or d.get("application")
                if elem:
                    elem = str(elem)
                    groups.setdefault(elem, []).append(rx[col])
        except (ValueError, SyntaxError):
            pass
    return groups


def _sum_matching_cols(df: pd.DataFrame | None, name: str) -> pd.Series | None:
    """Sum columns whose string representation contains *name* (mirrors sum_over_app)."""
    if df is None:
        return None
    matching = [df[c] for c in df.columns if name in str(c)]
    if not matching:
        return None
    return sum(matching)


def derive_nic_throughput(fe_apps: dict[str, dict]) -> dict[str, pd.Series | None]:
    """Total RX throughput per app (B/s).

    For multi-app dashboards (BDE) the Throughput panel columns encode the app
    name as the 'element' field of a serialised dict — mirrors the logic in
    analyze_data.py::process_frontend_info.
    """
    result: dict[str, pd.Series | None] = {}
    for app_key, frontend_data in fe_apps.items():
        if not frontend_data:
            continue
        throughput_dict = utils.search_dict(frontend_data, "Throughput")
        vals = list(throughput_dict.values())
        if not vals:
            continue
        rx = vals[0]
        if rx is None or (hasattr(rx, "empty") and rx.empty):
            continue

        groups = _parse_throughput_by_element(rx)
        if len(groups) > 1:
            # Multi-app: one series per element, summed over its queues
            for elem_name, cols in groups.items():
                total = sum(cols).replace([np.inf, -np.inf], np.nan).dropna()
                result[elem_name] = total.sort_index() if not total.empty else None
        else:
            # Single app (or unparseable columns): sum everything
            total = rx.sum(axis=1).replace([np.inf, -np.inf], np.nan).dropna()
            result[app_key] = total.sort_index() if not total.empty else None
    return result


def derive_tp_rates(
    tp_apps: dict[str, dict],
) -> dict[str, tuple[pd.Series | None, pd.Series | None]]:
    """Total TP produced and sent rate (summed across all DLHs), per app."""
    result: dict[str, tuple[pd.Series | None, pd.Series | None]] = {}
    for app_name, tp_data in tp_apps.items():
        if not tp_data:
            result[app_name] = (None, None)
            continue

        produced = None
        sent = None

        hr_vals = list(utils.search_dict(tp_data, "hit rates").values())
        if hr_vals and hr_vals[0] is not None and not hr_vals[0].empty:
            s = hr_vals[0].sum(axis=1).replace([np.inf, -np.inf], np.nan).dropna()
            if not s.empty:
                produced = s.sort_index()

        sent_vals = list(utils.search_dict(tp_data, "TP Sent rates").values())
        if sent_vals and sent_vals[0] is not None and not sent_vals[0].empty:
            s = sent_vals[0].sum(axis=1).replace([np.inf, -np.inf], np.nan).dropna()
            if not s.empty:
                sent = s.sort_index()

        result[app_name] = (produced, sent)
    return result


def derive_packet_loss(
    fe_apps: dict[str, dict],
) -> dict[str, tuple[pd.Series | None, pd.Series | None]]:
    """Percentage of missed and dropped packets per app."""
    result: dict[str, tuple[pd.Series | None, pd.Series | None]] = {}

    def _pct(num: pd.Series, denom_safe: pd.Series) -> pd.Series | None:
        pct = (num / denom_safe * 100).replace([np.inf, -np.inf], np.nan).dropna()
        return pct.sort_index() if not pct.empty else None

    for app_key, frontend_data in fe_apps.items():
        if not frontend_data:
            continue

        input_pkts = frontend_data.get("Input Packets")
        missed_pkts = frontend_data.get("Input Missed Packets")
        dropped_pkts = frontend_data.get("RX Dropped Packets")

        if input_pkts is None or missed_pkts is None:
            result[app_key] = (None, None)
            continue
        if input_pkts.empty or missed_pkts.empty:
            result[app_key] = (None, None)
            continue

        input_groups = _group_df_by_element(input_pkts)
        missed_groups = _group_df_by_element(missed_pkts)
        dropped_groups = _group_df_by_element(dropped_pkts) if dropped_pkts is not None else {}

        # If columns carry explicit app identity, use it
        all_elems = sorted(set(input_groups) | set(missed_groups) | set(dropped_groups))
        if all_elems:
            for elem_name in all_elems:
                inp = input_groups.get(elem_name)
                mis = missed_groups.get(elem_name)
                drp = dropped_groups.get(elem_name)

                if inp is None or mis is None:
                    result[elem_name] = (None, None)
                    continue

                total_pkts_safe = (inp + mis).where(lambda x: x > EPS, np.nan)
                result[elem_name] = (
                    _pct(mis, total_pkts_safe),
                    _pct(drp, total_pkts_safe) if drp is not None else None,
                )
        else:
            # Fallback: single app / unparseable columns
            total_input = input_pkts.sum(axis=1)
            total_missed = missed_pkts.sum(axis=1)
            total_pkts_safe = (total_input + total_missed).where(lambda x: x > EPS, np.nan)

            dropped_out = None
            if dropped_pkts is not None and not dropped_pkts.empty:
                dropped_out = _pct(dropped_pkts.sum(axis=1), total_pkts_safe)

            result[app_key] = (_pct(total_missed, total_pkts_safe), dropped_out)

    return result


def plot_timeseries_comparison(
    s1: pd.Series,
    s2: pd.Series,
    label1: str,
    label2: str,
    title: str,
    book,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
    ylim: tuple | None = None,
    hlines: list[tuple[float, str, str, str]] | None = None,
) -> None:
    """Overlay time-series from two runs and plot their ratio.

    hlines: optional list of (value, label, color, linestyle) drawn on the
            overlay plot only (e.g. reference / acceptance lines).
    """
    df1 = s1.to_frame("value")
    df2 = s2.to_frame("value")

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
            df1.rename(columns={"value": label1}),
            df2.rename(columns={"value": label2}),
        ],
        axis=1,
    )

    plotting.plot(
        combined.index,
        combined,
        combined.columns,
        "Relative time (s)",
        title,
    )
    if ylim is not None:
        plotting.plt.ylim(*ylim)
    if hlines:
        for value, hlabel, color, linestyle in hlines:
            plotting.plt.axhline(value, color=color, linestyle=linestyle, label=hlabel)
    plotting.plt.legend(fontsize="small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    overlay_xlim = plotting.plt.xlim()
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
        f"{label2} / {label1}",
    )
    plotting.plt.xlim(overlay_xlim)
    plotting.plt.axhline(1.0, color="k", linestyle="--")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    book.save()


# Color encoding: for app index i and run index r (0=run1, 1=run2), use C{2*i + r}.
# This keeps run1/run2 of the same app as adjacent palette entries, and for a single
# app collapses to the familiar C0 (run1) / C1 (run2) pair.
def _series_color(app_idx: int, run_idx: int) -> str:
    return f"C{app_idx * 2 + run_idx}"


def _app_suffix_label(app_name: str, n_apps: int) -> str:
    """Return a display suffix for the app name when there are multiple apps.

    Only cleans the legend label; it does not change internal app keys.
    """
    if n_apps <= 1 or app_name == "default":
        return ""

    display_name = str(app_name)
    if display_name.endswith("-0"):
        display_name = display_name[:-2]

    return f" {display_name}"


def plot_nic_throughput_comparison(
    thr1: dict[str, pd.Series | None],
    thr2: dict[str, pd.Series | None],
    label1: str,
    label2: str,
    book,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
    acceptance_gbs: float | None = None,
) -> None:
    """Compare total NIC RX throughput between two runs, one line per app per run."""
    def _prep(s: pd.Series | None, start_off: float, end_cut: float) -> pd.Series | None:
        if s is None:
            return None
        df = apply_time_window((s / 1e9).to_frame("v"), start_off, end_cut)
        if df.empty:
            return None
        return rebase_relative_time(df).iloc[:, 0]

    all_apps = sorted(set(thr1.keys()) | set(thr2.keys()))
    n_apps = len(all_apps)

    prepped1 = {
        app: _prep(thr1.get(app), first_file_time_start_offset, first_file_time_end_cut)
        for app in all_apps
    }
    prepped2 = {
        app: _prep(thr2.get(app), second_file_time_start_offset, second_file_time_end_cut)
        for app in all_apps
    }

    if make_same_time_range:
        active = [x for d in (prepped1, prepped2) for x in d.values() if x is not None]
        if active:
            end = min(float(x.index.max()) for x in active)
            for app in all_apps:
                if prepped1[app] is not None:
                    prepped1[app] = prepped1[app].loc[prepped1[app].index <= end]
                if prepped2[app] is not None:
                    prepped2[app] = prepped2[app].loc[prepped2[app].index <= end]

    # ── overlay ───────────────────────────────────────────────────────────────
    plotting.plt.figure()
    ax = plotting.plt.gca()
    has_data = False
    for app_idx, app in enumerate(all_apps):
        sfx = _app_suffix_label(app, n_apps)
        c1 = _series_color(app_idx, 0)
        c2 = _series_color(app_idx, 1)
        if prepped1[app] is not None:
            ax.plot(prepped1[app].index, prepped1[app].values,
                    label=f"{label1}{sfx}", color=c1)
            has_data = True
        if prepped2[app] is not None:
            ax.plot(prepped2[app].index, prepped2[app].values,
                    label=f"{label2}{sfx}", color=c2)
            has_data = True

    if not has_data:
        plotting.plt.close()
        return

    if acceptance_gbs is not None:
        ax.axhline(acceptance_gbs, color="k", linestyle=":",
                   label=f"acceptance ({acceptance_gbs} GB/s)")
    ax.set_xlabel("Relative time (s)")
    ax.set_ylabel("NIC RX throughput (GB/s)")
    ax.set_title("Total NIC RX throughput (GB/s)")
    ax.legend(fontsize="small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    overlay_xlim = ax.get_xlim()
    book.save()

    # ── ratio per app ─────────────────────────────────────────────────────────
    ratio_lines: list[tuple[str | None, pd.Series]] = []
    for app_idx, app in enumerate(all_apps):
        sa, sb = prepped1[app], prepped2[app]
        if sa is None or sb is None:
            continue
        _, sai, sbi = interpolate_to_common_grid(sa, sb)
        if sai.empty or sbi.empty:
            continue
        r = ratio_series(sbi, sai).dropna()
        if not r.empty:
            sfx = _app_suffix_label(app, n_apps).strip()
            ratio_lines.append((sfx or None, r))

    if ratio_lines:
        plotting.plt.figure()
        ax = plotting.plt.gca()
        for name, r in ratio_lines:
            ax.plot(r.index, r.values, label=name)
        ax.axhline(1.0, color="k", linestyle="--")
        ax.set_xlabel("Relative time (s)")
        ax.set_ylabel(f"{label2} / {label1}")
        ax.set_xlim(overlay_xlim)
        if any(name is not None for name, _ in ratio_lines):
            ax.legend(fontsize="small")
        plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
        book.save()


def plot_tp_rate_comparison(
    tp1: dict[str, tuple[pd.Series | None, pd.Series | None]],
    tp2: dict[str, tuple[pd.Series | None, pd.Series | None]],
    label1: str,
    label2: str,
    book,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
    expected_hz: float | None = None,
    acceptance_hz: float | None = None,
    ratio_ylim: tuple[float, float] | None = None,
) -> None:
    """All TPG time-series (produced + sent, all apps, both runs) on one plot (MHz).

    Color encodes (app, run): C{2*app_idx} = run1, C{2*app_idx+1} = run2.
    Linestyle encodes metric: solid = produced, dashed = sent.
    Ratio plot shows produced and sent ratios (run2 / run1) per app.
    """
    def _prep(s: pd.Series | None, start_off: float, end_cut: float) -> pd.Series | None:
        if s is None:
            return None
        df = apply_time_window(s.to_frame("v"), start_off, end_cut)
        if df.empty:
            return None
        return rebase_relative_time(df).iloc[:, 0]

    all_apps = sorted(set(tp1.keys()) | set(tp2.keys()))
    n_apps = len(all_apps)

    # Pre-process all series
    prepped: dict[str, dict] = {}  # app -> {"p1", "s1", "p2", "s2"}
    for app in all_apps:
        prod1, sent1 = tp1.get(app, (None, None))
        prod2, sent2 = tp2.get(app, (None, None))
        p1 = _prep(prod1, first_file_time_start_offset, first_file_time_end_cut)
        s1 = _prep(sent1, first_file_time_start_offset, first_file_time_end_cut)
        p2 = _prep(prod2, second_file_time_start_offset, second_file_time_end_cut)
        s2 = _prep(sent2, second_file_time_start_offset, second_file_time_end_cut)
        prepped[app] = {"p1": p1, "s1": s1, "p2": p2, "s2": s2}

    active = [v for d in prepped.values() for v in d.values() if v is not None]
    if not active:
        return

    if make_same_time_range:
        end = min(float(x.index.max()) for x in active)
        for app in all_apps:
            for k in ("p1", "s1", "p2", "s2"):
                ser = prepped[app][k]
                if ser is not None:
                    prepped[app][k] = ser.loc[ser.index <= end]

    # Scale to MHz
    for app in all_apps:
        for k in ("p1", "s1", "p2", "s2"):
            if prepped[app][k] is not None:
                prepped[app][k] = prepped[app][k] / 1e6

    # ── overlay ───────────────────────────────────────────────────────────────
    plotting.plt.figure()
    ax = plotting.plt.gca()
    for app_idx, app in enumerate(all_apps):
        sfx = _app_suffix_label(app, n_apps)
        c1 = _series_color(app_idx, 0)
        c2 = _series_color(app_idx, 1)
        d = prepped[app]
        if d["p1"] is not None:
            ax.plot(d["p1"].index, d["p1"].values,
                    label=f"{label1}{sfx} produced", color=c1, linestyle="-")
        if d["s1"] is not None:
            ax.plot(d["s1"].index, d["s1"].values,
                    label=f"{label1}{sfx} sent", color=c1, linestyle="--")
        if d["p2"] is not None:
            ax.plot(d["p2"].index, d["p2"].values,
                    label=f"{label2}{sfx} produced", color=c2, linestyle="-")
        if d["s2"] is not None:
            ax.plot(d["s2"].index, d["s2"].values,
                    label=f"{label2}{sfx} sent", color=c2, linestyle="--")

    if expected_hz is not None:
        val = expected_hz / 1e6
        ax.axhline(val, color="red", linestyle=":", label=f"expected hit rate ({val:.3f} MHz)")
    if acceptance_hz is not None:
        val = acceptance_hz / 1e6
        ax.axhline(val, color="k", linestyle=":", label=f"acceptance hit rate ({val:.3f} MHz)")

    ax.set_xlabel("Relative time (s)")
    ax.set_ylabel("TP rate (MHz)")
    ax.legend(fontsize="small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    overlay_xlim = ax.get_xlim()
    book.save()

    # ── ratio: (run2 / run1) per app, produced and sent on one axes ───────────
    ratio_lines: list[tuple[str, pd.Series]] = []
    for app_idx, app in enumerate(all_apps):
        sfx = _app_suffix_label(app, n_apps)
        d = prepped[app]
        for metric, sa, sb in [("produced", d["p1"], d["p2"]), ("sent", d["s1"], d["s2"])]:
            if sa is None or sb is None:
                continue
            _, sai, sbi = interpolate_to_common_grid(sa, sb)
            if sai.empty or sbi.empty:
                continue
            r = ratio_series(sbi, sai).dropna()
            if not r.empty:
                ratio_lines.append((f"{sfx} {metric}".strip(), r))

    if ratio_lines:
        plotting.plt.figure()
        ax = plotting.plt.gca()
        for name, r in ratio_lines:
            ax.plot(r.index, r.values, label=name)
        ax.axhline(1.0, color="k", linestyle="--")
        ax.set_xlabel("Relative time (s)")
        ax.set_ylabel(f"{label2} / {label1}")
        ax.legend(fontsize="small")
        ax.set_xlim(overlay_xlim)
        if ratio_ylim is not None:
            ax.set_ylim(*ratio_ylim)
        plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
        book.save()


def _plot_packet_metric_comparison(
    series1: dict[str, pd.Series | None],
    series2: dict[str, pd.Series | None],
    label1: str,
    label2: str,
    title: str,
    book,
    first_file_time_start_offset: float,
    second_file_time_start_offset: float,
    first_file_time_end_cut: float,
    second_file_time_end_cut: float,
    make_same_time_range: bool,
) -> None:
    """Generic per-app overlay + ratio for a single packet-loss metric."""
    def _prep(s: pd.Series | None, start_off: float, end_cut: float) -> pd.Series | None:
        if s is None:
            return None
        df = apply_time_window(s.to_frame("v"), start_off, end_cut)
        if df.empty:
            return None
        return rebase_relative_time(df).iloc[:, 0]

    all_apps = sorted(set(series1.keys()) | set(series2.keys()))
    n_apps = len(all_apps)

    prepped1 = {
        app: _prep(series1.get(app), first_file_time_start_offset, first_file_time_end_cut)
        for app in all_apps
    }
    prepped2 = {
        app: _prep(series2.get(app), second_file_time_start_offset, second_file_time_end_cut)
        for app in all_apps
    }

    if make_same_time_range:
        active = [x for d in (prepped1, prepped2) for x in d.values() if x is not None]
        if active:
            end = min(float(x.index.max()) for x in active)
            for app in all_apps:
                if prepped1[app] is not None:
                    prepped1[app] = prepped1[app].loc[prepped1[app].index <= end]
                if prepped2[app] is not None:
                    prepped2[app] = prepped2[app].loc[prepped2[app].index <= end]

    # ── overlay ───────────────────────────────────────────────────────────────
    plotting.plt.figure()
    ax = plotting.plt.gca()
    has_data = False
    for app_idx, app in enumerate(all_apps):
        sfx = _app_suffix_label(app, n_apps)
        c1 = _series_color(app_idx, 0)
        c2 = _series_color(app_idx, 1)
        if prepped1[app] is not None:
            ax.plot(prepped1[app].index, prepped1[app].values,
                    label=f"{label1}{sfx}", color=c1)
            has_data = True
        if prepped2[app] is not None:
            ax.plot(prepped2[app].index, prepped2[app].values,
                    label=f"{label2}{sfx}", color=c2)
            has_data = True

    if not has_data:
        plotting.plt.close()
        return

    ax.set_xlabel("Relative time (s)")
    ax.set_ylabel(title)
    ax.set_title(title)
    ax.legend(fontsize="small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    overlay_xlim = ax.get_xlim()
    book.save()

    # ── ratio per app ─────────────────────────────────────────────────────────
    ratio_lines: list[tuple[str | None, pd.Series]] = []
    for app_idx, app in enumerate(all_apps):
        sa, sb = prepped1[app], prepped2[app]
        if sa is None or sb is None:
            continue
        _, sai, sbi = interpolate_to_common_grid(sa, sb)
        if sai.empty or sbi.empty:
            continue
        r = ratio_series(sbi, sai).dropna()
        if not r.empty:
            sfx = _app_suffix_label(app, n_apps).strip()
            ratio_lines.append((sfx or None, r))

    if ratio_lines:
        plotting.plt.figure()
        ax = plotting.plt.gca()
        for name, r in ratio_lines:
            ax.plot(r.index, r.values, label=name)
        ax.axhline(1.0, color="k", linestyle="--")
        ax.set_xlabel("Relative time (s)")
        ax.set_ylabel(f"{label2} / {label1}")
        ax.set_xlim(overlay_xlim)
        if any(name is not None for name, _ in ratio_lines):
            ax.legend(fontsize="small")
        plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
        book.save()


def plot_packet_loss_comparison(
    loss1: dict[str, tuple[pd.Series | None, pd.Series | None]],
    loss2: dict[str, tuple[pd.Series | None, pd.Series | None]],
    label1: str,
    label2: str,
    book,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
) -> None:
    """Compare missed and dropped packet percentages between two runs, per app."""
    kw = dict(
        label1=label1, label2=label2, book=book,
        first_file_time_start_offset=first_file_time_start_offset,
        second_file_time_start_offset=second_file_time_start_offset,
        first_file_time_end_cut=first_file_time_end_cut,
        second_file_time_end_cut=second_file_time_end_cut,
        make_same_time_range=make_same_time_range,
    )

    missed1 = {app: pair[0] for app, pair in loss1.items()}
    missed2 = {app: pair[0] for app, pair in loss2.items()}
    if any(v is not None for v in missed1.values()) and any(v is not None for v in missed2.values()):
        _plot_packet_metric_comparison(missed1, missed2, title="Missed packets (%)", **kw)

    dropped1 = {app: pair[1] for app, pair in loss1.items()}
    dropped2 = {app: pair[1] for app, pair in loss2.items()}
    if any(v is not None for v in dropped1.values()) and any(v is not None for v in dropped2.values()):
        _plot_packet_metric_comparison(dropped1, dropped2, title="Dropped packets (%)", **kw)


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
    plotting.plt.axhline(80, color="k", linestyle=":", label="80%")
    plotting.plt.legend(fontsize="small")
    plotting.plt.bar_label(bars1, fmt="%.2f", fontsize="x-small")
    plotting.plt.bar_label(bars2, fmt="%.2f", fontsize="x-small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.22)
    overlay_xlim = plotting.plt.xlim()
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
        plotting.plt.ylabel(f"{label2} / {label1}")
        plotting.plt.axhline(1.0, color="k", linestyle="--")
        plotting.plt.bar_label(bars, fmt="%.3f", fontsize="x-small")
        plotting.plt.xlim(overlay_xlim)
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
    df1.index = df1.index*10.0
    df2 = rebase_relative_time(df2)
    df2.index = df2.index*10.0

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
    plotting.plt.axhline(80, color="k", linestyle=":", label="80%")
    plotting.plt.legend(fontsize="small")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    overlay_xlim = plotting.plt.xlim()
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
        f"{label2} / {label1}",
    )
    plotting.plt.xlim(overlay_xlim)
    plotting.plt.axhline(1.0, color="k", linestyle="--")
    plotting.plt.subplots_adjust(top=0.88, bottom=0.15)
    book.save()


_RP_CONSTANTS: dict[str, dict] = {
    "apa": {"num_channels": 2560, "num_wibs": 5, "num_nics": 8, "tp_rate": (100, 500)},
    "crp": {"num_channels": 3072, "num_wibs": 6, "num_nics": 8, "tp_rate": (100, 500)},
}


def _n_hit_rate_cols(tp_apps: dict[str, dict]) -> int:
    """Return the number of DLH columns in the hit-rates DataFrame (any app)."""
    for tp_data in tp_apps.values():
        hr_vals = list(utils.search_dict(tp_data, "hit rates").values())
        if hr_vals and hr_vals[0] is not None and not hr_vals[0].empty:
            return hr_vals[0].shape[1]
    return 0


def _infer_tp_reference_rates(
    data_source: str, n_hit_rate_cols: int
) -> tuple[float | None, float | None]:
    """Return total (expected_Hz, acceptance_Hz) for the detector configuration.

    Mirrors the logic in analyze_data.py: rates are per-channel values scaled
    to the full detector (all readout planes).
    """
    ds = (data_source or "").lower()
    rp: dict | None = None
    if "crp" in ds or "np02" in ds:
        rp = _RP_CONSTANTS["crp"]
    elif "apa" in ds or "np04" in ds:
        rp = _RP_CONSTANTS["apa"]

    # Fallback: try to infer APA vs CRP from the number of DLH columns.
    # APA: 5 WIBs * 8 NICs = 40 DLHs per readout plane
    # CRP: 6 WIBs * 8 NICs = 48 DLHs per readout plane
    if rp is None and n_hit_rate_cols and n_hit_rate_cols > 0:
        if (n_hit_rate_cols % (_RP_CONSTANTS["crp"]["num_wibs"] * _RP_CONSTANTS["crp"]["num_nics"])) == 0:
            rp = _RP_CONSTANTS["crp"]
        elif (n_hit_rate_cols % (_RP_CONSTANTS["apa"]["num_wibs"] * _RP_CONSTANTS["apa"]["num_nics"])) == 0:
            rp = _RP_CONSTANTS["apa"]

    if rp is None:
        return None, None

    n_dlh = rp["num_wibs"] * rp["num_nics"]
    n_rp = max(1, n_hit_rate_cols // n_dlh) if n_hit_rate_cols > 0 else 1
    expected = float(min(rp["tp_rate"]) * rp["num_channels"] * n_rp)
    acceptance = float(max(rp["tp_rate"]) * rp["num_channels"] * n_rp)
    return expected, acceptance


def compare_runs(
    first_config: str,
    second_config: str,
    first_file_time_start_offset: float = 0.0,
    second_file_time_start_offset: float = 0.0,
    first_file_time_end_cut: float = 0.0,
    second_file_time_end_cut: float = 0.0,
    make_same_time_range: bool = False,
    out_dir: str | None = None,
    tp_ratio_ylim: tuple[float, float] | None = None,
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

    time_window_kwargs = dict(
        first_file_time_start_offset=first_file_time_start_offset,
        second_file_time_start_offset=second_file_time_start_offset,
        first_file_time_end_cut=first_file_time_end_cut,
        second_file_time_end_cut=second_file_time_end_cut,
        make_same_time_range=make_same_time_range,
    )

    with plotting.PlotBook(output_file, True) as book:
        for host in common_hosts:
            host1 = run1["node_exporter"][host]
            host2 = run2["node_exporter"][host]

            cpu1 = derive_total_cpu_utilization(host1)
            cpu2 = derive_total_cpu_utilization(host2)
            if cpu1 is not None and cpu2 is not None:
                plot_total_cpu_summary_comparison(cpu1, cpu2, label1, label2, host, book)

            mem1 = derive_total_memory_usage(host1)
            mem2 = derive_total_memory_usage(host2)
            if mem1 is not None and mem2 is not None:
                plot_memory_usage_comparison(
                    mem1, mem2, label1, label2, host, book, **time_window_kwargs
                )

        # NIC throughput comparison
        thr1 = derive_nic_throughput(run1["frontend_ethernet"])
        thr2 = derive_nic_throughput(run2["frontend_ethernet"])
        if any(v is not None for v in thr1.values()) or any(v is not None for v in thr2.values()):
            plot_nic_throughput_comparison(
                thr1, thr2, label1, label2, book,
                acceptance_gbs=10.5,
                **time_window_kwargs,
            )

        # TP rate comparison (produced + sent, all apps)
        tp1 = derive_tp_rates(run1["trigger_primitives"])
        tp2 = derive_tp_rates(run2["trigger_primitives"])
        if tp1 or tp2:
            n_cols = _n_hit_rate_cols(run1["trigger_primitives"]) or _n_hit_rate_cols(run2["trigger_primitives"])
            expected_hz, acceptance_hz = _infer_tp_reference_rates(
                args1.get("data_source", ""), n_cols
            )
            plot_tp_rate_comparison(
                tp1, tp2, label1, label2, book,
                expected_hz=expected_hz, acceptance_hz=acceptance_hz,
                ratio_ylim=tp_ratio_ylim,
                **time_window_kwargs,
            )

        # Packet loss comparison (missed + dropped, all apps)
        loss1 = derive_packet_loss(run1["frontend_ethernet"])
        loss2 = derive_packet_loss(run2["frontend_ethernet"])
        if loss1 or loss2:
            plot_packet_loss_comparison(loss1, loss2, label1, label2, book, **time_window_kwargs)

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
@click.option(
    "--tp-ratio-ymin",
    type=float,
    default=None,
    help="Lower bound of the TP ratio plot y-axis. Use together with --tp-ratio-ymax.",
)
@click.option(
    "--tp-ratio-ymax",
    type=float,
    default=None,
    help="Upper bound of the TP ratio plot y-axis. Use together with --tp-ratio-ymin.",
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
    tp_ratio_ymin: float | None,
    tp_ratio_ymax: float | None,
):
    tp_ratio_ylim = None
    if tp_ratio_ymin is not None and tp_ratio_ymax is not None:
        tp_ratio_ylim = (tp_ratio_ymin, tp_ratio_ymax)
    compare_runs(
        first_config=first_config,
        second_config=second_config,
        first_file_time_start_offset=first_file_time_start_offset,
        second_file_time_start_offset=second_file_time_start_offset,
        first_file_time_end_cut=first_file_time_end_cut,
        second_file_time_end_cut=second_file_time_end_cut,
        make_same_time_range=make_same_time_range,
        out_dir=out_dir,
        tp_ratio_ylim=tp_ratio_ylim,
    )


if __name__ == "__main__":
    main()