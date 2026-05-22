"""
HezGene Exceptions — Custom exception classes for the evolution platform.
"""

from __future__ import annotations


class EnterpriseFeatureError(RuntimeError):
    """Raised when a user attempts to use an enterprise-only feature.

    Provides a structured upsell message with feature name, description,
    and upgrade URL.
    """

    UPGRADE_URL = "https://hezgene.ai/pricing"

    # Feature descriptions for upsell messages
    FEATURES = {
        "llm_mutations": {
            "title": "LLM-Powered Mutations",
            "description": (
                "Unlock creative AI mutations using VENOMX, GPT-4, Claude, or Gemini.\n"
                "   Free users get 6 AST mutation strategies.\n"
                "   Enterprise users add unlimited LLM-powered mutations."
            ),
        },
        "web_dashboard": {
            "title": "Battle Arena Web Dashboard",
            "description": (
                "Watch your code evolve in real-time. See mutants fight in the arena.\n"
                "   Compare DNA profiles. Deploy winners with one click."
            ),
        },
        "ci_cd": {
            "title": "CI/CD Integration",
            "description": (
                "Automatically evolve your code on every pull request.\n"
                "   HezGene reviews your code and suggests improvements."
            ),
        },
        "team_management": {
            "title": "Team Management",
            "description": (
                "Manage seats, permissions, and shared evolution configs.\n"
                "   Collaborate on code evolution across your team."
            ),
        },
    }

    def __init__(self, feature_key: str, message: str = ""):
        feature = self.FEATURES.get(feature_key, {})
        title = feature.get("title", feature_key.replace("_", " ").title())
        description = feature.get("description", message)

        self.feature_key = feature_key
        self.title = title
        self.description = description

        full_message = (
            f"🔒 {title} (Enterprise Feature)\n"
            f"   {description}\n\n"
            f"   Upgrade: {self.UPGRADE_URL}"
        )
        super().__init__(full_message)

    def rich_message(self) -> str:
        """Return a rich-formatted version for CLI display."""
        return (
            f"[bold red]🔒 {self.title}[/] [dim](Enterprise Feature)[/]\n"
            f"   {self.description}\n\n"
            f"   [bold cyan]Upgrade:[/] [link={self.UPGRADE_URL}]{self.UPGRADE_URL}[/]"
        )
