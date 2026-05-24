# ruff: noqa: E501
"""
HezGene — GitLab CI Integration.

Generates GitLab CI pipeline configuration files that run HezGene
evolution on merge requests.
"""

from __future__ import annotations

from pathlib import Path

# The GitLab CI YAML template
PIPELINE_TEMPLATE = """\
stages:
  - evolve

hezgene-evolution:
  stage: evolve
  image: python:3.12-slim
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - "**/*.py"
  before_script:
    - pip install hezgene
  script:
    - |
      git diff --name-only $CI_MERGE_REQUEST_DIFF_BASE_SHA...$CI_COMMIT_SHA -- '*.py' | while read file; do
        echo "Evolving: $file"
        hezgene run "$file" --llm --verbose
      done
  artifacts:
    paths:
      - .hezgene/sandbox/
    expire_in: 7 days
"""


class GitLabCIIntegration:
    """Generate and manage GitLab CI pipelines for HezGene."""

    CI_FILE = ".gitlab-ci.yml"

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def setup(self) -> Path:
        """Create the GitLab CI pipeline config file.

        Returns the path to the created config file.
        """
        ci_path = self.project_root / self.CI_FILE
        ci_path.write_text(PIPELINE_TEMPLATE, encoding="utf-8")
        return ci_path

    def remove(self) -> bool:
        """Remove the HezGene GitLab CI pipeline config."""
        ci_path = self.project_root / self.CI_FILE
        if ci_path.exists():
            ci_path.unlink()
            return True
        return False

    def is_configured(self) -> bool:
        """Check if the CI config file exists."""
        return (self.project_root / self.CI_FILE).exists()
