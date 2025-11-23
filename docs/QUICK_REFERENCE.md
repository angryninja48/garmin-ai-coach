# Quick Reference: Weekly Workflow Commands

## Initial Setup (Once)

```bash
# Create config
pixi run coach-init my_training_config.yaml

# Edit config with your details (athlete, goals, context)
# Then run full analysis
pixi run coach-cli --config my_training_config.yaml
```

**Cost:** $2-5 | **Time:** 3-5 min | **Generates:** analysis.html, planning.html, expert .md files

---

## Weekly Updates (Every Week)

```bash
# 1. Edit config - add progress notes
# 2. Run update
pixi run coach-cli --config my_training_config.yaml --update-plan
```

**Cost:** $0.10-0.50 | **Time:** 30-60 sec | **Updates:** planning.html only

---

## Monthly Check (Optional)

```bash
# Re-run full analysis every 4 weeks
pixi run coach-cli --config my_training_config.yaml
```

**Cost:** $2-5 | **Time:** 3-5 min | **Verifies:** Long-term fitness trends

---

## Config Template: Weekly Progress

```yaml
weekly_progress:
  notes: |
    Week X Status:
    - Completed: X/X runs as planned
    - Recovery: [RHR, injuries, energy]
    - Performance: [How workouts felt]
    - Adjustments needed: [More/less volume/intensity]
```

---

## When to Use Each Mode

| Scenario | Mode | Command |
|----------|------|---------|
| Start of season | Full | `pixi run coach-cli --config <config>` |
| After 4+ weeks off | Full | `pixi run coach-cli --config <config>` |
| Weekly plan refresh | Update | `pixi run coach-cli --config <config> --update-plan` |
| Monthly progress check | Full | `pixi run coach-cli --config <config>` |
| Changed race date/goals | Full | `pixi run coach-cli --config <config>` |

---

## Troubleshooting

**"Missing previous analysis files"**
→ Run full analysis first: `pixi run coach-cli --config <config>`

**Weekly update not adapting**
→ Add detailed `weekly_progress.notes` to config before running `--update-plan`

**Plan doesn't reflect new race**
→ Edit `competitions` section, then run full analysis (not `--update-plan`)

---

## File Structure

```
data/
├── analysis.html              # Full performance analysis
├── planning.html              # Weekly training plan (updated by both modes)
├── metrics_result.md          # Reused by --update-plan
├── activity_result.md         # Reused by --update-plan
├── physiology_result.md       # Reused by --update-plan
├── season_plan.md             # Reused by --update-plan
└── summary.json               # Cost/metadata tracking
```

---

## Cost Comparison: 23-Week Block

| Approach | Cost | Savings |
|----------|------|---------|
| Full analysis every week | $69 | - |
| Smart workflow (1 initial + 4 monthly + 18 weekly) | $20 | 71% |

---

## More Info

- Full workflow guide: [docs/WEEKLY_WORKFLOW.md](WEEKLY_WORKFLOW.md)
- Example usage: [docs/EXAMPLE_WEEKLY_USAGE.md](EXAMPLE_WEEKLY_USAGE.md)
- Config details: [cli/README.md](../cli/README.md)
