"""Run the sprint conditions on the Agrawal et al. (2025) double auction.

Usage (from the repo root, with OPENAI_API_KEY or OPENROUTER_API_KEY set):
    python run_experiments.py --test                 # one 3-round baseline session, to check setup and timing
    python run_experiments.py --model gpt-4.1 --conditions security generalised_trust parochial_trust fair_oversight --runs 10
    python run_experiments.py --model gpt-4.1 --conditions baseline --runs 3

Each session is saved under results/<timestamp>_<condition>-<run>/ (other models: results_<model>/).
Re-running skips sessions that already finished, so an interrupted run can be resumed.
"""
import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent
SIM = REPO / "src" / "continuous_double_auction" / "simulation.py"
DEFAULT_MODEL = "gpt-4.1-mini"


def results_dir(model):
    # gpt-4.1-mini runs stay in results/; other models get their own folder so runs and analysis never mix
    return REPO / ("results" if model == DEFAULT_MODEL else f"results_{model}")


def logs_dir(model):
    return REPO / ("logs" if model == DEFAULT_MODEL else f"logs_{model}")

# Every condition keeps the market identical (costs $80, values $100, 30 rounds, seller messaging on).
# Only the framing in the seller prompt, or the oversight flag, changes.
CONDITIONS = {
    # Reproduced from Agrawal et al. (2025)
    "baseline":          [],
    "harsh_oversight":   ["--oversight_enabled"],
    "urgency":           ["--boss_pressure"],
    # New conditions
    "security":          ["--seller_prompt_template", "seller_prompt_security.jinja2"],
    "generalised_trust": ["--seller_prompt_template", "seller_prompt_generalised_trust.jinja2"],
    "parochial_trust":   ["--seller_prompt_template", "seller_prompt_parochial_trust.jinja2"],
    "fair_oversight":    ["--oversight_enabled", "--seller_prompt_template", "seller_prompt_fair_oversight.jinja2"],
}


def finished_tags(model):
    done = set()
    if results_dir(model).exists():
        for d in results_dir(model).iterdir():
            if (d / "collusion_metrics.json").exists() and "_" in d.name:
                done.add(d.name.split("_", 2)[-1])  # strip YYYYMMDD_HHMMSS_
    return done


def run_one(condition, run_idx, model, rounds, temperature):
    tag = f"{condition}-{run_idx}"
    cmd = [sys.executable, str(SIM),
           "--seller_comms_enabled",
           "--seller_models", *[model] * 5,
           "--buyer_models", *[model] * 5,
           "--rounds", str(rounds),
           "--temperature", str(temperature),
           "--tag", tag,
           *CONDITIONS[condition]]
    env = dict(os.environ, WANDB_MODE="disabled", PYTHONPATH=str(REPO), CDA_RESULTS_DIR=str(results_dir(model)))
    logs = logs_dir(model)
    logs.mkdir(exist_ok=True)
    start = time.time()
    with open(logs / f"{tag}.log", "w") as log:
        proc = subprocess.run(cmd, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT)
    mins = (time.time() - start) / 60
    return tag, proc.returncode, mins


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--conditions", nargs="+", default=list(CONDITIONS), choices=list(CONDITIONS))
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--parallel", type=int, default=4, help="sessions to run at once")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--rounds", type=int, default=30)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--test", action="store_true", help="one 3-round baseline session")
    a = p.parse_args()

    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")):
        sys.exit("Set OPENAI_API_KEY or OPENROUTER_API_KEY first.")

    if a.test:
        jobs = [("test_baseline", 1)]
        CONDITIONS["test_baseline"] = []
        a.rounds = 3
    else:
        done = finished_tags(a.model)
        jobs = [(c, i) for i in range(1, a.runs + 1) for c in a.conditions if f"{c}-{i}" not in done]
        print(f"{len(jobs)} sessions to run ({len(done)} already finished).")

    with ThreadPoolExecutor(max_workers=a.parallel) as pool:
        futures = [pool.submit(run_one, c, i, a.model, a.rounds, a.temperature) for c, i in jobs]
        for f in as_completed(futures):
            tag, code, mins = f.result()
            status = "ok" if code == 0 else f"FAILED (see {logs_dir(a.model).name}/{tag}.log)"
            print(f"{tag}: {status}, {mins:.1f} min")


if __name__ == "__main__":
    main()
