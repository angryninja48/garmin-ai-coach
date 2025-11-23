"""
Quick script to estimate token usage of different context strategies.

Run with: pixi run python tests/estimate_token_usage.py
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


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for JSON."""
    return len(text) // 4


def compare_strategies():
    """Compare token usage across different context strategies."""
    
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    
    if not email or not password:
        print("❌ Set GARMIN_EMAIL and GARMIN_PASSWORD in .env")
        return
    
    print("🔐 Connecting to Garmin Connect...")
    extractor = TriathlonCoachDataExtractor(email, password)
    
    strategies = [
        ("7 days raw", 7, None, None),
        ("14 days raw", 14, None, None),
        ("30 days raw", 30, None, None),
        ("90 days raw", 90, None, None),
        ("14d + 90d trends", 90, 14, 90),
    ]
    
    print("\n" + "="*70)
    print("TOKEN USAGE COMPARISON")
    print("="*70)
    
    for strategy_name, extract_days, recent_window, trends_window in strategies:
        config = ExtractionConfig(
            activities_range=extract_days,
            metrics_range=extract_days,
            include_detailed_activities=True,
            include_metrics=True,
        )
        
        garmin_data = extractor.extract_data(config)
        garmin_data_dict = asdict(garmin_data)
        
        if recent_window and trends_window:
            # Use prepared context
            context = prepare_agent_context(
                garmin_data=garmin_data_dict,
                recent_window_days=recent_window,
                trends_window_days=trends_window,
            )
            context_json = json.dumps(context)
        else:
            # Use raw data
            context_json = json.dumps(garmin_data_dict)
        
        tokens = estimate_tokens(context_json)
        
        print(f"\n📊 {strategy_name}:")
        print(f"   Activities: {len(garmin_data.recent_activities)}")
        print(f"   Size: {len(context_json):,} chars")
        print(f"   Tokens: ~{tokens:,}")
        print(f"   Cost (Claude): ~${tokens * 0.003 / 1000:.4f}")
    
    print("\n" + "="*70)
    print("💡 Recommendation: 14d + 90d trends strategy provides best balance")
    print("="*70)


if __name__ == "__main__":
    compare_strategies()
