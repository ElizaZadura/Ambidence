from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


ContentMode = Literal["literal", "fenced_code"]


class FileEntry(BaseModel):
    """
    A single file to be written under artifacts/<run_id>/generated_app/.

    content_mode:
      - literal: write content as-is
      - fenced_code: extract first triple-backtick code block and write its inner text
    """

    path: str
    content: str
    content_mode: ContentMode = "literal"
    overwrite: bool = True


class FileManifest(BaseModel):
    task_id: str
    files: List[FileEntry] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

