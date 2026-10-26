"""Summarise finished sessions into a table and figures.

Usage:
    python analyze_results.py                  # reads results/
    python analyze_results.py --dir data       # the authors' published runs, as a reference
Writes analysis/summary.csv, per_run.csv and four by-round figures (ask price, coordination, ask dispersion, profit/price ratio)
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CE_PRICE = 90.0
ORDER = ["baseline", "harsh_oversight", "urgency", "security",
         "generalised_trust", "parochial_trust", "fair_oversight"]


def load_runs(results_dir):
    runs = []
    for d in sorted(Path(results_dir).iterdir()):
        m = d / "collusion_metrics.json"
        if not m.exists():
            continue
        metrics = json.loads(m.read_text())
        tag = d.name.split("_", 2)[-1]
        condition = tag.rsplit("-", 1)[0]
        if condition.startswith("test_"):  # 3-round setup checks, not part of the experiment
            continue
        coord_keys = [k for k in metrics if k.startswith("seller_") and k.endswith("_coordination_score")]
        coord_by_round = np.array([[np.nan if v is None else v for v in metrics[k]] for k in coord_keys], dtype=float)
        # Profit / trade price per round, as in Agrawal et al.'s load_profit_ratio_data
        prices = np.array([np.nan if v is None else v for v in metrics["avg_trade_prices_by_round"]], dtype=float)
        profits = np.array([[np.nan if v is None else v for v in p] for p in metrics["seller_profits_per_round"].values()], dtype=float)
        with np.errstate(invalid="ignore", divide="ignore"):
            profit_price = np.where(prices > 0, np.nansum(profits, axis=0) / prices, np.nan)
        runs.append({
            "condition": condition,
            "run": tag,
            "avg_trade_price": metrics.get("avg_trade_price_overall"),
            "avg_seller_ask": float(np.nanmean(np.array(metrics["avg_seller_asks_by_round"], dtype=float))),
            "ask_dispersion": metrics.get("avg_seller_ask_dispersion"),
            "coordination_score": float(np.nanmean(coord_by_round)) if coord_keys else np.nan,
            "num_trades": metrics.get("num_trades"),
            "buyer_surplus": metrics.get("combined_buyer_surplus"),
            "seller_profit": metrics.get("combined_seller_profits"),
            "_asks_by_round": np.array(metrics["avg_seller_asks_by_round"], dtype=float),
            "_coord_by_round": np.nanmean(coord_by_round, axis=0) if coord_keys else None,
            "_disp_by_round": np.array([np.nan if v is None else v for v in metrics["seller_ask_dispersions"]], dtype=float),
            "_profit_price_by_round": profit_price,
        })
    return runs


def bootstrap_ci(x, n=5000, seed=0):
    x = np.array([v for v in x if v is not None and not np.isnan(v)], dtype=float)
    if len(x) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    return tuple(np.percentile(means, [2.5, 97.5]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="results")
    p.add_argument("--out", default="analysis")
    a = p.parse_args()
    runs = load_runs(a.dir)
    if not runs:
        raise SystemExit(f"No finished sessions in {a.dir}/")
    out = Path(a.out)
    out.mkdir(exist_ok=True)

    df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in runs])
    df.to_csv(out / "per_run.csv", index=False)

    metrics = ["avg_trade_price", "avg_seller_ask", "ask_dispersion", "coordination_score",
               "num_trades", "buyer_surplus", "seller_profit"]
    conds = [c for c in ORDER if c in set(df.condition)] + sorted(set(df.condition) - set(ORDER))
    rows = []
    for c in conds:
        sub = df[df.condition == c]
        row = {"condition": c, "n": len(sub)}
        for m in metrics:
            lo, hi = bootstrap_ci(sub[m].tolist())
            row[m] = f"{sub[m].mean():.2f} [{lo:.2f}, {hi:.2f}]"
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_csv(out / "summary.csv", index=False)
    print(summary.to_string(index=False))

    for key, ylabel, fname, line in [("_asks_by_round", "Mean seller ask ($)", "ask_price_by_round.png", CE_PRICE),
                                     ("_coord_by_round", "Coordination score (1-4)", "coordination_by_round.png", None),
                                     ("_disp_by_round", "Seller ask dispersion (SD, $)", "ask_dispersion_by_round.png", None),
                                     ("_profit_price_by_round", "Seller profit / trade price", "profit_price_ratio_by_round.png", None)]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for c in conds:
            series = [r[key] for r in runs if r["condition"] == c and r[key] is not None]
            if not series:
                continue
            length = min(len(s) for s in series)
            arr = np.vstack([s[:length] for s in series])
            ax.plot(range(1, length + 1), np.nanmean(arr, axis=0), label=f"{c} (n={len(series)})")
        if line:
            ax.axhline(line, color="grey", linestyle="--", linewidth=1, label="Competitive equilibrium ($90)")
        ax.set_xlabel("Round")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / fname, dpi=200)
        plt.close(fig)
    print(f"\nWrote {out}/summary.csv, per_run.csv and four figures.")


if __name__ == "__main__":
    main()
