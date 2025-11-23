from dataclasses import dataclass, field
from enum import Enum

from core.config import AIMode, get_config


class AgentRole(Enum):
    SUMMARIZER = "summarizer"
    METRICS_EXPERT = "metrics_expert"
    PHYSIOLOGY_EXPERT = "physiology_expert"
    ACTIVITY_EXPERT = "activity_expert"
    SYNTHESIS = "synthesis"
    WORKOUT = "workout"
    COMPETITION_PLANNER = "competition_planner"
    SEASON_PLANNER = "season_planner"
    FORMATTER = "formatter"


@dataclass
class AISettings:
    mode: AIMode

    model_assignments: dict[AIMode, dict[AgentRole, str]] = field(
        default_factory=lambda: {
            AIMode.STANDARD: {
                # Data Summarization - Fast & Efficient
                AgentRole.SUMMARIZER: "claude-4",
                AgentRole.FORMATTER: "gpt-4o",
                # Deep Analysis - Claude Opus with extended reasoning
                AgentRole.METRICS_EXPERT: "claude-opus-thinking",
                AgentRole.PHYSIOLOGY_EXPERT: "claude-opus-thinking",
                AgentRole.ACTIVITY_EXPERT: "claude-opus",
                # Synthesis - High-quality output
                AgentRole.SYNTHESIS: "claude-opus",
                # Strategic Planning - GPT-5 reasoning
                AgentRole.WORKOUT: "gpt-5",
                AgentRole.COMPETITION_PLANNER: "gpt-5",
                AgentRole.SEASON_PLANNER: "gpt-5",
            },
            AIMode.COST_EFFECTIVE: {
                # Gemini 2.0 Flash - Extremely cheap, 2M context, very fast
                AgentRole.SUMMARIZER: "gemini-2.5-flash",
                AgentRole.METRICS_EXPERT: "gemini-2.5-flash",
                AgentRole.PHYSIOLOGY_EXPERT: "gemini-2.5-flash",
                AgentRole.ACTIVITY_EXPERT: "gemini-2.5-flash",
                AgentRole.SYNTHESIS: "gemini-2.5-flash",
                # GPT-5-mini for formatting/planning - fast & cheap
                AgentRole.FORMATTER: "gpt-5-mini",
                AgentRole.WORKOUT: "gpt-5-mini",
                AgentRole.COMPETITION_PLANNER: "gpt-5-mini",
                AgentRole.SEASON_PLANNER: "gpt-5-mini",
            },
            AIMode.DEVELOPMENT: {
                # Claude-4 Thinking for development debugging
                AgentRole.SUMMARIZER: "claude-4-thinking",
                AgentRole.FORMATTER: "claude-4",
                AgentRole.METRICS_EXPERT: "claude-4-thinking",
                AgentRole.PHYSIOLOGY_EXPERT: "claude-4-thinking",
                AgentRole.ACTIVITY_EXPERT: "claude-4-thinking",
                AgentRole.SYNTHESIS: "claude-4-thinking",
                AgentRole.WORKOUT: "claude-4-thinking",
                AgentRole.COMPETITION_PLANNER: "claude-4-thinking",
                AgentRole.SEASON_PLANNER: "claude-4-thinking",
            },
        }
    )

    def get_model_for_role(self, role: AgentRole) -> str:
        return self.model_assignments[self.mode][role]

    @classmethod
    def load_settings(cls) -> "AISettings":
        return cls(mode=get_config().ai_mode)


# Global settings instance
ai_settings = AISettings.load_settings()
