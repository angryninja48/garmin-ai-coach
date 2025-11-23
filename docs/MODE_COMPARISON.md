# Mode Comparison: Full Analysis vs Weekly Update

## Side-by-Side Comparison

| Feature | Full Analysis | Weekly Update |
|---------|--------------|---------------|
| **Command** | `pixi run coach-cli --config <config>` | `pixi run coach-cli --config <config> --update-plan` |
| **Cost** | $2-5 per run | $0.10-0.50 per run |
| **Time** | 3-5 minutes | 30-60 seconds |
| **Data extracted** | Up to 365 days | Last 14 days only |
| **Tokens used** | 75,000-120,000 | 8,000-15,000 |
| **Analysis agents** | 3 experts (Metrics, Physiology, Activity) | None (reuses previous) |
| **HITL questions** | Yes (2-5 questions typical) | No |
| **Season plan** | Generated fresh | Reused from previous |
| **Weekly plan** | Generated fresh | Generated fresh |
| **Plots/visualizations** | Generated (if enabled) | Reused from previous |
| **Expert .md files** | Saved for reuse | Read and reused |

---

## What Each Mode Does

### Full Analysis Mode

**Workflow:**
1. Extract up to 365 days from Garmin
2. Prepare optimized context (recent + trends)
3. Run 3 parallel summarizers
4. Run 3 expert agents (may ask HITL questions)
5. Synthesize expert analyses
6. Format analysis HTML
7. Generate plots (if enabled)
8. Create season plan
9. Integrate data for planning
10. Generate weekly plan
11. Format planning HTML

**Output files created/updated:**
- ✅ `analysis.html`
- ✅ `planning.html`
- ✅ `metrics_result.md`
- ✅ `activity_result.md`
- ✅ `physiology_result.md`
- ✅ `season_plan.md`
- ✅ `summary.json`

### Weekly Update Mode

**Workflow:**
1. Extract last 14 days from Garmin
2. Load previous expert .md files
3. Integrate data for planning (with fresh metrics + progress notes)
4. Generate updated weekly plan
5. Format planning HTML

**Output files created/updated:**
- ✅ `planning.html`
- ✅ `summary.json` (adds weekly update metadata)

**Output files reused (not regenerated):**
- 🔄 `metrics_result.md` (from previous full analysis)
- 🔄 `activity_result.md` (from previous full analysis)
- 🔄 `physiology_result.md` (from previous full analysis)
- 🔄 `season_plan.md` (from previous full analysis)

---

## When to Use Each Mode

### Use Full Analysis When:

✅ **Starting a new training block**
- Beginning of season
- New A-priority race on calendar
- Major goal change

✅ **After extended breaks**
- 4+ weeks off training
- Injury recovery period
- Vacation/travel break

✅ **Monthly deep-dives**
- Verify long-term fitness trends
- Check VO2 max progression
- Regenerate plots with 4 weeks of new data

✅ **Significant context changes**
- Changed race dates
- New injury/limitation
- Different training philosophy

### Use Weekly Update When:

✅ **Regular weekly refreshes**
- Continuing existing training block
- Following prescribed season plan
- Normal week-to-week progression

✅ **Minor adjustments needed**
- Reporting progress on current plan
- Adjusting next week based on how this week went
- Managing fatigue/recovery within existing framework

✅ **Cost-conscious operation**
- Want AI coaching but minimizing spend
- Don't need re-analysis of long-term trends
- Previous analysis still relevant

---

## Functional Differences

### What Weekly Update CAN Do

✅ Adjust weekly plan based on your progress notes  
✅ Account for latest Garmin metrics (RHR, recent workouts)  
✅ Modify volume/intensity based on readiness signals  
✅ Add/remove workout days based on recovery status  
✅ Incorporate recent performance indicators  
✅ Maintain alignment with season plan  

### What Weekly Update CANNOT Do

❌ Re-analyze long-term trends (e.g., 6-month VO2 max trajectory)  
❌ Update plots/visualizations  
❌ Change season plan structure  
❌ Ask clarifying questions (no HITL)  
❌ Generate new analysis HTML  
❌ Re-evaluate race goals or periodization  

---

## Example Scenarios

### Scenario 1: Week 3 of Base Building

**Situation:** Following prescribed plan, everything going well  
**Best mode:** 🟢 Weekly Update  
**Why:** No need to re-analyze 6 months of data. Just update next week's plan based on current progress.

---

### Scenario 2: Injured, 3 Weeks Off

**Situation:** Hamstring strain, took 3 weeks completely off  
**Best mode:** 🔴 Full Analysis  
**Why:** Significant detraining likely occurred. Need fresh analysis of fitness levels and adjusted season plan.

---

### Scenario 3: First Month Going Great

**Situation:** 4 weeks into training, want to verify fitness gains  
**Best mode:** 🔴 Full Analysis  
**Why:** Monthly deep-dive to confirm VO2 max improving, chronic load building safely, generate updated plots.

---

### Scenario 4: Tempo Run Felt Too Hard

**Situation:** This week's tempo was too aggressive, need easier next week  
**Best mode:** 🟢 Weekly Update  
**Why:** Minor adjustment within existing framework. Add note to `weekly_progress` explaining, system will adjust intensity.

---

### Scenario 5: Race Date Changed

**Situation:** Target race moved from May to June  
**Best mode:** 🔴 Full Analysis  
**Why:** Season plan needs restructuring with new timeline. Update config `competitions` section and regenerate.

---

## Cost Analysis: Real Examples

### Conservative Athlete (18-week block)

**Full analysis every week:**
- 18 weeks × $2.50 = **$45.00**

**Smart workflow:**
- 1 initial: $2.50
- 3 monthly checks: $7.50
- 14 weekly updates: $3.50
- **Total: $13.50** (70% savings)

---

### Aggressive Analyst (23-week block, higher AI mode)

**Full analysis every week:**
- 23 weeks × $4.50 = **$103.50**

**Smart workflow:**
- 1 initial: $4.50
- 5 monthly checks: $22.50
- 17 weekly updates: $8.50
- **Total: $35.50** (66% savings)

---

### Budget-Conscious (12-week block, cost_effective mode)

**Full analysis every week:**
- 12 weeks × $2.00 = **$24.00**

**Smart workflow:**
- 1 initial: $2.00
- 2 monthly checks: $4.00
- 9 weekly updates: $1.80
- **Total: $7.80** (68% savings)

---

## Technical Implementation Details

### Full Analysis: Agent Architecture

```
START
  ↓
[Metrics Summarizer] [Physiology Summarizer] [Activity Summarizer]
  ↓                    ↓                        ↓
[Metrics Expert]   [Physiology Expert]     [Activity Expert]
  ↓                    ↓                        ↓
  └──────────────► [Synthesis] ◄───────────────┘
                      ↓
                  [Formatter]
                      ↓
               [Plot Resolution]
                      ↓
                 [Season Planner] ← (Metrics/Physiology/Activity Experts feed here too)
                      ↓
              [Data Integration]
                      ↓
              [Weekly Planner]
                      ↓
              [Plan Formatter]
                      ↓
                     END
```

**Total nodes:** 13  
**Parallel execution:** Yes (3 summarizers, 3 experts run in parallel)  
**LLM calls:** ~15-20 depending on HITL interactions

---

### Weekly Update: Streamlined Architecture

```
START
  ↓
[Data Integration] ← Loads previous expert .md files
  ↓
[Weekly Planner] ← Uses progress notes + fresh metrics
  ↓
[Plan Formatter]
  ↓
END
```

**Total nodes:** 3  
**Parallel execution:** No (sequential, very fast)  
**LLM calls:** ~3-4

---

## Recommended Frequency

### Conservative Approach
- Full analysis: Initial + every 4 weeks
- Weekly updates: Every other week
- **Cost per 20-week block:** ~$15

### Balanced Approach
- Full analysis: Initial + every 4 weeks
- Weekly updates: Every week
- **Cost per 20-week block:** ~$20

### Aggressive Approach
- Full analysis: Initial + every 3 weeks
- Weekly updates: Every week
- **Cost per 20-week block:** ~$30

### Budget Approach
- Full analysis: Initial + mid-block + pre-race
- Weekly updates: Every 2 weeks
- **Cost per 20-week block:** ~$10

---

## Quality Considerations

### Is Weekly Update "Good Enough"?

**Yes, when:**
- Your training is progressing normally
- Previous analysis captured your current fitness well
- No major disruptions (injury, illness, life stress)
- Season plan is still appropriate
- You provide detailed progress notes

**No, consider full analysis when:**
- It's been 4+ weeks since last full analysis
- Significant fitness change suspected (better or worse)
- Want to see long-term trend verification
- Previous analysis feels "stale" or outdated
- Want fresh plots/visualizations

**Bottom line:** Weekly updates are highly effective for ongoing plan adjustments within an established framework. They don't replace deep analysis, they complement it.

---

## Summary

**Full Analysis = Deep understanding + strategic planning**  
Use for: Starting, checking, course-correcting

**Weekly Update = Tactical adjustments + execution guidance**  
Use for: Ongoing refinement, week-to-week adaptation

**Together = Professional AI coaching at sustainable cost**  
The magic is in combining both modes appropriately throughout your training journey.
