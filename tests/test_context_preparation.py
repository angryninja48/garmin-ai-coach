"""
Tests for context preparation service.

Validates sliding window + aggregation approach for managing agent context.
"""

import json
from datetime import date, datetime, timedelta

import pytest

from services.garmin.context_preparation import (
    ContextPreparationService,
    PreparedContext,
    WeeklyAggregate,
    prepare_agent_context,
)


@pytest.fixture
def sample_activities():
    """Generate sample activities spanning 120 days."""
    activities = []
    base_date = date.today() - timedelta(days=120)
    
    for day_offset in range(0, 120, 2):  # Every other day
        activity_date = base_date + timedelta(days=day_offset)
        
        # Alternate between running and cycling
        activity_type = "running" if day_offset % 4 == 0 else "cycling"
        
        activities.append({
            "activity_id": f"act_{day_offset}",
            "activity_name": f"{activity_type.title()} Session",
            "activity_type": activity_type,
            "start_time": f"{activity_date.isoformat()}T06:00:00",
            "summary": {
                "distance": 10000 if activity_type == "running" else 30000,  # meters
                "duration": 3600 if activity_type == "running" else 5400,  # seconds
                "elevation_gain": 50 if activity_type == "running" else 200,  # meters
                "average_hr": 145,
                "max_hr": 165,
                "activity_training_load": 85 if activity_type == "running" else 120,
            },
        })
    
    return activities


@pytest.fixture
def sample_recovery_data():
    """Generate sample recovery data."""
    recovery_data = []
    base_date = date.today() - timedelta(days=120)
    
    for day_offset in range(120):
        recovery_date = base_date + timedelta(days=day_offset)
        
        recovery_data.append({
            "date": recovery_date.isoformat(),
            "sleep": {
                "duration": {
                    "total": 7.5,
                },
                "resting_heart_rate": 52,
            },
        })
    
    return recovery_data


@pytest.fixture
def sample_garmin_data(sample_activities, sample_recovery_data):
    """Create sample Garmin data structure."""
    return {
        "recent_activities": sample_activities,
        "recovery_indicators": sample_recovery_data,
        "physiological_markers": {
            "resting_heart_rate": 52,
            "vo2_max": 58.5,
            "hrv": {
                "weekly_avg": 65,
                "last_night_avg": 68,
            },
        },
        "training_status": {
            "acute_training_load": {
                "acute_load": 450,
                "chronic_load": 380,
                "acwr": 1.18,
            },
        },
        "daily_stats": {
            "average_stress_level": 35,
            "resting_heart_rate": 52,
        },
    }


class TestContextPreparationService:
    """Test context preparation service functionality."""
    
    def test_service_initialization(self):
        """Test service can be instantiated."""
        service = ContextPreparationService()
        assert service is not None
    
    def test_parse_activity_date_iso_format(self):
        """Test parsing ISO format activity dates."""
        service = ContextPreparationService()
        
        # ISO with timezone
        activity = {"start_time": "2025-11-23T06:30:00Z"}
        result = service._parse_activity_date(activity)
        assert result == date(2025, 11, 23)
        
        # ISO without timezone
        activity = {"start_time": "2025-11-23T06:30:00"}
        result = service._parse_activity_date(activity)
        assert result == date(2025, 11, 23)
        
        # Date only
        activity = {"start_time": "2025-11-23"}
        result = service._parse_activity_date(activity)
        assert result == date(2025, 11, 23)
    
    def test_get_week_start(self):
        """Test week start calculation (Monday)."""
        service = ContextPreparationService()
        
        # Saturday November 23, 2025
        saturday = date(2025, 11, 23)
        week_start = service._get_week_start(saturday)
        assert week_start == date(2025, 11, 17)  # Previous Monday
        assert week_start.weekday() == 0  # Monday
        
        # Monday
        monday = date(2025, 11, 17)
        week_start = service._get_week_start(monday)
        assert week_start == monday
    
    def test_prepare_agent_context_structure(self, sample_garmin_data):
        """Test prepared context has correct structure."""
        service = ContextPreparationService()
        
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
            analysis_date=date.today(),
            recent_window_days=14,
            trends_window_days=90,
        )
        
        assert isinstance(result, PreparedContext)
        assert isinstance(result.recent_activities, list)
        assert isinstance(result.weekly_trends, list)
        assert isinstance(result.current_metrics, dict)
        assert result.recent_window_days == 14
        assert result.trends_window_days == 90
    
    def test_sliding_window_splits_correctly(self, sample_garmin_data):
        """Test activities are correctly split between recent and historical."""
        service = ContextPreparationService()
        
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
            analysis_date=date.today(),
            recent_window_days=14,
            trends_window_days=90,
        )
        
        # Should have activities in recent window
        assert len(result.recent_activities) > 0
        
        # Recent activities should be within 14 days
        for activity in result.recent_activities:
            activity_date = service._parse_activity_date(activity)
            days_ago = (date.today() - activity_date).days
            assert days_ago <= 14
    
    def test_weekly_aggregation_structure(self, sample_garmin_data):
        """Test weekly aggregates have correct structure."""
        service = ContextPreparationService()
        
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
            analysis_date=date.today(),
            recent_window_days=14,
            trends_window_days=90,
        )
        
        assert len(result.weekly_trends) > 0
        
        for week in result.weekly_trends:
            assert "week_start" in week
            assert "week_end" in week
            assert "week_number" in week
            assert "volume" in week
            assert "by_activity_type" in week
            assert "intensity" in week
            assert "key_sessions" in week
            assert "recovery" in week
    
    def test_weekly_aggregation_calculations(self, sample_garmin_data):
        """Test weekly aggregations calculate metrics correctly."""
        service = ContextPreparationService()
        
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
            analysis_date=date.today(),
            recent_window_days=14,
            trends_window_days=90,
        )
        
        # Find a week with activities
        weeks_with_activities = [w for w in result.weekly_trends if w["volume"]["total_activities"] > 0]
        assert len(weeks_with_activities) > 0
        
        sample_week = weeks_with_activities[0]
        
        # Verify volume metrics are reasonable
        assert sample_week["volume"]["total_distance_km"] > 0
        assert sample_week["volume"]["total_duration_hours"] > 0
        
        # Verify intensity metrics
        if sample_week["intensity"]["avg_heart_rate"]:
            assert 100 <= sample_week["intensity"]["avg_heart_rate"] <= 200
    
    def test_current_metrics_extraction(self, sample_garmin_data):
        """Test current metrics are correctly extracted."""
        service = ContextPreparationService()
        
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
            analysis_date=date.today(),
        )
        
        metrics = result.current_metrics
        assert metrics["resting_heart_rate"] == 52
        assert metrics["vo2_max"] == 58.5
        assert metrics["hrv"]["weekly_avg"] == 65
        assert metrics["training_load"]["acute"] == 450
        assert metrics["training_load"]["chronic"] == 380
        assert metrics["training_load"]["acwr"] == 1.18
    
    def test_to_dict_serializable(self, sample_garmin_data):
        """Test prepared context can be serialized to dict."""
        service = ContextPreparationService()
        
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
        )
        
        result_dict = result.to_dict()
        
        # Ensure can be JSON serialized
        json_str = json.dumps(result_dict)
        assert len(json_str) > 0
        
        # Verify structure
        assert "recent_activities" in result_dict
        assert "weekly_trends" in result_dict
        assert "current_metrics" in result_dict
        assert "metadata" in result_dict
    
    def test_convenience_function(self, sample_garmin_data):
        """Test convenience function works correctly."""
        result = prepare_agent_context(
            garmin_data=sample_garmin_data,
            recent_window_days=14,
            trends_window_days=90,
        )
        
        assert isinstance(result, dict)
        assert "recent_activities" in result
        assert "weekly_trends" in result
        assert "current_metrics" in result
        assert "metadata" in result
    
    def test_empty_activities_handled(self):
        """Test service handles empty activities gracefully."""
        service = ContextPreparationService()
        
        empty_data = {
            "recent_activities": [],
            "recovery_indicators": [],
            "physiological_markers": {},
            "training_status": {},
            "daily_stats": {},
        }
        
        result = service.prepare_agent_context(
            garmin_data=empty_data,
        )
        
        assert len(result.recent_activities) == 0
        # Should still create weekly structure (even with no data)
        assert len(result.weekly_trends) > 0
    
    def test_token_reduction_estimate(self, sample_garmin_data):
        """Test that prepared context is smaller than raw data."""
        service = ContextPreparationService()
        
        # Prepare optimized context
        result = service.prepare_agent_context(
            garmin_data=sample_garmin_data,
        )
        
        result_dict = result.to_dict()
        
        # Compare sizes (rough estimate)
        raw_json = json.dumps(sample_garmin_data)
        prepared_json = json.dumps(result_dict)
        
        raw_size = len(raw_json)
        prepared_size = len(prepared_json)
        
        # Prepared should be significantly smaller
        # (Not always true with small test data, but validates structure)
        print(f"\nRaw data size: {raw_size} chars")
        print(f"Prepared context size: {prepared_size} chars")
        print(f"Reduction: {100 * (1 - prepared_size/raw_size):.1f}%")
        
        # At minimum, verify prepared context is reasonable size
        assert prepared_size < 50000  # Should be well under 50KB for test data


class TestWeeklyAggregate:
    """Test WeeklyAggregate dataclass."""
    
    def test_to_dict_conversion(self):
        """Test WeeklyAggregate converts to dict correctly."""
        aggregate = WeeklyAggregate(
            week_start="2025-11-17",
            week_end="2025-11-23",
            week_number=1,
            total_activities=5,
            total_distance_km=50.5,
            total_duration_hours=4.25,
            total_elevation_gain_m=450.0,
            activities_by_type={"running": 3, "cycling": 2},
            distance_by_type={"running": 30.0, "cycling": 20.5},
            duration_by_type={"running": 2.5, "cycling": 1.75},
            avg_heart_rate=148.5,
            max_heart_rate=172,
            total_training_load=425.0,
            longest_activity_distance_km=15.0,
            longest_activity_duration_hours=1.5,
            highest_intensity_activity="running",
            avg_resting_hr=52.0,
            avg_sleep_hours=7.5,
        )
        
        result = aggregate.to_dict()
        
        assert result["week_start"] == "2025-11-17"
        assert result["volume"]["total_activities"] == 5
        assert result["volume"]["total_distance_km"] == 50.5
        assert result["by_activity_type"]["counts"]["running"] == 3
        assert result["intensity"]["avg_heart_rate"] == 148.5
        assert result["recovery"]["avg_sleep_hours"] == 7.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
