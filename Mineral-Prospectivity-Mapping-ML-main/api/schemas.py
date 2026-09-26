"""Schémas Pydantic pour l'API REST."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ModelInfo(BaseModel):
    name: str
    description: str


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class DemoRequest(BaseModel):
    model: Literal["rf", "svm", "ann", "cnn", "woe"] = "woe"
    seed: int = Field(default=42, ge=0)
    output_dir: str = "outputs/api_demo"


class RunResponse(BaseModel):
    auc: float
    kappa: float
    model: str
    data_source: str
    provenance_path: str
    output_files: list[str]
    map_shape: list[int]


class ValidateRequest(BaseModel):
    config: dict[str, Any]
    check_files: bool = False


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]
    project_name: str | None = None
    model: str | None = None
    region: str | None = None


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
