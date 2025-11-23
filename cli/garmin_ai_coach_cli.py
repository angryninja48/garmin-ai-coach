#!/usr/bin/env python3

import argparse
import asyncio
import getpass
import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from services.outside.client import OutsideApiGraphQlClient

sys.path.append(str(Path(__file__).parent.parent))


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class ConfigParser:

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        content = self.config_path.read_text(encoding="utf-8")

        if self.config_path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(content)
        elif self.config_path.suffix == ".json":
            return json.loads(content)
        else:
            raise ValueError(f"Unsupported config format: {self.config_path.suffix}")

    def get_athlete_info(self) -> tuple[str, str]:
        if not (email := self.config.get("athlete", {}).get("email")):
            raise ValueError("Athlete email is required in config file")

        return self.config.get("athlete", {}).get("name", "Athlete"), email

    def get_contexts(self) -> tuple[str, str]:
        return (
            self.config.get("context", {}).get("analysis", "").strip(),
            self.config.get("context", {}).get("planning", "").strip()
        )

    def get_extraction_config(self) -> dict[str, Any]:
        extraction = self.config.get("extraction", {})
        return {
            "activities_days": extraction.get("activities_days", 7),
            "metrics_days": extraction.get("metrics_days", 14),
            "context_recent_days": extraction.get("context_recent_days", 14),
            "context_trends_days": extraction.get("context_trends_days", 180),
            "ai_mode": extraction.get("ai_mode", "development"),
            "enable_plotting": extraction.get("enable_plotting", False),
            "hitl_enabled": extraction.get("hitl_enabled", True),
        }

    def get_competitions(self) -> list[dict[str, Any]]:
        competitions = self.config.get("competitions", [])
        return [
            {
                "name": comp.get("name", ""),
                "date": comp.get("date", ""),
                "race_type": comp.get("race_type", ""),
                "priority": comp.get("priority", "B"),
                "target_time": comp.get("target_time", ""),
            }
            for comp in competitions
        ]

    def get_output_directory(self) -> Path:
        return Path(self.config.get("output", {}).get("directory", "./data"))

    def get_password(self) -> str:
        return (
            self.config.get("credentials", {}).get("password", "") or
            getpass.getpass("Enter Garmin Connect password: ")
        )

    def get_weekly_progress(self) -> str:
        """Get progress notes from config for weekly updates."""
        return self.config.get("weekly_progress", {}).get("notes", "").strip()


def fetch_outside_competitions_from_config(config: dict[str, Any]) -> list[dict[str, Any]]:
    client = OutsideApiGraphQlClient()

    if isinstance(outside_cfg := config.get("outside"), dict) and any(
        isinstance(value, list) for value in outside_cfg.values()
    ):
        return client.get_competitions(outside_cfg)

    aggregate: list[dict[str, Any]] = []

    if isinstance(legacy_bikereg := config.get("bikereg", []), list) and legacy_bikereg:
        aggregate.extend(client.get_competitions(legacy_bikereg))

    if legacy_all := {
        key: entries
        for key in ("runreg", "trireg", "skireg")
        if isinstance(entries := config.get(key, []), list) and entries
    }:
        aggregate.extend(client.get_competitions(legacy_all))

    return aggregate


async def run_analysis_from_config(config_path: Path) -> None:
    config_parser = ConfigParser(config_path)
    athlete_name, email = config_parser.get_athlete_info()
    analysis_context, planning_context = config_parser.get_contexts()
    extraction_settings = config_parser.get_extraction_config()

    competitions = config_parser.get_competitions()
    outside_competitions = fetch_outside_competitions_from_config(config_parser.config)
    if outside_competitions:
        competitions.extend(outside_competitions)

    output_dir = config_parser.get_output_directory()

    logger.info(f"Starting analysis for {athlete_name}")
    logger.info(f"Output directory: {output_dir}")

    password = config_parser.get_password()

    os.environ["AI_MODE"] = extraction_settings.get("ai_mode", "development")
    logger.info(f"AI Mode: {os.environ['AI_MODE']}")

    from langsmith.run_helpers import trace

    from services.ai.langgraph.state.training_analysis_state import create_initial_state
    from services.ai.langgraph.workflows.interactive_runner import run_workflow_with_hitl
    from services.ai.langgraph.workflows.planning_workflow import (
        create_integrated_analysis_and_planning_workflow,
        run_complete_analysis_and_planning,
    )
    from services.garmin import ExtractionConfig, TriathlonCoachDataExtractor, prepare_agent_context

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Extracting Garmin Connect data...")
        extractor = TriathlonCoachDataExtractor(email, password)

        extraction_config = ExtractionConfig(
            activities_range=extraction_settings["activities_days"],
            metrics_range=extraction_settings["metrics_days"],
            include_detailed_activities=True,
            include_metrics=True,
        )

        garmin_data = extractor.extract_data(extraction_config)
        logger.info("Data extraction completed")
        
        # Prepare optimized context for agents
        recent_days = extraction_settings.get("context_recent_days", 14)
        trends_days = extraction_settings.get("context_trends_days", 180)
        logger.info(f"Preparing optimized context: {recent_days}d recent + {trends_days}d trends...")
        garmin_data_dict = asdict(garmin_data)
        prepared_context = prepare_agent_context(
            garmin_data=garmin_data_dict,
            analysis_date=None,  # Use today
            recent_window_days=recent_days,
            trends_window_days=trends_days,
        )
        logger.info("Context preparation completed")

        now = datetime.now()
        plotting_enabled = extraction_settings.get("enable_plotting", False)
        hitl_enabled = extraction_settings.get("hitl_enabled", True)
        
        logger.info(f"Plotting enabled: {plotting_enabled}")
        logger.info(f"HITL enabled: {hitl_enabled}")
        
        current_date = {"date": now.strftime("%Y-%m-%d"), "day_name": now.strftime("%A")}
        week_dates = [
            {"date": (now + timedelta(days=offset)).strftime("%Y-%m-%d"),
             "day_name": (now + timedelta(days=offset)).strftime("%A")}
            for offset in range(14)
        ]
        
        logger.info("Running AI analysis and planning...")
        
        if hitl_enabled:
            def prompt_user(question: str) -> str:
                print(f"\n{'='*70}")
                print(f"🤖 {question}")
                print(f"{'='*70}")
                response = input("\n👤 Your answer: ").strip()
                return response
            
            def show_progress(message: str) -> None:
                print(message)
            
            workflow = create_integrated_analysis_and_planning_workflow()
            execution_id = f"cli_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}_complete"
            config = {"configurable": {"thread_id": execution_id}}
            
            async with trace(
                name="Garmin HITL Session",
                project_name="garmin_ai_coach_analysis",
                inputs={
                    "thread_id": execution_id,
                    "athlete": athlete_name,
                    "plotting_enabled": plotting_enabled,
                    "hitl_enabled": True,
                },
                tags=[f"thread:{execution_id}", "garmin", "hitl", "cli"],
            ) as run:
                logger.info("Created parent LangSmith run for HITL session")
                
                result = await run_workflow_with_hitl(
                    workflow_app=workflow,
                    initial_state=create_initial_state(
                        user_id="cli_user",
                        athlete_name=athlete_name,
                        garmin_data=garmin_data_dict,
                        prepared_context=prepared_context,
                        analysis_context=analysis_context,
                        planning_context=planning_context,
                        competitions=competitions,
                        current_date=current_date,
                        week_dates=week_dates,
                        execution_id=execution_id,
                        plotting_enabled=plotting_enabled,
                        hitl_enabled=True,
                    ),
                    config=config,
                    prompt_callback=prompt_user,
                    progress_callback=show_progress,
                )
                
                run.end(outputs={
                    "status": "completed",
                    "execution_id": execution_id,
                    "cancelled": result.get("cancelled", False),
                })
                logger.info("Parent LangSmith run completed successfully")
        else:
            result = await run_complete_analysis_and_planning(
                user_id="cli_user",
                athlete_name=athlete_name,
                garmin_data=garmin_data_dict,
                prepared_context=prepared_context,
                analysis_context=analysis_context,
                planning_context=planning_context,
                competitions=competitions,
                current_date=current_date,
                week_dates=week_dates,
                plotting_enabled=plotting_enabled,
                hitl_enabled=False,
            )

        logger.info("Saving results...")

        files_generated: list[str] = []
        
        for filename, key in [
            ("analysis.html", "analysis_html"),
            ("planning.html", "planning_html"),
            ("metrics_result.md", "metrics_result"),
            ("activity_result.md", "activity_result"),
            ("physiology_result.md", "physiology_result"),
            ("season_plan.md", "season_plan"),
        ]:
            if content := result.get(key):
                (output_dir / filename).write_text(content, encoding="utf-8")
                files_generated.append(filename)
                logger.info(f"Saved: {output_dir}/{filename}")

        cost_total = float(
            result.get("cost_summary", {}).get("total_cost_usd", 0.0) or
            result.get("execution_metadata", {}).get("total_cost_usd", 0.0) or
            sum(cost.get("total_cost", 0) for cost in result.get("costs", []))
        )
        total_tokens = int(
            result.get("cost_summary", {}).get("total_tokens", 0) or
            result.get("execution_metadata", {}).get("total_tokens", 0)
        )

        (output_dir / "summary.json").write_text(
            json.dumps({
                "athlete": athlete_name,
                "analysis_date": datetime.now().isoformat(),
                "competitions": competitions,
                "total_cost_usd": cost_total,
                "total_tokens": total_tokens,
                "execution_id": result.get("execution_id", ""),
                "trace_id": result.get("execution_metadata", {}).get("trace_id", ""),
                "root_run_id": result.get("execution_metadata", {}).get("root_run_id", ""),
                "files_generated": files_generated,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        logger.info("✅ Analysis completed successfully!")
        if outside_competitions:
            logger.info(f"✅  Added {len(outside_competitions)} Outside competitions from config")
        logger.info(f"📁 Results saved to: {output_dir}")
        logger.info(f"💰 Total cost: ${cost_total:.2f} ({total_tokens} tokens)")
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise


async def run_weekly_update_from_config(config_path: Path) -> None:
    """Run lightweight weekly plan update without full analysis.
    
    This reuses previous analysis results and only updates the weekly plan
    with fresh metrics and progress notes. Much faster and cheaper than
    running full analysis.
    """
    config_parser = ConfigParser(config_path)
    athlete_name, email = config_parser.get_athlete_info()
    planning_context = config_parser.get_contexts()[1]  # Only need planning context
    weekly_progress = config_parser.get_weekly_progress()
    extraction_settings = config_parser.get_extraction_config()
    
    competitions = config_parser.get_competitions()
    outside_competitions = fetch_outside_competitions_from_config(config_parser.config)
    if outside_competitions:
        competitions.extend(outside_competitions)
    
    output_dir = config_parser.get_output_directory()
    
    logger.info(f"Running weekly update for {athlete_name}")
    logger.info(f"Output directory: {output_dir}")
    
    # Check for previous analysis files
    required_files = ["metrics_result.md", "activity_result.md", "physiology_result.md", "season_plan.md"]
    missing_files = [f for f in required_files if not (output_dir / f).exists()]
    if missing_files:
        logger.error(f"❌ Missing previous analysis files: {', '.join(missing_files)}")
        logger.error("Run full analysis first with: pixi run coach-cli --config <config>")
        raise FileNotFoundError(f"Required analysis files not found: {missing_files}")
    
    password = config_parser.get_password()
    os.environ["AI_MODE"] = extraction_settings.get("ai_mode", "development")
    
    from services.ai.langgraph.workflows.weekly_update_workflow import run_weekly_update
    from services.garmin import ExtractionConfig, TriathlonCoachDataExtractor
    
    try:
        logger.info("Extracting incremental Garmin data (last 14 days)...")
        extractor = TriathlonCoachDataExtractor(email, password)
        
        # Only fetch last 14 days for efficiency
        extraction_config = ExtractionConfig(
            activities_range=14,
            metrics_range=14,
            include_detailed_activities=True,
            include_metrics=True,
        )
        
        garmin_data = extractor.extract_data(extraction_config)
        garmin_data_dict = asdict(garmin_data)
        logger.info("Incremental data extraction completed")
        
        # Load previous analysis results
        logger.info("Loading previous analysis results...")
        metrics_result = (output_dir / "metrics_result.md").read_text(encoding="utf-8")
        activity_result = (output_dir / "activity_result.md").read_text(encoding="utf-8")
        physiology_result = (output_dir / "physiology_result.md").read_text(encoding="utf-8")
        season_plan = (output_dir / "season_plan.md").read_text(encoding="utf-8")
        
        now = datetime.now()
        current_date = {"date": now.strftime("%Y-%m-%d"), "day_name": now.strftime("%A")}
        week_dates = [
            {"date": (now + timedelta(days=offset)).strftime("%Y-%m-%d"),
             "day_name": (now + timedelta(days=offset)).strftime("%A")}
            for offset in range(14)
        ]
        
        logger.info("Running AI weekly plan update...")
        result = await run_weekly_update(
            user_id="cli_user",
            athlete_name=athlete_name,
            incremental_garmin_data=garmin_data_dict,
            weekly_progress=weekly_progress,
            planning_context=planning_context,
            competitions=competitions,
            current_date=current_date,
            week_dates=week_dates,
            metrics_result=metrics_result,
            activity_result=activity_result,
            physiology_result=physiology_result,
            season_plan=season_plan,
        )
        
        logger.info("Saving updated plan...")
        
        if content := result.get("planning_html"):
            (output_dir / "planning.html").write_text(content, encoding="utf-8")
            logger.info(f"Saved: {output_dir}/planning.html")
        
        cost_total = float(result.get("cost_summary", {}).get("total_cost_usd", 0.0))
        total_tokens = int(result.get("cost_summary", {}).get("total_tokens", 0))
        
        # Update summary.json with weekly update metadata
        summary_path = output_dir / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        else:
            summary = {"athlete": athlete_name}
        
        summary.update({
            "last_weekly_update": datetime.now().isoformat(),
            "weekly_update_cost_usd": cost_total,
            "weekly_update_tokens": total_tokens,
        })
        
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        
        logger.info("✅ Weekly update completed successfully!")
        logger.info(f"📁 Updated plan saved to: {output_dir}")
        logger.info(f"💰 Update cost: ${cost_total:.2f} ({total_tokens} tokens)")
        
    except Exception as e:
        logger.error(f"❌ Weekly update failed: {e}")
        raise


def create_config_template(output_path: Path) -> None:
    template_path = Path(__file__).parent / "coach_config_template.yaml"

    if template_path.exists():
        output_path.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info(f"✅ Config template created: {output_path}")
        logger.info("Edit this file with your settings and run analysis with --config")
    else:
        logger.error("❌ Template file not found")


def main():
    parser = argparse.ArgumentParser(
        description="Garmin AI Coach CLI - AI Triathlon Coach",
        epilog="Example: python garmin_ai_coach_cli.py --config my_config.yaml",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=Path, help="Path to configuration file (YAML or JSON)")
    group.add_argument("--init-config", type=Path, help="Create a configuration template file")

    parser.add_argument("--output-dir", type=Path, help="Override output directory from config")
    parser.add_argument(
        "--update-plan",
        action="store_true",
        help="Run lightweight weekly plan update (requires previous analysis)"
    )

    args = parser.parse_args()

    if args.init_config:
        create_config_template(args.init_config)
        return

    if args.config:
        try:
            if args.update_plan:
                logger.info("Running weekly plan update mode (fast & cost-effective)")
                asyncio.run(run_weekly_update_from_config(args.config))
            else:
                asyncio.run(run_analysis_from_config(args.config))
        except KeyboardInterrupt:
            logger.info("❌ Analysis cancelled by user")
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
