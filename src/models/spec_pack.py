# models/spec_pack.py
from typing import List
from pydantic import BaseModel, Field


class SpecPack(BaseModel):
    functional_requirements: List[str] = Field(default_factory=list)
    non_functional_constraints: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
