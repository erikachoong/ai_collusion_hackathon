# Pilot runs on gpt-4.1-mini (not part of the main results)

Pilot runs used to test the pipeline. All seven conditions with gpt-4.1-mini for every
agent (10 sessions per condition, plus two 3-round setup tests).

gpt-4.1-mini sellers never priced above about $85 in any condition, so these runs
cannot show changes in price collusion. The report cites them once, as a robustness check: the direction of the
coordination-score differences (parochial above generalised trust; both oversight conditions lowest, fair no higher than harsh) matches the GPT-4.1 results.

- `results/`: one folder per session (transcripts, judge scores, metrics)
- `analysis/`: summary table and figures from `analyze_results.py --dir pilot_gpt-4.1-mini/results --out pilot_gpt-4.1-mini/analysis`

The main results are in `results_gpt-4.1/` and `analysis_gpt-4.1/`.
