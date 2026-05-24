# ruff: noqa: E501
"""
HezGene — GitHub Actions Integration.

Generates GitHub Actions workflow files that run HezGene evolution
on every pull request, posting results as PR comments.
"""

from __future__ import annotations

from pathlib import Path

# The GitHub Actions workflow YAML template
WORKFLOW_TEMPLATE = """\
name: HezGene Evolution

on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - '**.py'

permissions:
  contents: read
  pull-requests: write

jobs:
  evolve:
    name: 🧬 Evolve Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install HezGene
        run: |
          pip install hezgene

      - name: Run Evolution on Changed Files
        run: |
          git diff --name-only origin/${{ github.base_ref }}...HEAD -- '*.py' | while read file; do
            echo "Evolving: $file"
            hezgene run "$file" --llm --verbose
          done

      - name: Post Results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const glob = require('@actions/glob');
            const globber = await glob.create('.hezgene/sandbox/*_evolved.py');
            let body = '## 🧬 HezGene Evolution Report\\n\\n';
            let evolved = 0;
            for await (const file of globber.globGenerator()) {
              evolved++;
              const content = fs.readFileSync(file, 'utf8');
              body += `### ${file}\\n\\`\\`\\`python\\n${content.slice(0, 500)}\\n\\`\\`\\`\\n\\n`;
            }
            if (evolved === 0) {
              body += '✅ All functions are already optimal. No improvements found.\\n';
            } else {
              body += `🏆 ${evolved} function(s) can be improved. Review the sandbox.\\n`;
            }
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
"""


class GitHubActionsIntegration:
    """Generate and manage GitHub Actions workflows for HezGene."""

    WORKFLOW_DIR = ".github/workflows"
    WORKFLOW_FILE = "hezgene-evolve.yml"

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def setup(self) -> Path:
        """Create the GitHub Actions workflow file.

        Returns the path to the created workflow file.
        """
        workflow_dir = self.project_root / self.WORKFLOW_DIR
        workflow_dir.mkdir(parents=True, exist_ok=True)

        workflow_path = workflow_dir / self.WORKFLOW_FILE
        workflow_path.write_text(WORKFLOW_TEMPLATE, encoding="utf-8")
        return workflow_path

    def remove(self) -> bool:
        """Remove the HezGene GitHub Actions workflow."""
        workflow_path = self.project_root / self.WORKFLOW_DIR / self.WORKFLOW_FILE
        if workflow_path.exists():
            workflow_path.unlink()
            return True
        return False

    def is_configured(self) -> bool:
        """Check if the workflow file exists."""
        return (self.project_root / self.WORKFLOW_DIR / self.WORKFLOW_FILE).exists()
