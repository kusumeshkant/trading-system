"""
Chart generators — all return PNG bytes using matplotlib (Agg backend, no display needed).
"""
import io
from typing import List, Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_STYLE = {
    "figure.facecolor": "#FAFAFA",
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#CCCCCC",
    "axes.grid": True,
    "grid.color": "#EEEEEE",
    "grid.linewidth": 0.8,
    "font.family": "DejaVu Sans",
    "font.size": 9,
}
_GREEN = "#22C55E"
_RED = "#EF4444"
_BLUE = "#4A9EFF"
_DARK = "#1A1A2E"


def _save(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def equity_curve_chart(equity: List[float], initial: float = 10_000) -> bytes:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(12, 5))
        x = range(len(equity))
        ax.plot(x, equity, color=_BLUE, linewidth=2, zorder=3)
        ax.fill_between(x, equity, initial, where=[v >= initial for v in equity],
                        alpha=0.15, color=_GREEN)
        ax.fill_between(x, equity, initial, where=[v < initial for v in equity],
                        alpha=0.15, color=_RED)
        ax.axhline(initial, color="#888888", linestyle="--", linewidth=0.9, label=f"Start ${initial:,.0f}")
        ax.set_title("Equity Curve", fontsize=14, fontweight="bold", color=_DARK)
        ax.set_xlabel("Trade #")
        ax.set_ylabel("Portfolio Value ($)")
        ax.legend(fontsize=8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        fig.tight_layout()
        return _save(fig)


def drawdown_chart(equity: List[float]) -> bytes:
    if len(equity) < 2:
        return b""
    arr = np.array(equity, dtype=float)
    peak = np.maximum.accumulate(arr)
    dd_pct = np.where(peak > 0, (peak - arr) / peak * 100, 0.0)

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(12, 4))
        x = range(len(dd_pct))
        ax.fill_between(x, -dd_pct, 0, color=_RED, alpha=0.4)
        ax.plot(x, -dd_pct, color=_RED, linewidth=1)
        ax.set_title("Drawdown (%)", fontsize=14, fontweight="bold", color=_DARK)
        ax.set_xlabel("Trade #")
        ax.set_ylabel("Drawdown (%)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
        fig.tight_layout()
        return _save(fig)


def pnl_bar_chart(dates: List[str], pnl_values: List[float]) -> bytes:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(max(10, len(dates) * 0.4), 5))
        bar_colors = [_GREEN if v >= 0 else _RED for v in pnl_values]
        ax.bar(dates, pnl_values, color=bar_colors, edgecolor="white", linewidth=0.5, zorder=3)
        ax.axhline(0, color="#888888", linewidth=0.9)
        ax.set_title("Daily Net P&L", fontsize=14, fontweight="bold", color=_DARK)
        ax.set_xlabel("Date")
        ax.set_ylabel("Net P&L ($)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:+,.2f}"))
        plt.xticks(rotation=45, ha="right", fontsize=8)
        fig.tight_layout()
        return _save(fig)


def strategy_performance_chart(strategy_data: Dict[str, dict]) -> bytes:
    if not strategy_data:
        return b""
    strategies = list(strategy_data.keys())
    pnls = [strategy_data[s].get("net_pnl", 0) for s in strategies]
    bar_colors = [_GREEN if v >= 0 else _RED for v in pnls]
    max_abs = max(abs(p) for p in pnls) or 1

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(10, max(4, len(strategies) * 0.9)))
        bars = ax.barh(strategies, pnls, color=bar_colors, edgecolor="white", zorder=3)
        ax.axvline(0, color="#888888", linewidth=0.9)
        ax.set_title("Strategy Performance (Net P&L)", fontsize=14, fontweight="bold", color=_DARK)
        ax.set_xlabel("Net P&L ($)")
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:+,.2f}"))
        for bar, v in zip(bars, pnls):
            offset = max_abs * 0.02
            ax.text(v + (offset if v >= 0 else -offset),
                    bar.get_y() + bar.get_height() / 2,
                    f"${v:+.2f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
        fig.tight_layout()
        return _save(fig)


def pair_performance_chart(pair_data: Dict[str, dict]) -> bytes:
    return strategy_performance_chart(pair_data)


def win_loss_pie_chart(wins: int, losses: int) -> bytes:
    total = wins + losses
    if total == 0:
        return b""
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(6, 6))
        labels = [f"Wins ({wins})", f"Losses ({losses})"]
        ax.pie(
            [wins, losses],
            labels=labels,
            colors=[_GREEN, _RED],
            explode=(0.05, 0),
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontsize": 11},
            wedgeprops={"edgecolor": "white", "linewidth": 2},
        )
        ax.set_title(f"Win / Loss Distribution  (n={total})", fontsize=13, fontweight="bold", color=_DARK)
        fig.tight_layout()
        return _save(fig)


def hourly_heatmap(hourly_data: Dict[str, dict]) -> bytes:
    if not hourly_data:
        return b""
    hours = [str(h) for h in range(24)]
    pnls = [hourly_data.get(h, {}).get("net_pnl", 0) for h in hours]
    bar_colors = [_GREEN if v >= 0 else _RED for v in pnls]

    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.bar(hours, pnls, color=bar_colors, edgecolor="white", linewidth=0.5, zorder=3)
        ax.axhline(0, color="#888888", linewidth=0.9)
        ax.set_title("P&L by Hour of Day (UTC)", fontsize=14, fontweight="bold", color=_DARK)
        ax.set_xlabel("Hour (UTC)")
        ax.set_ylabel("Net P&L ($)")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:+,.2f}"))
        fig.tight_layout()
        return _save(fig)


def rr_distribution_chart(rr_values: List[float]) -> bytes:
    if not rr_values:
        return b""
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.hist(rr_values, bins=20, color=_BLUE, edgecolor="white", linewidth=0.5, zorder=3)
        ax.axvline(1.0, color=_RED, linestyle="--", linewidth=1, label="R:R = 1.0")
        ax.axvline(float(np.mean(rr_values)), color=_GREEN, linestyle="--", linewidth=1,
                   label=f"Mean = {np.mean(rr_values):.2f}")
        ax.set_title("R:R Distribution", fontsize=14, fontweight="bold", color=_DARK)
        ax.set_xlabel("Risk : Reward")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=8)
        fig.tight_layout()
        return _save(fig)
