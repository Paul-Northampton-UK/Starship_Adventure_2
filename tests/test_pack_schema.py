import pytest
from pydantic import ValidationError

from engine.schemas.pack import GamePackSchema, ObjectSchema, RoomSchema


def test_game_pack_schema_accepts_title_or_name():
    data = {
        "id": "demo_pack",
        "name": "Demo",
        "version": "1.2.3",
        "engine_min_version": "1.0.0",
        "start_room_id": "ship_bridge",
        "start_power_state": "emergency",
    }

    pack = GamePackSchema.model_validate(data)
    assert pack.title == "Demo"
    assert pack.version == "1.2.3"


def test_game_pack_schema_requires_title_or_name():
    data = {
        "id": "demo_pack",
        "version": "1.0.0",
        "start_room_id": "ship_bridge",
        "start_power_state": "emergency",
    }

    with pytest.raises(ValidationError):
        GamePackSchema.model_validate(data)


def test_room_schema_detects_missing_description():
    room = RoomSchema.model_validate({"room_id": "bridge", "name": "Bridge"})
    assert not room.has_any_description()


def test_object_schema_identifies_hidden_objects():
    obj = ObjectSchema.model_validate(
        {
            "id": "mystery",
            "name": "Mystery Item",
            "location": None,
            "properties": {"is_visible": False},
        }
    )
    assert obj.is_hidden()
