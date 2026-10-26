"""Copy Agrawal et al.'s published GPT-4.1 runs into results_gpt-4.1/ and re-score them with my judge.

Their baseline, urgency and oversight runs used the same prompts and market as mine (checked), so I reuse
them instead of paying to re-run them. Only the coordination scores are recomputed, so that every row in
results_gpt-4.1/ is scored by the same judge (gpt-4.1-mini). Prices, trades and profits are their own numbers.

    python import_paper_runs.py

Copies are tagged paper_baseline-N, paper_urgency-N and paper_harsh_oversight-N, so they sit next to (and are
never confused with) my own GPT-4.1 runs. data/ is left untouched. Re-running skips runs already re-scored.
"""
import json
import os
import re
import shutil
from pathlib import Path

os.environ.setdefault("WANDB_MODE", "disabled")
from src.continuous_double_auction.evaluation.evaluate import run_llm_eval

REPO = Path(__file__).resolve().parent
DATA = REPO / "data"
OUT = REPO / "results_gpt-4.1"
# paper tag -> my condition name
PAPER_CONDITIONS = {"base-seller_comms": "paper_baseline",
                    "boss_pressure": "paper_urgency",
                    "oversight": "paper_harsh_oversight"}


def main():
    OUT.mkdir(exist_ok=True)
    for src in sorted(DATA.iterdir()):
        m = re.fullmatch(r"(\d{8}_\d{6})_(.+)-(\d+)", src.name)
        if not m or m.group(2) not in PAPER_CONDITIONS:
            continue
        dest = OUT / f"{m.group(1)}_{PAPER_CONDITIONS[m.group(2)]}-{m.group(3)}"
        if (dest / "rescored.flag").exists():
            print(f"{dest.name}: already re-scored")
            continue
        shutil.copytree(src, dest, dirs_exist_ok=True)

        metadata = json.loads((dest / "experiment_metadata.json").read_text())
        evals = run_llm_eval(metadata, dest / "unified.log")  # only the folder is used; seller .md files are read
        (dest / "llm_eval_full.json").write_text(json.dumps(
            [{"seller_id": s, "rounds": r} for s, r in evals.items()], indent=2, ensure_ascii=False))

        metrics = json.loads((dest / "collusion_metrics.json").read_text())
        metrics = {k: v for k, v in metrics.items() if not k.endswith("_coordination_score")}
        for seller_id, rounds in evals.items():
            metrics[f"{seller_id}_coordination_score"] = [
                r["data"].get("score") if r.get("status") == "success" and isinstance(r.get("data"), dict) else None
                for r in rounds]
        (dest / "collusion_metrics.json").write_text(json.dumps(metrics, indent=2))
        (dest / "rescored.flag").write_text("coordination scores recomputed with my judge\n")
        print(f"{dest.name}: re-scored")


if __name__ == "__main__":
    main()
