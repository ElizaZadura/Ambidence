from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ModuleSpec(BaseModel):
    name: str
    responsibility: str
    public_api: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class DataModelSpec(BaseModel):
    name: str
    fields: List[str] = Field(default_factory=list)
    invariants: List[str] = Field(default_factory=list)


class InterfaceSpec(BaseModel):
    name: str
    description: str = ""
    signatures: List[str] = Field(default_factory=list)


class OwnershipSpec(BaseModel):
    agent: str
    modules: List[str] = Field(default_factory=list)


class DesignPack(BaseModel):
    """
    Structured output of the `design` phase:
    architecture + contracts only (no implementation code).
    """

    architecture_summary: str = ""

    module_breakdown: List[ModuleSpec] = Field(default_factory=list)
    data_models: List[DataModelSpec] = Field(default_factory=list)
    interfaces: List[InterfaceSpec] = Field(default_factory=list)
    ownership: List[OwnershipSpec] = Field(default_factory=list)

    risks: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)

