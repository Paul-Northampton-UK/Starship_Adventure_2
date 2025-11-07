"""Pydantic models for pack-level YAML files."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PackPowerState(str, Enum):
    """Allowed power states for pack start conditions."""

    OFFLINE = "offline"
    EMERGENCY = "emergency"
    MAIN_POWER = "main_power"
    TORCH_LIGHT = "torch_light"


class GamePackSchema(BaseModel):
    """Schema for packs/<game>/game.yaml."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique pack identifier.")
    title: str | None = Field(default=None, min_length=1, description="Display title.")
    name: str | None = Field(default=None, min_length=1, description="Fallback title field.")
    version: str | None = Field(default=None, min_length=1)
    engine_min_version: str | None = Field(default=None, min_length=1)
    start_room_id: str = Field(..., min_length=1)
    start_power_state: PackPowerState = Field(default=PackPowerState.EMERGENCY)
    schema_version: int | None = None
    authors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str | None = None

    @model_validator(mode="after")
    def ensure_title(cls, model: "GamePackSchema") -> "GamePackSchema":
        """Ensure either title or name is present and normalise defaults."""

        if not (model.title or model.name):
            raise ValueError("Either 'title' or 'name' must be provided in game.yaml")
        if not model.title and model.name:
            model.title = model.name
        if not model.version:
            model.version = "0.1.0"
        return model


class RoomSchema(BaseModel):
    """Minimal schema for room entries used in packs."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, str_strip_whitespace=True)

    room_id: str | None = Field(default=None, alias="room_id")
    id: str | None = Field(default=None, alias="id")
    name: str | None = None
    description: str | None = None
    desc: str | None = None
    long_description: str | None = Field(default=None, alias="long_description")

    @model_validator(mode="after")
    def ensure_identifier(cls, model: "RoomSchema") -> "RoomSchema":
        identifier = model.room_id or model.id
        if not identifier:
            raise ValueError("room entries must include 'room_id' or 'id'")
        model.room_id = identifier
        return model

    def has_any_description(self) -> bool:
        """Return True if any description field contains text."""

        for field_name in ("description", "desc", "long_description"):
            value = getattr(self, field_name, None)
            if isinstance(value, str) and value.strip():
                return True
        return False


class ObjectSchema(BaseModel):
    """Schema for minimal object validation (objects.yaml)."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    location: str | None = None
    properties: dict[str, Any] | None = None
    initial_state: bool | None = None

    def is_hidden(self) -> bool:
        """Whether the object is intentionally hidden / invisible."""

        props = self.properties or {}
        if isinstance(props, dict) and props.get("is_visible") is False:
            return True
        return self.initial_state is False


__all__ = [
    "GamePackSchema",
    "ObjectSchema",
    "PackPowerState",
    "RoomSchema",
]

