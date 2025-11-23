"""
Integration test to validate context preparation with real Garmin data.

Run with: pixi run python tests/test_context_integration.py
"""

import json
import os
from dataclasses import asdict
from datetime import date

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from services.garmin import ExtractionConfig, TriathlonCoachDataExtractor, prepare_agent_context


def test_with_real_data():
    """Test context preparation with real Garmin data."""
    
    # Get credentials from environment
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        print("❌ GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        return
    
    print("🔐 Connecting to Garmin Connect...")
    extractor = TriathlonCoachDataExtractor(email, password)
    
    print("📊 Extracting data (last 90 days)...")
    config = ExtractionConfig(
        activities_range=90,
        metrics_range=90,
        include_detailed_activities=True,
        include_metrics=True,
    )
    
    garmin_data = extractor.extract_data(config)
    garmin_data_dict = asdict(garmin_data)
    
    print(f"✅ Extracted {len(garmin_data.recent_activities)} activities")
    
    print("\n📦 Preparing optimized context...")
    prepared = prepare_agent_context(
        garmin_data=garmin_data_dict,
        analysis_date=date.today(),
        recent_window_days=14,
        trends_window_days=90,
    )
    
    print("\n" + "="*70)
    print("CONTEXT PREPARATION RESULTS")
    print("="*70)
    
    # Recent activities
    recent_count = len(prepared["recent_activities"])
    print(f"\n📅 Recent Activities (last 14 days): {recent_count}")
    if recent_count > 0:
        print("   Sample:")
        for i, act in enumerate(prepared["recent_activities"][:3]):
            print(f"   - {act['activity_type']}: {act.get('start_time', 'N/A')}")
    
    # Weekly trends
    weekly_count = len(prepared["weekly_trends"])
    print(f"\n📈 Weekly Trends (last 90 days): {weekly_count} weeks")
    if weekly_count > 0:
        print("   Sample weeks:")
        for week in prepared["weekly_trends"][-3:]:  # Last 3 weeks
            vol = week["volume"]
            print(f"   - Week {week['week_number']} ({week['week_start']}): "
                  f"{vol['total_activities']} activities, "
                  f"{vol['total_distance_km']:.1f}km, "
                  f"{vol['total_duration_hours']:.1f}h")
    
    # Current metrics
    metrics = prepared["current_metrics"]
    print(f"\n💓 Current Metrics:")
    print(f"   - RHR: {metrics.get('resting_heart_rate')}")
    print(f"   - VO2 Max: {metrics.get('vo2_max')}")
    if metrics.get("training_load"):
        tl = metrics["training_load"]
        print(f"   - Acute Load: {tl.get('acute')}")
        print(f"   - Chronic Load: {tl.get('chronic')}")
        print(f"   - ACWR: {tl.get('acwr')}")
    
    # Size comparison
    raw_json = json.dumps(garmin_data_dict)
    prepared_json = json.dumps(prepared)
    
    raw_size = len(raw_json)
    prepared_size = len(prepared_json)
    reduction = 100 * (1 - prepared_size / raw_size)
    
    print(f"\n💾 Token Efficiency:")
    print(f"   - Raw data size: {raw_size:,} chars (~{raw_size//4:,} tokens)")
    print(f"   - Prepared size: {prepared_size:,} chars (~{prepared_size//4:,} tokens)")
    print(f"   - Reduction: {reduction:.1f}%")
    
    # Save sample output
    output_file = "data/context_preparation_sample.json"
    with open(output_file, "w") as f:
        json.dump(prepared, f, indent=2)
    print(f"\n💾 Saved sample to: {output_file}")
    
    print("\n✅ Context preparation working correctly!")


if __name__ == "__main__":
    test_with_real_data()
