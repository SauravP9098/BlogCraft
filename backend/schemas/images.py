from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ImageSpec(BaseModel):
    placeholder: str = Field(default="[[IMAGE_1]]", description="e.g. [[IMAGE_1]]")
    after_section: str = Field(default="", description="The ## Section heading after which to place this image")
    filename: str = Field(..., description="Save filename, e.g. qkv_flow.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt to send to the image model.")
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    images: List[ImageSpec] = Field(default_factory=list)
    md_with_placeholders: Optional[str] = None
