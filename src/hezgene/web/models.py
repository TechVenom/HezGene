"""
HezGene Web — Pydantic data models for the API.
"""

from typing import Any

from pydantic import BaseModel


class EvolutionRequest(BaseModel):
    file_id: str
    function_name: str | None = None
    use_llm: bool = False
    apply: bool = False
    generations: int = 5


class ConfigUpdate(BaseModel):
    key: str
    value: Any


class LLMTestRequest(BaseModel):
    provider: str
    model: str
    base_url: str | None = ""
    api_key: str | None = ""


class EvolutionSession(BaseModel):
    session_id: str
    file_id: str
    function_name: str | None = None
    status: str = "pending"
    result: dict | None = None


class GitHubConnectRequest(BaseModel):
    url: str


class ProjectEvolveRequest(BaseModel):
    project_path: str | None = None
    file_path: str | None = None
    function_name: str | None = None
    use_llm: bool = False
    apply: bool = False
    generations: int = 5

