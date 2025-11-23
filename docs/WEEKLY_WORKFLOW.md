# Efficient Weekly Training Workflow

This guide explains how to use the AI coach system efficiently for ongoing training, minimizing cost while maximizing value.

## Overview: Two Modes

### 🔍 Full Analysis Mode (Initial Setup)
**When to use:** Start of season, after major breaks, or monthly deep-dives

**What it does:**
- Extracts up to 365 days of Garmin data
- Runs comprehensive analysis with 3 expert agents (Metrics, Physiology, Activity)
- HITL asks clarifying questions to understand your context
- Generates season plan + detailed weekly plan
- Creates plots and visualizations

**Cost:** $2-5 per run (depending on AI mode and data volume)

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml
```

### ⚡ Weekly Update Mode (Ongoing Training)
**When to use:** Weekly plan refreshes throughout your training block

**What it does:**
- Extracts only last 14 days of fresh Garmin data
- Reuses previous expert analysis (no re-analysis needed)
- Reads your progress notes from config
- Updates only the weekly plan based on progress + fresh metrics
- Skips HITL and plotting

**Cost:** $0.10-0.50 per run (~90% cheaper than full analysis)

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml --update-plan
```

---

## Recommended Workflow

### 1️⃣ Initial Setup (Once per season)

Run full analysis to establish baseline:

```bash
# Edit your config with comprehensive context
pixi run coach-cli --config my_training_config.yaml
```

This generates:
- `analysis.html` - Full performance analysis
- `planning.html` - Season plan + first 2 weeks
- `metrics_result.md`, `activity_result.md`, `physiology_result.md`, `season_plan.md` - Expert analysis (saved for reuse)

### 2️⃣ Weekly Updates (Throughout training block)

**Each week:**

1. **Update progress notes** in your config:

```yaml
weekly_progress:
  notes: |
    Week 1 Status:
    - Completed: 3/3 runs as planned
    - Recovery: Calves feeling 80% better, no pain
    - RHR: Dropped from 58 to 53 (back to baseline)
    - Energy: Felt strong on easy runs, HR staying low
    - Adjustments needed: Ready to add 5km to long run
```

2. **Run weekly update:**

```bash
pixi run coach-cli --config my_training_config.yaml --update-plan
```

3. **Review updated plan** in `planning.html`

### 3️⃣ Monthly Deep-Dive (Optional)

Every 4 weeks, run full analysis again to:
- Re-analyze long-term trends
- Verify fitness progression (VO2 max, chronic load)
- Update season plan if needed
- Generate fresh plots

```bash
pixi run coach-cli --config my_training_config.yaml
```

---

## Config Structure for Weekly Updates

### Minimal Config (for weekly updates)

```yaml
athlete:
  name: "Your Name"
  email: "you@example.com"

context:
  planning: |
    Target race: Half Marathon on May 4, 2026
    Focus: Build to sub-2:00 capability
    
extraction:
  ai_mode: "cost_effective"  # Cheaper for weekly updates

competitions:
  - name: "Sydney Hoka Half Marathon"
    date: "2026-05-04"
    race_type: "Half Marathon"
    priority: "A"
    target_time: "01:59:30"

# Update this weekly
weekly_progress:
  notes: |
    Week 1: Recovery week complete
    - All sessions completed as prescribed
    - RHR back to 51-52 baseline
    - Calves recovered, no issues
    - Ready to progress volume

output:
  directory: "./data"

credentials:
  password: ""
```

### What to Include in Progress Notes

✅ **DO include:**
- Session completion status (3/3 runs, missed Thursday ride)
- Subjective feelings (felt strong, struggled with fatigue)
- Recovery metrics (RHR trends, sleep quality)
- Injury/pain status (calf tightness resolved, knee niggle starting)
- Energy levels and life stress
- Readiness for progression or need for modification

❌ **DON'T include:**
- Detailed workout data (system fetches this automatically from Garmin)
- Metrics you don't have (AI uses Garmin data for HR, pace, etc.)

---

## Cost Comparison

### Example 23-Week Training Block

**Inefficient approach (full analysis every week):**
- 23 full runs × $3.00 = **$69.00**
- Total tokens: ~1.15M

**Efficient approach (full + weekly updates):**
- 1 initial full analysis: $3.00
- 4 monthly deep-dives: $12.00
- 18 weekly updates × $0.25 = $4.50
- **Total: $19.50** (72% savings)
- Total tokens: ~300K

---

## Troubleshooting

### Error: "Missing previous analysis files"

**Problem:** You ran `--update-plan` without running full analysis first

**Solution:** Run initial full analysis:
```bash
pixi run coach-cli --config my_training_config.yaml
```

### Weekly update doesn't reflect progress notes

**Problem:** `weekly_progress.notes` section is empty or not updated

**Solution:** Edit your config and add detailed progress notes before running `--update-plan`

### Plan isn't adapting to my feedback

**Problem:** Progress notes are too vague ("Week 1 done")

**Solution:** Provide specific, actionable details:
```yaml
weekly_progress:
  notes: |
    Week 1: Struggled more than expected
    - Completed 2/3 runs (skipped Thursday - too fatigued)
    - RHR elevated at 55 (baseline is 51)
    - Heavy legs throughout the week
    - Work stress high this week
    - Need: Reduce volume, focus on recovery
```

### Want to change race date or goals

**Update your config:**
1. Edit `competitions` section with new date/target
2. Run full analysis again (not `--update-plan`) to regenerate season plan:
```bash
pixi run coach-cli --config my_training_config.yaml
```

---

## Advanced Tips

### Pixi Task Shortcuts

Add to your `pixi.toml`:

```toml
[tasks]
coach-full = "python cli/garmin_ai_coach_cli.py --config my_training_config.yaml"
coach-update = "python cli/garmin_ai_coach_cli.py --config my_training_config.yaml --update-plan"
```

Then use:
```bash
pixi run coach-full    # Full analysis
pixi run coach-update  # Weekly update
```

### Archiving Previous Plans

Keep history of your coaching advice:

```bash
# Before running update, archive previous plan
cp data/planning.html data/archive/planning_2025-12-01.html

# Then run update
pixi run coach-update
```

### Multiple Athletes/Configs

Manage different configs for different seasons:

```
configs/
├── 2026_marathon_block.yaml
├── 2026_triathlon_season.yaml
└── offseason_maintenance.yaml
```

Run with:
```bash
pixi run coach-cli --config configs/2026_marathon_block.yaml --update-plan
```

---

## Key Takeaways

1. **Initial analysis is comprehensive and expensive** - Do it once per season or monthly
2. **Weekly updates are fast and cheap** - Use them for weekly plan refreshes
3. **Progress notes are critical** - Specific feedback = better plan adaptations
4. **Reuse analysis artifacts** - Previous expert analysis stays relevant for weeks
5. **HITL is for understanding, not updates** - Weekly updates skip questions for efficiency

The system is designed to give you AI coaching insights at sustainable costs, balancing deep analysis with lightweight updates throughout your training journey.
