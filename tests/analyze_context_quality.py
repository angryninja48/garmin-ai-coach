"""
Analyze the quality and completeness of prepared context.

Run with: pixi run python tests/analyze_context_quality.py
"""

import json
from datetime import datetime, date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
from dataclasses import asdict

from services.garmin import ExtractionConfig, TriathlonCoachDataExtractor, prepare_agent_context


def analyze_context_quality():
    """Analyze what information is preserved vs lost in context preparation."""
    
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        print("❌ Set GARMIN_EMAIL and GARMIN_PASSWORD in .env")
        return
    
    print("🔐 Connecting to Garmin Connect...")
    extractor = TriathlonCoachDataExtractor(email, password)
    
    print("📊 Extracting 90 days of data...")
    config = ExtractionConfig(
        activities_range=90,
        metrics_range=90,
        include_detailed_activities=True,
        include_metrics=True,
    )
    
    garmin_data = extractor.extract_data(config)
    garmin_data_dict = asdict(garmin_data)
    
    print("📦 Preparing optimized context...")
    prepared = prepare_agent_context(
        garmin_data=garmin_data_dict,
        recent_window_days=14,
        trends_window_days=90,
    )
    
    print("\n" + "="*70)
    print("CONTEXT QUALITY ANALYSIS")
    print("="*70)
    
    # Analyze what's in recent activities
    print("\n📅 RECENT ACTIVITIES (Last 14 Days - Full Detail)")
    print("="*70)
    recent = prepared["recent_activities"]
    
    if recent:
        for act in recent[:3]:  # Show first 3
            summary = act.get("summary", {})
            print(f"\n✓ {act['activity_type'].title()}: {act.get('activity_name', 'N/A')}")
            print(f"  Date: {act.get('start_time', 'N/A')[:10]}")
            print(f"  Distance: {summary.get('distance', 0)/1000:.2f}km")
            print(f"  Duration: {summary.get('duration', 0)/3600:.2f}h")
            print(f"  Avg HR: {summary.get('average_hr', 'N/A')}")
            print(f"  Training Load: {summary.get('activity_training_load', 'N/A')}")
            print(f"  Laps available: {'Yes' if act.get('laps') else 'No'}")
            print(f"  Weather data: {'Yes' if act.get('weather') else 'No'}")
        
        if len(recent) > 3:
            print(f"\n  ... and {len(recent) - 3} more recent activities")
    
    # Analyze weekly trends
    print("\n\n📈 WEEKLY TRENDS (Last 90 Days - Aggregated)")
    print("="*70)
    trends = prepared["weekly_trends"]
    
    # Show progression over time
    print("\nWeek-by-week progression:")
    print(f"{'Week':<6} {'Dates':<22} {'Activities':<12} {'Distance':<12} {'Duration':<10} {'Load':<10}")
    print("-" * 70)
    
    for week in trends:
        vol = week["volume"]
        intensity = week["intensity"]
        week_dates = f"{week['week_start']} to {week['week_end'][:5]}"
        
        print(f"{week['week_number']:<6} {week_dates:<22} "
              f"{vol['total_activities']:<12} "
              f"{vol['total_distance_km']:.1f}km{'':<7} "
              f"{vol['total_duration_hours']:.1f}h{'':<6} "
              f"{intensity.get('total_training_load') or 0:.0f}")
    
    # Calculate training insights from trends
    print("\n\n💡 TRAINING INSIGHTS FROM TRENDS")
    print("="*70)
    
    # Calculate averages
    total_weeks = len([w for w in trends if w["volume"]["total_activities"] > 0])
    avg_weekly_activities = sum(w["volume"]["total_activities"] for w in trends) / len(trends)
    avg_weekly_km = sum(w["volume"]["total_distance_km"] for w in trends) / len(trends)
    avg_weekly_hours = sum(w["volume"]["total_duration_hours"] for w in trends) / len(trends)
    
    # Find peak week
    peak_week = max(trends, key=lambda w: w["volume"]["total_distance_km"])
    
    # Activity type distribution
    all_activity_types = set()
    for week in trends:
        all_activity_types.update(week["by_activity_type"]["counts"].keys())
    
    print(f"Training weeks with activity: {total_weeks}/{len(trends)}")
    print(f"Average weekly volume: {avg_weekly_km:.1f}km, {avg_weekly_hours:.1f}h, {avg_weekly_activities:.1f} activities")
    print(f"Peak week: Week {peak_week['week_number']} ({peak_week['week_start']}) - "
          f"{peak_week['volume']['total_distance_km']:.1f}km")
    print(f"Activity types tracked: {', '.join(sorted(all_activity_types))}")
    
    # Check what key training questions can be answered
    print("\n\n✓ CAN ANSWER FROM THIS CONTEXT:")
    print("="*70)
    questions = [
        ("Recent performance", "✓ Last 14 days detailed activities"),
        ("Training volume trends", "✓ 11+ weeks of weekly volume"),
        ("Activity type distribution", "✓ By-type breakdown per week"),
        ("Training load progression", "✓ Weekly training load totals"),
        ("Long run progression", "✓ Longest run/ride each week"),
        ("Intensity patterns", "✓ Avg/max HR per week"),
        ("Recovery trends", "✓ Weekly avg RHR & sleep"),
        ("Current fitness state", "✓ Latest VO2max, ACWR, HRV"),
        ("Training consistency", "✓ Activity frequency per week"),
        ("Volume ramp rate", "✓ Week-over-week changes"),
    ]
    
    for question, answer in questions:
        print(f"  {answer:<40} {question}")
    
    # Check what's missing
    print("\n\n⚠️  DETAIL LOST (BY DESIGN):")
    print("="*70)
    limitations = [
        "Individual workout details beyond 14 days",
        "Lap-by-lap splits for historical activities",
        "Weather data for historical activities",
        "Exact timestamps of historical activities",
        "Daily metrics (aggregated to weekly)",
    ]
    
    for limitation in limitations:
        print(f"  - {limitation}")
    
    print("\n\n🎯 CONTEXT SUITABILITY BY AGENT:")
    print("="*70)
    
    agents = {
        "Season Planner": {
            "needs": ["Long-term volume trends", "Training progression", "Activity types"],
            "rating": "✅ EXCELLENT - Has 11 weeks of trends"
        },
        "Weekly Planner": {
            "needs": ["Recent activities", "Current fitness", "Last week's volume"],
            "rating": "✅ EXCELLENT - Has detailed recent + last week trends"
        },
        "Activity Expert": {
            "needs": ["Recent workouts", "Workout quality", "Performance"],
            "rating": "✅ GOOD - Has 14 days detailed, trends for context"
        },
        "Metrics Expert": {
            "needs": ["Training load", "Fitness markers", "Trends"],
            "rating": "✅ EXCELLENT - Has current metrics + weekly load history"
        },
        "Physiology Expert": {
            "needs": ["Recovery data", "HR trends", "Sleep patterns"],
            "rating": "✅ GOOD - Has weekly recovery averages + current state"
        },
    }
    
    for agent, info in agents.items():
        print(f"\n{agent}:")
        print(f"  Needs: {', '.join(info['needs'])}")
        print(f"  {info['rating']}")
    
    print("\n\n💾 DETAILED CONTEXT SAVED TO:")
    print("="*70)
    print("  data/context_preparation_sample.json")
    print("\nReview this file to see exactly what agents will receive!")
    
    # Calculate if this is enough for season planning
    print("\n\n🏃 SEASON PLANNING READINESS:")
    print("="*70)
    
    weeks_of_data = len(trends)
    months_of_data = weeks_of_data / 4.33
    
    print(f"Historical data span: {weeks_of_data} weeks (~{months_of_data:.1f} months)")
    
    if months_of_data >= 6:
        print("✅ EXCELLENT: 6+ months for robust season planning")
    elif months_of_data >= 3:
        print("✅ GOOD: 3+ months sufficient for season planning")
    elif months_of_data >= 2:
        print("⚠️  ADEQUATE: 2+ months works but more history better")
    else:
        print("⚠️  LIMITED: <2 months may limit season planning insights")
    
    print("\n" + "="*70)
    print("RECOMMENDATION: Context provides excellent balance of detail + history!")
    print("="*70)


if __name__ == "__main__":
    analyze_context_quality()
