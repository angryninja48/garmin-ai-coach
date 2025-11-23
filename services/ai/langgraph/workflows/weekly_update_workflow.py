"""Lightweight workflow for weekly plan updates without full analysis re-run."""

import logging
from datetime import datetime

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ..config.langsmith_config import LangSmithConfig
from ..nodes.data_integration_node import data_integration_node
from ..nodes.plan_formatter_node import plan_formatter_node
from ..nodes.weekly_planner_node import weekly_planner_node
from ..state.training_analysis_state import TrainingAnalysisState, create_initial_state
from ..utils.workflow_cost_tracker import ProgressIntegratedCostTracker

logger = logging.getLogger(__name__)


def create_weekly_update_workflow():
    """Create a lightweight workflow that only updates the weekly plan.
    
    This skips full analysis and reuses previous expert analysis results,
    only refreshing the weekly plan with latest progress and metrics.
    """
    LangSmithConfig.setup_langsmith()

    workflow = StateGraph(TrainingAnalysisState)

    # Only planning nodes - no analysis nodes
    workflow.add_node("data_integration", data_integration_node)
    workflow.add_node("weekly_planner", weekly_planner_node)
    workflow.add_node("plan_formatter", plan_formatter_node)

    workflow.add_edge(START, "data_integration")
    workflow.add_edge("data_integration", "weekly_planner")
    workflow.add_edge("weekly_planner", "plan_formatter")
    workflow.add_edge("plan_formatter", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("Created lightweight weekly update workflow (3 nodes)")
    return app


async def run_weekly_update(
    user_id: str,
    athlete_name: str,
    incremental_garmin_data: dict,
    weekly_progress: str,
    planning_context: str = "",
    competitions: list | None = None,
    current_date: dict | None = None,
    week_dates: list | None = None,
    # Reuse previous analysis results
    metrics_result: str = "",
    activity_result: str = "",
    physiology_result: str = "",
    season_plan: str = "",
    plots: list | None = None,
    available_plots: list | None = None,
    progress_manager=None,
) -> dict:
    """Run lightweight weekly plan update.
    
    Args:
        user_id: User identifier
        athlete_name: Athlete's name
        incremental_garmin_data: Only last 7-14 days of fresh data
        weekly_progress: User's progress notes from config
        planning_context: Original planning context
        competitions: Competition list
        current_date: Current date dict
        week_dates: Week dates for planning
        metrics_result: Previous metrics expert analysis (reused)
        activity_result: Previous activity expert analysis (reused)
        physiology_result: Previous physiology expert analysis (reused)
        season_plan: Previous season plan (reused)
        plots: Previous plots (reused)
        available_plots: Previous available plots (reused)
        progress_manager: Progress tracking manager
        
    Returns:
        Final state with updated planning_html
    """
    execution_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_weekly_update"
    cost_tracker = ProgressIntegratedCostTracker(f"garmin_ai_coach_weekly_{user_id}", progress_manager)

    # Create state with previous analysis + new progress
    initial_state = create_initial_state(
        user_id=user_id,
        athlete_name=athlete_name,
        garmin_data=incremental_garmin_data,
        planning_context=f"{planning_context}\n\n## Weekly Progress Update\n{weekly_progress}",
        competitions=competitions,
        current_date=current_date,
        week_dates=week_dates,
        execution_id=execution_id,
        plotting_enabled=False,  # No plots needed for updates
    )
    
    # Inject previous analysis results
    initial_state.update({
        "metrics_result": metrics_result,
        "activity_result": activity_result,
        "physiology_result": physiology_result,
        "season_plan": season_plan,
        "plots": plots or [],
        "available_plots": available_plots or [],
    })

    final_state, execution = await cost_tracker.run_workflow_with_progress(
        create_weekly_update_workflow(),
        initial_state,
        execution_id,
        user_id,
    )

    if execution.cost_summary:
        final_state["cost_summary"] = cost_tracker.get_legacy_cost_summary(execution)
        final_state["execution_metadata"] = {
            "trace_id": execution.trace_id,
            "root_run_id": execution.root_run_id,
            "execution_time_seconds": execution.execution_time_seconds,
            "total_cost_usd": execution.cost_summary.total_cost_usd,
            "total_tokens": execution.cost_summary.total_tokens,
        }
        logger.info(
            f"Weekly update complete for user {user_id}: "
            f"${execution.cost_summary.total_cost_usd:.4f} "
            f"({execution.cost_summary.total_tokens} tokens)"
        )
    else:
        logger.warning(f"No cost data available for user {user_id} weekly update")
        final_state["cost_summary"] = {"total_cost_usd": 0.0, "total_tokens": 0}
        final_state["execution_metadata"] = {}

    return final_state
