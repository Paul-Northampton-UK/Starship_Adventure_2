import os
from contextlib import contextmanager

import pytest

from engine.command_defs import CommandIntent
from engine.game_loop import GameLoop
from engine.nlp_v2.parser import NLPCommandParserV2


@contextmanager
def nlp_v2_enabled():
    original = os.environ.get("NLP_V2")
    os.environ["NLP_V2"] = "1"
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("NLP_V2", None)
        else:
            os.environ["NLP_V2"] = original


@pytest.fixture()
def v2_parser():
    with nlp_v2_enabled():
        yield NLPCommandParserV2()


@pytest.mark.parametrize(
    ("text", "direction"),
    [
        ("north", "north"),
        ("go east", "east"),
        ("travel south", "south"),
        ("move up", "up"),
        ("walk in", "in"),
        ("run out", "out"),
    ],
)
def test_v2_move_positive(v2_parser, text, direction):
    result = v2_parser.parse(text)
    assert result["intent"] == "MOVE"
    assert result["data"]["direction"] == direction


@pytest.mark.parametrize(
    ("text", "direction"),
    [
        ("walk to the north", "north"),
        ("GO EAST!", "east"),
        ("  move   west  ", "west"),
    ],
)
def test_v2_move_normalization(v2_parser, text, direction):
    result = v2_parser.parse(text)
    assert result["intent"] == "MOVE"
    assert result["data"]["direction"] == direction


@pytest.mark.parametrize("text", ["inventory", "calibrate sensors", "dance around"])
def test_v2_move_negative(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("look", {"scope": "room"}),
        ("LOOK around", {"scope": "room"}),
        ("examine console", {"target": "console"}),
        ("inspect the red panel", {"target": "red panel"}),
        ("check door", {"target": "door"}),
        ("look at the console", {"target": "console"}),
        ("  Look   around  ", {"scope": "room"}),
        ("EXAMINE   THE   CONSOLE!!!", {"target": "console"}),
    ],
)
def test_v2_look_positive(v2_parser, text, expected):
    result = v2_parser.parse(text)
    assert result["intent"] == "LOOK"
    assert result["data"] == expected


@pytest.mark.parametrize("text", ["inventory", "sing a song"])
def test_v2_look_negative(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"


@pytest.mark.parametrize(
    ("text", "expected_object"),
    [
        ("take keycard", "keycard"),
        ("TAKE THE wrench", "wrench"),
        ("pick up the datapad", "datapad"),
        ("pick up an alien artifact", "alien artifact"),
    ],
)
def test_v2_take_commands(v2_parser, text, expected_object):
    result = v2_parser.parse(text)
    assert result["intent"] == "TAKE"
    assert result["data"]["object"] == expected_object


@pytest.mark.parametrize(
    ("text", "expected_object"),
    [
        ("drop keycard", "keycard"),
        ("drop the strange orb", "strange orb"),
    ],
)
def test_v2_drop_commands(v2_parser, text, expected_object):
    result = v2_parser.parse(text)
    assert result["intent"] == "DROP"
    assert result["data"]["object"] == expected_object


@pytest.mark.parametrize(
    ("text", "obj", "container", "prep"),
    [
        ("put datapad in locker", "datapad", "locker", "in"),
        ("PUT the keycard into the safe", "keycard", "safe", "into"),
        ("put wrench onto workbench", "wrench", "workbench", "onto"),
        ("put the cup on the table", "cup", "table", "on"),
    ],
)
def test_v2_put_commands(v2_parser, text, obj, container, prep):
    result = v2_parser.parse(text)
    assert result["intent"] == "PUT"
    assert result["data"]["object"] == obj
    assert result["data"]["container"] == container
    assert result["data"]["preposition"] == prep


@pytest.mark.parametrize(
    "text",
    [
        "take",
        "drop",
        "put datapad",  # missing container
        "put datapad near locker",  # unsupported preposition
    ],
)
def test_v2_inventory_incomplete_or_invalid(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"


@pytest.mark.parametrize(
    ("text", "intent", "target"),
    [
        ("open airlock", "OPEN", "airlock"),
        ("OPEN THE door", "OPEN", "door"),
        ("close hatch", "CLOSE", "hatch"),
        ("shut the cargo door", "CLOSE", "cargo door"),
    ],
)
def test_v2_open_close_commands(v2_parser, text, intent, target):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"]["target"] == target


@pytest.mark.parametrize(
    ("text", "intent", "target", "tool"),
    [
        ("lock locker", "LOCK", "locker", None),
        ("LOCK the storage hatch", "LOCK", "storage hatch", None),
        ("unlock door with keycard", "UNLOCK", "door", "keycard"),
        ("unlock the vault with the master key", "UNLOCK", "vault", "master key"),
        ("lock the chest with the spare key", "LOCK", "chest", "spare key"),
    ],
)
def test_v2_lock_unlock_commands(v2_parser, text, intent, target, tool):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"]["target"] == target
    if tool is None:
        assert "tool" not in result["data"]
    else:
        assert result["data"]["tool"] == tool


def test_v2_access_missing_target(v2_parser):
    for text in ("open", "lock", "unlock with keycard"):
        result = v2_parser.parse(text)
        assert result["intent"] == "UNKNOWN"


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("help", "HELP"),
        ("save", "SAVE"),
        ("load", "LOAD"),
        ("quit", "QUIT"),
        ("exit", "QUIT"),
    ],
)
def test_v2_system_single_word(v2_parser, text, intent):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"] == {}


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("save game", "SAVE"),
        ("load game", "LOAD"),
        ("exit now", "QUIT"),
        ("please help", "HELP"),
    ],
)
def test_v2_system_multi_word(v2_parser, text, intent):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"] == {}


@pytest.mark.parametrize(
    ("text", "intent"),
    [
        ("HELP!", "HELP"),
        ("  save   game  ", "SAVE"),
        ("LOAD.", "LOAD"),
        ("Quit!!!", "QUIT"),
    ],
)
def test_v2_system_normalization(v2_parser, text, intent):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"] == {}


@pytest.mark.parametrize(
    ("text", "expected_intent"),
    [
        ("open door", "OPEN"),
        ("scan sector", "SCAN"),
        ("take keycard", "TAKE"),
    ],
)
def test_v2_system_negative_cases(v2_parser, text, expected_intent):
    result = v2_parser.parse(text)
    assert result["intent"] == expected_intent


@pytest.mark.parametrize(
    ("text", "npc"),
    [
        ("talk to engineer", "engineer"),
        ("speak to the captain", "captain"),
        ("talk with engineer", "engineer"),
        ("talk to chief engineer", "chief engineer"),
    ],
)
def test_v2_social_talk(v2_parser, text, npc):
    result = v2_parser.parse(text)
    assert result["intent"] == "TALK"
    assert result["data"]["npc"] == npc


@pytest.mark.parametrize(
    ("text", "npc", "topic"),
    [
        ("ask captain about reactor", "captain", "reactor"),
        ("ask the engineer about the power core", "engineer", "power core"),
        ("ask medic status", "medic", "status"),
        ("ask chief engineer about shield harmonics", "chief engineer", "shield harmonics"),
    ],
)
def test_v2_social_ask(v2_parser, text, npc, topic):
    result = v2_parser.parse(text)
    assert result["intent"] == "ASK"
    assert result["data"]["npc"] == npc
    assert result["data"]["topic"] == topic


@pytest.mark.parametrize(
    ("text", "obj", "npc"),
    [
        ("give keycard to guard", "keycard", "guard"),
        ("give the data pad to the captain", "data pad", "captain"),
        ("give access card to security officer", "access card", "security officer"),
        ("give the keycard to the guard", "keycard", "guard"),
    ],
)
def test_v2_social_give(v2_parser, text, obj, npc):
    result = v2_parser.parse(text)
    assert result["intent"] == "GIVE"
    assert result["data"]["object"] == obj
    assert result["data"]["npc"] == npc


@pytest.mark.parametrize(
    ("text", "obj", "npc"),
    [
        ("show datapad to medic", "datapad", "medic"),
        ("show the artifact to the scientist", "artifact", "scientist"),
        ("SHOW   datapad   to   MEDIC!!!", "datapad", "medic"),
    ],
)
def test_v2_social_show(v2_parser, text, obj, npc):
    result = v2_parser.parse(text)
    assert result["intent"] == "SHOW"
    assert result["data"]["object"] == obj
    assert result["data"]["npc"] == npc


@pytest.mark.parametrize(
    "text",
    [
        "talk",
        "ask captain",
        "give keycard",
        "show to guard",
        "show datapad",
        "give the keycard for guard",
        "give it to him",
        "show datapad to him",
        "ask about reactor",
    ],
)
def test_v2_social_incomplete(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"


@pytest.mark.parametrize(
    ("text", "target", "intent"),
    [
        ("read datapad", "datapad", "READ"),
        ("scan console", "console", "SCAN"),
        ("read mission log", "mission log", "READ"),
        ("scan access panel", "access panel", "SCAN"),
        ("read the datapad", "datapad", "READ"),
        ("scan the console", "console", "SCAN"),
        ("READ   datapad!", "datapad", "READ"),
        (" scan   the   panel ", "panel", "SCAN"),
    ],
)
def test_v2_read_scan_positive(v2_parser, text, target, intent):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"]["target"] == target


@pytest.mark.parametrize(
    "text",
    [
        "read",
        "scan",
        "read it",
        "scan it",
        "read from datapad",
        "scan with tricorder",
        "read from the datapad",
        "scan with the console",
    ],
)
def test_v2_read_scan_invalid_forms(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"
    assert result["data"] == {}


def test_v2_read_scan_does_not_override_look(v2_parser):
    result = v2_parser.parse("look at datapad")
    assert result["intent"] == "LOOK"
    assert result["data"]["target"] == "datapad"


def test_v2_read_scan_adapter_target_population():
    loop = GameLoop.__new__(GameLoop)
    read_parsed = loop._adapt_v2_result(
        {"intent": "READ", "data": {"target": "mission log"}},
        "read mission log",
    )
    assert read_parsed.intent == CommandIntent.READ
    assert read_parsed.target == "mission log"

    scan_parsed = loop._adapt_v2_result(
        {"intent": "SCAN", "data": {"target": "console"}},
        "scan console",
    )
    assert scan_parsed.intent == CommandIntent.SCAN
    assert scan_parsed.target == "console"


@pytest.mark.parametrize(
    ("text", "intent", "target"),
    [
        ("equip energy pistol", "EQUIP", "energy pistol"),
        ("unequip suit", "UNEQUIP", "suit"),
        ("wear the space suit", "WEAR", "space suit"),
        ("remove helmet", "REMOVE", "helmet"),
        ("WIELD plasma saber", "WIELD", "plasma saber"),
    ],
)
def test_v2_equipment_positive(v2_parser, text, intent, target):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    assert result["data"]["target"] == target


@pytest.mark.parametrize(
    "text",
    [
        "equip",
        "unequip",
        "wear",
        "remove",
        "wield",
        "equip with rifle",
        "remove from suit",
        "wear it",
    ],
)
def test_v2_equipment_invalid(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"
    assert result["data"] == {}


def test_v2_equipment_adapter_sets_action_and_target():
    loop = GameLoop.__new__(GameLoop)
    parsed = loop._adapt_v2_result(
        {"intent": "WEAR", "data": {"target": "space suit", "action": "wear"}},
        "wear space suit",
    )
    assert parsed.intent == CommandIntent.WEAR
    assert parsed.target == "space suit"
    assert parsed.action == "wear"


@pytest.mark.parametrize(
    ("text", "intent", "target", "weapon"),
    [
        ("attack", "ATTACK", None, None),
        ("attack pirate", "ATTACK", "pirate", None),
        ("attack security drone", "ATTACK", "security drone", None),
        ("ATTACK pirate!", "ATTACK", "pirate", None),
        ("aim", "AIM", None, None),
        ("aim pistol", "AIM", "pistol", None),
        ("aim energy pistol", "AIM", "energy pistol", None),
        ("shoot drone", "SHOOT", "drone", None),
        ("shoot pistol at drone", "SHOOT", "drone", "pistol"),
        ("fire pistol", "SHOOT", None, "pistol"),
        (" shoot   drone ", "SHOOT", "drone", None),
        ("Fire   the   pistol", "SHOOT", None, "pistol"),
        ("block", "BLOCK", None, None),
        ("dodge", "DODGE", None, None),
        ("flee", "FLEE", None, None),
        ("run away", "FLEE", None, None),
    ],
)
def test_v2_combat_positive(v2_parser, text, intent, target, weapon):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    if target:
        assert result["data"]["target"] == target
    else:
        assert "target" not in result["data"]
    if weapon:
        assert result["data"]["weapon"] == weapon
    else:
        assert "weapon" not in result["data"]


@pytest.mark.parametrize(
    "text",
    [
        "attack with",
        "attack with pistol",
        "aim it",
        "shoot",
        "fire",
        "shoot at drone",
        "equip with pistol",  # regression guard
        "attack him",
        "shoot it",
        "fight",
    ],
)
def test_v2_combat_invalid(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"
    assert result["data"] == {}


def test_v2_combat_adapter_weapon_target():
    loop = GameLoop.__new__(GameLoop)
    parsed = loop._adapt_v2_result(
        {"intent": "SHOOT", "data": {"weapon": "pistol", "target": "drone"}},
        "shoot pistol at drone",
    )
    assert parsed.intent == CommandIntent.SHOOT
    assert parsed.target == "drone"
    assert parsed.secondary_target == "pistol"


@pytest.mark.parametrize(
    ("text", "intent", "weapon", "ammo", "target"),
    [
        ("reload pistol", "RELOAD", "pistol", None, None),
        ("reload pistol with energy cell", "RELOAD", "pistol", "energy cell", None),
        ("load rifle", "RELOAD", "rifle", None, None),
        ("unload pistol", "UNLOAD", "pistol", None, None),
        ("check ammo", "CHECK", None, None, "ammo"),
        ("check pistol", "CHECK", None, None, "pistol"),
    ],
)
def test_v2_reload_unload_check_positive(v2_parser, text, intent, weapon, ammo, target):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    data = result["data"]
    if weapon:
        assert data["weapon"] == weapon
    else:
        assert "weapon" not in data
    if ammo:
        assert data["ammo"] == ammo
    else:
        assert "ammo" not in data
    if target:
        assert data["target"] == target
    else:
        assert "target" not in data


@pytest.mark.parametrize(
    "text",
    [
        "reload",
        "reload with ammo",
        "unload",
        "check",
    ],
)
def test_v2_reload_unload_check_invalid(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"
    assert result["data"] == {}


def test_v2_reload_adapter_fields():
    loop = GameLoop.__new__(GameLoop)
    parsed = loop._adapt_v2_result(
        {"intent": "RELOAD", "data": {"weapon": "pistol", "ammo": "cell"}},
        "reload pistol with cell",
    )
    assert parsed.intent == CommandIntent.RELOAD
    assert parsed.target == "pistol"
    assert parsed.secondary_target == "cell"


@pytest.mark.parametrize(
    ("text", "intent", "target"),
    [
        ("sneak", "SNEAK", None),
        ("hide", "HIDE", None),
        ("pickpocket guard", "PICKPOCKET", "guard"),
        ("PICKPOCKET the captain", "PICKPOCKET", "captain"),
        ("disarm trap", "DISARM_TRAP", "trap"),
        ("disarm security trap", "DISARM_TRAP", "security trap"),
    ],
)
def test_v2_stealth_positive(v2_parser, text, intent, target):
    result = v2_parser.parse(text)
    assert result["intent"] == intent
    if target is None:
        assert result["data"] == {}
    else:
        key = "npc" if intent == "PICKPOCKET" else "trap"
        assert result["data"][key] == target


@pytest.mark.parametrize(
    "text",
    [
        "sneak past guard",
        "hide behind crate",
        "pickpocket",
        "pickpocket him",
        "disarm",
        "disarm it",
    ],
)
def test_v2_stealth_invalid(v2_parser, text):
    result = v2_parser.parse(text)
    assert result["intent"] == "UNKNOWN"
    assert result["data"] == {}


def test_v2_stealth_adapter_targets():
    loop = GameLoop.__new__(GameLoop)
    pick = loop._adapt_v2_result(
        {"intent": "PICKPOCKET", "data": {"npc": "guard"}},
        "pickpocket guard",
    )
    assert pick.intent == CommandIntent.PICKPOCKET
    assert pick.target == "guard"

    disarm = loop._adapt_v2_result(
        {"intent": "DISARM_TRAP", "data": {"trap": "laser trap"}},
        "disarm laser trap",
    )
    assert disarm.intent == CommandIntent.DISARM_TRAP
    assert disarm.target == "laser trap"
