# Weekly Update: Example Usage

This document shows a real example of using the efficient weekly workflow for Jon Baker's sub-2:00 half marathon goal.

## Initial Full Analysis (November 23, 2025)

**Config used:**
```yaml
athlete:
  name: "Jon Baker"
  email: "jonbaker85@gmail.com"

context:
  analysis: |
    Completed half marathon on November 23, 2025 with disappointing 2:11 finish.
    Struggled after 2km, calves shot by finish. Race compromised by:
    - Food poisoning 12 days before race (Nov 11)
    - Funeral disruption (6 days off training, Oct 26-31)
    - Elevated RHR on race day (58 vs 51-52 baseline)

  planning: |
    ## Goal Race
    Half Marathon on May 4, 2026 - Target: Sub-2:00 (5:41/km average pace)
    
    ## Training Philosophy
    Felt best in the lead up to April half marathon. Need structured rebuild.

extraction:
  activities_days: 365
  metrics_days: 365
  context_recent_days: 60
  context_trends_days: 365
  ai_mode: "cost_effective"

competitions:
  - name: "Sydney Hoka Half Marathon"
    date: "2026-05-04"
    race_type: "Half Marathon"
    priority: "A"
    target_time: "01:59:30"
```

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml
```

**Cost:** $2.80, 85,000 tokens  
**Time:** 4 minutes  
**Output:** Full analysis + season plan + Week 1-2 detailed plan

---

## Week 1 Update (December 2, 2025)

**Progress after Week 1:**
- Completed all 3 easy recovery runs as prescribed
- Calves recovered to 90%, no pain
- RHR dropped from 58 to 53 (back to baseline)
- Felt strong on runs, HR staying in zone 1-2
- Ready to progress volume

**Config update:**
```yaml
# Add this section to your existing config
weekly_progress:
  notes: |
    Week 1 (Nov 25-Dec 1): Recovery week completed successfully
    
    Completed workouts:
    - Monday: Easy 5km @ 6:40/km, HR 144 avg (felt good, calves okay)
    - Wednesday: Easy 6km @ 6:35/km, HR 146 avg (stronger, no calf issues)
    - Saturday: Easy 7km @ 6:30/km, HR 148 avg (felt excellent)
    
    Recovery status:
    - Calves: 90% recovered, minor tightness but no pain during runs
    - RHR trend: 58→55→53 (back to baseline of 51-53)
    - Sleep: 7-8 hours/night, good quality
    - Energy: High, feeling recovered and motivated
    
    Readiness:
    - Ready to progress volume by 10-15%
    - Can handle introducing tempo work if prescribed
    - Work schedule allows flexible training next week
```

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml --update-plan
```

**Cost:** $0.25, 8,000 tokens (91% cheaper!)  
**Time:** 45 seconds  
**Output:** Updated planning.html with Week 2-3 adjusted for progress

**What changed in the plan:**
- Week 2 volume increased from 18km → 22km (safe progression)
- Added optional light tempo if feeling good
- Maintained focus on aerobic base but allows advancement
- Adjusted long run from 8km → 10km based on readiness

---

## Week 2 Update (December 9, 2025)

**Progress after Week 2:**
- Completed 3/3 runs but struggled more than expected
- Introduced tempo run (5km w/ 3km @ threshold) - HR spiked to 175
- RHR elevated to 56 by end of week
- Mild calf tightness returned on tempo day

**Config update:**
```yaml
weekly_progress:
  notes: |
    Week 2 (Dec 2-8): Volume increase handled, but tempo too aggressive
    
    Completed workouts:
    - Monday: Easy 7km @ 6:25/km, HR 147 (good)
    - Wednesday: Tempo attempt - 2km easy, 3km @ 5:30/km (too fast), 
                 HR spiked to 175, calves tightened up, cut session short
    - Saturday: Easy 10km @ 6:40/km, HR 150 (sluggish, heavy legs)
    
    Recovery status:
    - Calves: Mild tightness returned after tempo (5/10 on pain scale)
    - RHR trend: 53→54→56 (elevated from baseline)
    - Sleep: 6-7 hours (work stress this week)
    - Energy: Moderate, felt fatigue accumulating
    
    Lessons learned:
    - Tempo effort was too intense - need to ease into threshold work
    - Volume increase + intensity = too much too soon
    - Life stress (work deadline) affected recovery
    
    Adjustments needed:
    - Pull back on intensity this week
    - Keep volume similar but focus on easy aerobic runs
    - Let RHR return to baseline before pushing again
    - Monitor calf closely, may need extra rest day
```

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml --update-plan
```

**Cost:** $0.30, 9,500 tokens  
**Time:** 50 seconds  
**Output:** Week 3-4 plan adjusted with recovery focus

**What changed in the plan:**
- Week 3 pulled back to easier aerobic focus (no tempo)
- Volume held at 20km (not progressed)
- Added explicit calf-strengthening routine
- Emphasized strict HR discipline at 144-150 bpm
- Optional rest day mid-week if RHR stays elevated

---

## Week 6 Update (December 30, 2025)

**Progress after Weeks 3-6:**
- Back on track after recovery adjustment
- RHR stable at 51-52 for 3 weeks
- Built up to 32km/week comfortably
- Introduced controlled tempo work successfully
- No calf issues

**Config update:**
```yaml
weekly_progress:
  notes: |
    Weeks 3-6 summary: Excellent rebuild phase
    
    Week 3-4: Recovery focus paid off
    - RHR returned to 51-52 baseline
    - Aerobic runs felt smooth, HR under control
    - Calves fully recovered
    
    Week 5-6: Successful progression
    - Volume: 25km → 28km → 32km (gradual increase working well)
    - Reintroduced tempo: 8km run with 4km @ threshold pace (5:45/km)
      HR controlled at 168-170 avg, felt sustainable
    - Long run: Extended to 14km @ 6:20/km, HR 150 avg (excellent)
    
    Current status:
    - Feeling strongest since April
    - No injury concerns
    - RHR consistently 51-52
    - Sleep improving (7-8hrs regularly)
    - Work stress reduced (holidays)
    
    Ready for:
    - Continue building volume toward 40km/week
    - Regular tempo work weekly
    - Can handle more structured threshold sessions
    - Excited for next phase of training
```

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml --update-plan
```

**Cost:** $0.35, 11,000 tokens  
**Time:** 55 seconds  
**Output:** Week 7-8 plan with progressive build

**What changed in the plan:**
- Week 7-8 increases volume to 35-38km
- Adds structured tempo intervals (6x1km @ 5:35/km with 90s recovery)
- Long run extended to 16km with progression finish
- Introduces optional 4th easy run day for volume
- Maintains aerobic foundation while building specific endurance

---

## Monthly Deep-Dive (January 6, 2026)

After 6 weeks of training, run full analysis to:
- Verify fitness trends (VO2 max progression)
- Check chronic load building appropriately
- Generate updated plots
- Reassess season plan

**Command:**
```bash
pixi run coach-cli --config my_training_config.yaml
```

**Cost:** $3.10, 92,000 tokens  
**Time:** 4.5 minutes

**Key findings:**
- VO2 max improved from 44.0 → 45.0 (good progress!)
- Chronic load rebuilding steadily (298 → 385)
- ACWR staying in safe zone (0.9-1.2)
- On track for sub-2:00 goal if progression continues

---

## Cost Summary: 6 Weeks of Training

**Inefficient approach (full analysis every week):**
- 6 full runs × $3.00 = **$18.00**

**Efficient approach (full + weekly updates):**
- 1 initial full analysis: $2.80
- 5 weekly updates × $0.28 avg = $1.40
- 1 monthly deep-dive: $3.10
- **Total: $7.30** (59% savings)

**For full 23-week block:**
- Inefficient: ~$69
- Efficient: ~$20 (71% savings)

---

## Key Takeaways

1. **Progress notes quality matters:** Specific, detailed notes = better adaptations
2. **Weekly updates catch issues early:** Week 2 tempo overreach was corrected before causing injury
3. **Monthly deep-dives verify trajectory:** Confirm fitness is building as expected
4. **Cost-effective ongoing coaching:** $0.25-0.35 per week for personalized plan updates
5. **System learns from your feedback:** Plans become more aligned with your responses over time
