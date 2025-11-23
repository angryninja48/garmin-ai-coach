"""
Context preparation service for AI agents.

Implements a hybrid sliding window + aggregation approach to manage token budgets
while providing agents with relevant historical context.

Strategy:
- Last 14 days: Full detailed activity data
- Last 90 days: Weekly aggregated trends (volume, intensity, key metrics)
- Future: Semantic retrieval for similar training periods
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WeeklyAggregate:
    """Aggregated training metrics for a single week."""
    
    week_start: str
    week_end: str
    week_number: int
    
    # Volume metrics
    total_activities: int
    total_distance_km: float
    total_duration_hours: float
    total_elevation_gain_m: float
    
    # Activity type breakdown
    activities_by_type: dict[str, int]
    distance_by_type: dict[str, float]
    duration_by_type: dict[str, float]
    
    # Intensity indicators
    avg_heart_rate: float | None
    max_heart_rate: float | None
    total_training_load: float | None
    
    # Key sessions
    longest_activity_distance_km: float | None
    longest_activity_duration_hours: float | None
    highest_intensity_activity: str | None
    
    # Recovery indicators
    avg_resting_hr: float | None
    avg_sleep_hours: float | None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "week_start": self.week_start,
            "week_end": self.week_end,
            "week_number": self.week_number,
            "volume": {
                "total_activities": self.total_activities,
                "total_distance_km": round(self.total_distance_km, 2),
                "total_duration_hours": round(self.total_duration_hours, 2),
                "total_elevation_gain_m": round(self.total_elevation_gain_m, 2),
            },
            "by_activity_type": {
                "counts": self.activities_by_type,
                "distance_km": {k: round(v, 2) for k, v in self.distance_by_type.items()},
                "duration_hours": {k: round(v, 2) for k, v in self.duration_by_type.items()},
            },
            "intensity": {
                "avg_heart_rate": round(self.avg_heart_rate, 1) if self.avg_heart_rate else None,
                "max_heart_rate": self.max_heart_rate,
                "total_training_load": round(self.total_training_load, 1) if self.total_training_load else None,
            },
            "key_sessions": {
                "longest_distance_km": round(self.longest_activity_distance_km, 2) if self.longest_activity_distance_km else None,
                "longest_duration_hours": round(self.longest_activity_duration_hours, 2) if self.longest_activity_duration_hours else None,
                "highest_intensity_type": self.highest_intensity_activity,
            },
            "recovery": {
                "avg_resting_hr": round(self.avg_resting_hr, 1) if self.avg_resting_hr else None,
                "avg_sleep_hours": round(self.avg_sleep_hours, 2) if self.avg_sleep_hours else None,
            },
        }


@dataclass
class PreparedContext:
    """Prepared context for AI agents with sliding window + aggregation."""
    
    recent_activities: list[dict[str, Any]]  # Last 14 days detailed
    weekly_trends: list[dict[str, Any]]  # 90-day aggregated by week
    current_metrics: dict[str, Any]  # Latest physiological markers
    
    # Metadata
    preparation_date: str
    recent_window_days: int
    trends_window_days: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for state injection."""
        return {
            "recent_activities": self.recent_activities,
            "weekly_trends": self.weekly_trends,
            "current_metrics": self.current_metrics,
            "metadata": {
                "preparation_date": self.preparation_date,
                "recent_window_days": self.recent_window_days,
                "trends_window_days": self.trends_window_days,
            },
        }


class ContextPreparationService:
    """Service for preparing optimized context for AI agents."""
    
    @staticmethod
    def _get_week_start(activity_date: date) -> date:
        """Get Monday of the week for a given date."""
        return activity_date - timedelta(days=activity_date.weekday())
    
    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float."""
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to int."""
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _parse_activity_date(activity: dict[str, Any]) -> date | None:
        """Extract and parse activity start date."""
        try:
            start_time = activity.get("start_time", "")
            if not start_time:
                return None
            
            # Handle ISO format with timezone
            if "T" in start_time:
                dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                return dt.date()
            
            # Handle date-only format
            return datetime.strptime(start_time.split("T")[0], "%Y-%m-%d").date()
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse activity date from {start_time}: {e}")
            return None
    
    def prepare_agent_context(
        self,
        garmin_data: dict[str, Any],
        analysis_date: date | None = None,
        recent_window_days: int = 14,
        trends_window_days: int = 90,
    ) -> PreparedContext:
        """
        Prepare optimized context for AI agents.
        
        Args:
            garmin_data: Full Garmin data dictionary
            analysis_date: Date of analysis (defaults to today)
            recent_window_days: Days of detailed recent data (default 14)
            trends_window_days: Days of aggregated trends (default 90)
        
        Returns:
            PreparedContext with recent details + weekly aggregates
        """
        if analysis_date is None:
            analysis_date = date.today()
        
        logger.info(
            f"Preparing context for {analysis_date}: "
            f"{recent_window_days}d recent + {trends_window_days}d trends"
        )
        
        # Extract activities
        activities = garmin_data.get("recent_activities", [])
        
        # Split into recent (detailed) and historical (for aggregation)
        recent_cutoff = analysis_date - timedelta(days=recent_window_days)
        trends_cutoff = analysis_date - timedelta(days=trends_window_days)
        
        recent_activities: list[dict[str, Any]] = []
        historical_activities: list[dict[str, Any]] = []
        
        for activity in activities:
            activity_date = self._parse_activity_date(activity)
            if activity_date is None:
                continue
            
            if activity_date > recent_cutoff:
                recent_activities.append(activity)
            elif activity_date > trends_cutoff:
                historical_activities.append(activity)
        
        logger.info(
            f"Split activities: {len(recent_activities)} recent, "
            f"{len(historical_activities)} historical for aggregation"
        )
        
        # Aggregate historical activities by week
        weekly_trends = self._aggregate_by_week(
            historical_activities,
            garmin_data,
            trends_cutoff,
            recent_cutoff,
        )
        
        # Extract current metrics
        current_metrics = self._extract_current_metrics(garmin_data)
        
        return PreparedContext(
            recent_activities=recent_activities,
            weekly_trends=weekly_trends,
            current_metrics=current_metrics,
            preparation_date=analysis_date.isoformat(),
            recent_window_days=recent_window_days,
            trends_window_days=trends_window_days,
        )
    
    def _aggregate_by_week(
        self,
        activities: list[dict[str, Any]],
        garmin_data: dict[str, Any],
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Aggregate activities by week.
        
        Args:
            activities: List of activities to aggregate
            garmin_data: Full Garmin data for recovery metrics
            start_date: Start of aggregation window
            end_date: End of aggregation window
        
        Returns:
            List of weekly aggregate dictionaries
        """
        # Group activities by week
        weeks: dict[date, list[dict[str, Any]]] = defaultdict(list)
        
        for activity in activities:
            activity_date = self._parse_activity_date(activity)
            if activity_date is None:
                continue
            
            week_start = self._get_week_start(activity_date)
            weeks[week_start].append(activity)
        
        # Create weekly aggregates
        aggregates: list[WeeklyAggregate] = []
        
        # Iterate through all weeks in range (even if no activities)
        current_week = self._get_week_start(start_date)
        week_number = 1
        
        while current_week < end_date:
            week_activities = weeks.get(current_week, [])
            
            aggregate = self._create_weekly_aggregate(
                week_start=current_week,
                activities=week_activities,
                garmin_data=garmin_data,
                week_number=week_number,
            )
            
            aggregates.append(aggregate)
            current_week += timedelta(days=7)
            week_number += 1
        
        # Sort by date (oldest first)
        aggregates.sort(key=lambda x: x.week_start)
        
        logger.info(f"Created {len(aggregates)} weekly aggregates")
        
        return [agg.to_dict() for agg in aggregates]
    
    def _create_weekly_aggregate(
        self,
        week_start: date,
        activities: list[dict[str, Any]],
        garmin_data: dict[str, Any],
        week_number: int,
    ) -> WeeklyAggregate:
        """Create a weekly aggregate from a list of activities."""
        week_end = week_start + timedelta(days=6)
        
        # Initialize accumulators
        total_distance = 0.0
        total_duration = 0.0
        total_elevation = 0.0
        total_training_load = 0.0
        
        activities_by_type: dict[str, int] = defaultdict(int)
        distance_by_type: dict[str, float] = defaultdict(float)
        duration_by_type: dict[str, float] = defaultdict(float)
        
        heart_rates: list[float] = []
        max_hrs: list[int] = []
        
        longest_distance = 0.0
        longest_duration = 0.0
        highest_intensity_type = None
        max_intensity_load = 0.0
        
        # Process activities
        for activity in activities:
            activity_type = activity.get("activity_type", "unknown")
            summary = activity.get("summary", {})
            
            # Volume metrics (convert to standard units)
            distance_m = self._safe_float(summary.get("distance", 0))
            distance_km = distance_m / 1000.0 if distance_m else 0.0
            
            duration_s = self._safe_float(summary.get("duration", 0))
            duration_h = duration_s / 3600.0 if duration_s else 0.0
            
            elevation = self._safe_float(summary.get("elevation_gain", 0))
            training_load = self._safe_float(summary.get("activity_training_load", 0))
            
            total_distance += distance_km
            total_duration += duration_h
            total_elevation += elevation
            total_training_load += training_load
            
            # By-type breakdowns
            activities_by_type[activity_type] += 1
            distance_by_type[activity_type] += distance_km
            duration_by_type[activity_type] += duration_h
            
            # Heart rate data
            avg_hr = self._safe_float(summary.get("average_hr"))
            max_hr = self._safe_int(summary.get("max_hr"))
            
            if avg_hr > 0:
                heart_rates.append(avg_hr)
            if max_hr > 0:
                max_hrs.append(max_hr)
            
            # Track longest sessions
            if distance_km > longest_distance:
                longest_distance = distance_km
            if duration_h > longest_duration:
                longest_duration = duration_h
            
            # Track highest intensity
            if training_load > max_intensity_load:
                max_intensity_load = training_load
                highest_intensity_type = activity_type
        
        # Calculate averages
        avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else None
        max_hr = max(max_hrs) if max_hrs else None
        
        # Get recovery metrics for this week
        avg_resting_hr, avg_sleep = self._extract_weekly_recovery_metrics(
            garmin_data, week_start, week_end
        )
        
        return WeeklyAggregate(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            week_number=week_number,
            total_activities=len(activities),
            total_distance_km=total_distance,
            total_duration_hours=total_duration,
            total_elevation_gain_m=total_elevation,
            activities_by_type=dict(activities_by_type),
            distance_by_type=dict(distance_by_type),
            duration_by_type=dict(duration_by_type),
            avg_heart_rate=avg_hr,
            max_heart_rate=max_hr,
            total_training_load=total_training_load if total_training_load > 0 else None,
            longest_activity_distance_km=longest_distance if longest_distance > 0 else None,
            longest_activity_duration_hours=longest_duration if longest_duration > 0 else None,
            highest_intensity_activity=highest_intensity_type,
            avg_resting_hr=avg_resting_hr,
            avg_sleep_hours=avg_sleep,
        )
    
    def _extract_weekly_recovery_metrics(
        self,
        garmin_data: dict[str, Any],
        week_start: date,
        week_end: date,
    ) -> tuple[float | None, float | None]:
        """Extract average recovery metrics for a week."""
        recovery_data = garmin_data.get("recovery_indicators", [])
        
        resting_hrs: list[float] = []
        sleep_hours: list[float] = []
        
        for entry in recovery_data:
            try:
                entry_date = datetime.fromisoformat(entry.get("date", "")).date()
                if week_start <= entry_date <= week_end:
                    # Resting HR
                    sleep_info = entry.get("sleep", {})
                    rhr = sleep_info.get("resting_heart_rate")
                    if rhr:
                        resting_hrs.append(float(rhr))
                    
                    # Sleep duration
                    duration_info = sleep_info.get("duration", {})
                    total_sleep = duration_info.get("total")
                    if total_sleep:
                        sleep_hours.append(float(total_sleep))
            except (ValueError, TypeError, KeyError):
                continue
        
        avg_rhr = sum(resting_hrs) / len(resting_hrs) if resting_hrs else None
        avg_sleep = sum(sleep_hours) / len(sleep_hours) if sleep_hours else None
        
        return avg_rhr, avg_sleep
    
    def _extract_current_metrics(self, garmin_data: dict[str, Any]) -> dict[str, Any]:
        """Extract current physiological markers and training status."""
        physiological = garmin_data.get("physiological_markers", {})
        training_status = garmin_data.get("training_status", {})
        daily_stats = garmin_data.get("daily_stats", {})
        
        return {
            "resting_heart_rate": physiological.get("resting_heart_rate"),
            "vo2_max": physiological.get("vo2_max"),
            "hrv": physiological.get("hrv"),
            "training_load": {
                "acute": training_status.get("acute_training_load", {}).get("acute_load"),
                "chronic": training_status.get("acute_training_load", {}).get("chronic_load"),
                "acwr": training_status.get("acute_training_load", {}).get("acwr"),
            },
            "current_stress": daily_stats.get("average_stress_level"),
            "current_rhr": daily_stats.get("resting_heart_rate"),
        }


# Convenience function for easy integration
def prepare_agent_context(
    garmin_data: dict[str, Any],
    analysis_date: date | None = None,
    recent_window_days: int = 14,
    trends_window_days: int = 90,
) -> dict[str, Any]:
    """
    Convenience function to prepare context for agents.
    
    Args:
        garmin_data: Full Garmin data dictionary
        analysis_date: Date of analysis (defaults to today)
        recent_window_days: Days of detailed recent data (default 14)
        trends_window_days: Days of aggregated trends (default 90)
    
    Returns:
        Dictionary with prepared context ready for state injection
    """
    service = ContextPreparationService()
    context = service.prepare_agent_context(
        garmin_data=garmin_data,
        analysis_date=analysis_date,
        recent_window_days=recent_window_days,
        trends_window_days=trends_window_days,
    )
    return context.to_dict()
