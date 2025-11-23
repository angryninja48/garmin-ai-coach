"""Quick test of 6-month context configuration."""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from dataclasses import asdict
from services.garmin import ExtractionConfig, TriathlonCoachDataExtractor, prepare_agent_context

email = os.getenv('GARMIN_EMAIL')
password = os.getenv('GARMIN_PASSWORD')

print('🔐 Testing 6-month context preparation...')
extractor = TriathlonCoachDataExtractor(email, password)

config = ExtractionConfig(activities_range=180, metrics_range=180, include_detailed_activities=True, include_metrics=True)
garmin_data = extractor.extract_data(config)
print(f'✅ Extracted {len(garmin_data.recent_activities)} activities from 180 days')

garmin_data_dict = asdict(garmin_data)
prepared = prepare_agent_context(garmin_data_dict, recent_window_days=14, trends_window_days=180)

weeks = len(prepared['weekly_trends'])
recent = len(prepared['recent_activities'])
print(f'✅ Prepared context: {recent} recent activities + {weeks} weekly trends')
print(f'📊 Historical span: ~{weeks/4.33:.1f} months of trends')
print('✅ Configuration working perfectly!')
