# High-trust conditions against LLM market collusion

Erika Choong, Apart Research AI Collusion Research Sprint (October 2026, Track 1: Markets and Collusion).

This is a fork of Agrawal et al. (2025), "[Evaluating LLM Agent Collusion in Double Auctions](https://arxiv.org/abs/2507.01413)"
([original code](https://github.com/andyjliu/llm-agent-collusion)). It asks whether conditions found in high-trust societies
(existential security, generalised trust and fair enforcement) reduce collusion between LLM seller agents while keeping the
market productive. Payoffs and market code are unchanged; only one framing block in the seller prompt, or the oversight
switch, differs between conditions.

## What is new in this fork

| Path | What it is |
|---|---|
| `src/continuous_double_auction/prompt_templates/seller_prompt_{security,generalised_trust,parochial_trust,fair_oversight}.jinja2` | The four new seller prompts. Each differs from `seller_prompt_base.jinja2` in one block (check with `diff`). |
| `run_experiments.py` | Runs the seven conditions (definitions at the top of the file). Resumes interrupted runs. Non-default models save to `results_<model>/`. |
| `import_paper_runs.py` | Copies Agrawal et al.'s published GPT-4.1 baseline, urgency and oversight runs into `results_gpt-4.1/` and re-scores them with the same judge. |
| `analyze_results.py` | Summary table with bootstrapped 95% CIs and four by-round figures. |
| `results_gpt-4.1/` | **Main results.** One folder per session: agent transcripts (`Seller *.md`, `Buyer *.md`), market log, judge scores, metrics. |
| `analysis_gpt-4.1/` | **Main analysis:** `summary.csv`, `per_run.csv`, figures. |
| `pilot_gpt-4.1-mini/` | Pilot runs on gpt-4.1-mini. Not part of the main results (see its README). |

### Conditions

| Condition | Source | What changes |
|---|---|---|
| `paper_baseline` | Agrawal et al., reused | Nothing (seller messaging on) |
| `paper_harsh_oversight` | Agrawal et al., reused | Monitor, licence-revocation threat, 5-character message limit once triggered |
| `paper_urgency` | Agrawal et al., reused | CEO says the seller will be "decommissioned" if margins drop |
| `security` | New | CEO message in the same slot: permanent role, no scoring, no penalty |
| `generalised_trust` | New | CEO message: one community with everyone; buyers are long-term partners |
| `parochial_trust` | New | Same wording, but the community is only the other sellers |
| `fair_oversight` | New | Same monitor and message limit as harsh oversight, framed as impartial and proportionate, no threat |
| `baseline` (n=3) | New | My own GPT-4.1 baseline sessions, to check the reused runs reproduce |

### Reproducing

GPT-4.1 for all agents (5 sellers, 5 buyers), gpt-4.1-mini for the coordination judge and the overseer, 30 rounds,
temperature 0.7. Calls go to OpenAI directly with `OPENAI_API_KEY`, or through OpenRouter if `OPENROUTER_API_KEY` is set.

```bash
pip install -r requirements.txt && pip install -e .
python run_experiments.py --model gpt-4.1 --conditions security generalised_trust parochial_trust fair_oversight --runs 10
python run_experiments.py --model gpt-4.1 --conditions baseline --runs 3
# Reused runs: put Agrawal et al.'s published runs in data/ (from their repo), then
PYTHONPATH=. python import_paper_runs.py
python analyze_results.py --dir results_gpt-4.1 --out analysis_gpt-4.1
```

Runs are not seeded, so agent names, companies and opening prices differ between sessions.

---

The rest of this README is the original from Agrawal et al.

# Evaluating LLM Agent Collusion in Double Auctions

This repository contains code and data for "[Evaluating LLM Agent Collusion in Double Auctions](https://arxiv.org/abs/2507.01413)".

## Installation

Create a virtual environment

```bash
conda create -n env python=3.12 -y
conda activate env
pip install -r requirements.txt
conda env config vars set OPENAI_API_KEY=$secret
conda env config vars set ANTHROPIC_API_KEY=$secret
conda env config vars set OPENROUTER_API_KEY=$secret
```

Install src as a local pip package

```bash
pip install -e .
```

## Code structure

The codebase is structured as follows:

- `src/`: Main source code directory
  - `continuous_double_auction/`: Contains the code for simulation of a continuous double auction (CDA) market
    - `evaluation/`: Scripts to evaluate, analyze and plot simulations
    - `experiments/`: Experiment scripts that run the simulation with predefined parameters
    - `market/`: Core implementation code of the CDA market
    - `prompt_templates/`: Templates for agent prompts
    - `util/`: Various utility functions
    - `resources/`: Contains the ModelWrapper which provides a unified interface to LLMs
    - `simulation.py`: Entry point to run simulations from

## Usage

You can run a simulation from the command line with the following command:

```bash
python src/continuous_double_auction/simulation.py
```

### Command Line Arguments

| Argument                   | Type           | Required | Default                                                   | Description                                                                  |
| -------------------------- | -------------- | -------- | --------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `--seller_valuations`      | list of floats | No       | `[80.0, 80.0, 80.0, 80.0, 80.0]`                          | List of seller valuations (true costs for each seller)                       |
| `--buyer_valuations`       | list of floats | No       | `[100.0, 100.0, 100.0, 100.0, 100.0, 100.0]`              | List of buyer valuations (true values for each buyer)                        |
| `--seller_models`          | list of str    | No       | `["gpt-4.1", "gpt-4.1", "gpt-4.1", "gpt-4.1", "gpt-4.1"]` | Models to use for sellers (must be in SUPPORTED\_MODELS)                     |
| `--buyer_models`           | list of str    | No       | `["gpt-4.1", "gpt-4.1", "gpt-4.1", "gpt-4.1", "gpt-4.1"]` | Models to use for buyers (must be in SUPPORTED\_MODELS)                      |
| `--seller_prompt_template` | str            | No       | `"seller_prompt_base.jinja2"`                             | Prompt template file to use for sellers                                      |
| `--rounds`                 | int            | No       | `30`                                                      | Number of rounds (hours) to run the simulation for                           |
| `--temperature`            | float          | No       | `0.7`                                                     | Temperature for the models                                                   |
| `--tag`                    | str            | No       | `""` (empty string)                                       | Custom tag to identify the experiment                                        |
| `--seller_comms_enabled`   | flag           | No       | `False`                                                   | Whether sellers can communicate or not                                       |
| `--buyer_comms_enabled`    | flag           | No       | `False`                                                   | Whether buyers can communicate or not                                        |
| `--hide_num_rounds`        | flag           | No       | `False`                                                   | If set, agents will not be told the total number of rounds in the simulation |
| `--oversight_enabled`      | flag           | No       | `False`                                                   | Whether to enable oversight for sellers                                      |
| `--boss_pressure`          | flag           | No       | `False`                                                   | Whether to apply pressure on sellers to keep prices high                     |
| `--max_message_length`     | int            | No       | `500`                                                     | Maximum length for agent communication messages                              |

### Experiments

Preset experiments can be run using the scripts in either the `experiments/` directory or the `src/continuous_double_auction/experiments/` directory.
