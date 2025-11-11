from __future__ import annotations

import re
from typing import Any, Dict

from loguru import logger


FILLER_WORDS = {"the", "to", "at", "on", "a", "an"}
ARTICLE_WORDS = {"the", "a", "an"}
DIRECTION_MAP = {
    "north": "north",
    "south": "south",
    "east": "east",
    "west": "west",
    "up": "up",
    "down": "down",
    "in": "in",
    "out": "out",
    "enter": "in",
    "exit": "out",
}
MOVEMENT_VERBS = {"go", "move", "travel", "walk", "run"}
OBSERVATION_VERBS = {"look", "examine", "inspect", "check"}
TAKE_VERB = "take"
TAKE_TWO_WORD_VERB = ("pick", "up")
DROP_VERB = "drop"
PUT_VERB = "put"
PUT_PREPOSITIONS = {"in", "into", "onto", "on"}
OPEN_VERBS = {"open"}
CLOSE_VERBS = {"close", "shut"}
LOCK_VERBS = {"lock"}
UNLOCK_VERBS = {"unlock"}
TOOL_DELIMITER = "with"
SYSTEM_COMMANDS = {
    "help": "HELP",
    "save": "SAVE",
    "load": "LOAD",
    "quit": "QUIT",
    "exit": "QUIT",
}
SOCIAL_TALK_VERBS = {"talk", "speak"}
SOCIAL_ASK_VERB = "ask"
SOCIAL_GIVE_VERB = "give"
SOCIAL_SHOW_VERB = "show"
SOCIAL_TALK_PREPOSITIONS = {"to", "with"}
PRONOUN_BLOCKLIST = {
    "him",
    "her",
    "them",
    "it",
    "himself",
    "herself",
    "themselves",
    "me",
    "you",
    "us",
    "ourselves",
    "yourself",
    "yourselves",
    "myself",
}
READ_VERBS = {"read"}
SCAN_VERBS = {"scan"}
EQUIP_VERBS = {"equip"}
UNEQUIP_VERBS = {"unequip"}
WEAR_VERBS = {"wear"}
REMOVE_VERBS = {"remove"}
WIELD_VERBS = {"wield"}
RELOAD_VERBS = {"reload", "load"}
UNLOAD_VERBS = {"unload"}
CHECK_VERBS = {"check"}
READ_SCAN_INVALID_PREFIXES = {"from", "with"}
EQUIP_INVALID_PREFIXES = {"with", "from"}
ATTACK_VERBS = {"attack"}
AIM_VERBS = {"aim"}
SHOOT_VERBS = {"shoot", "fire"}
BLOCK_VERBS = {"block"}
DODGE_VERBS = {"dodge"}
FLEE_SINGLE_VERBS = {"flee"}
FLEE_MULTI = [("run", "away")]
COMBAT_INVALID_PREFIXES = {"with", "from"}
RELOAD_INVALID_PREFIXES = {"from"}
UNLOAD_INVALID_PREFIXES = {"from", "with"}
SNEAK_VERBS = {"sneak"}
HIDE_VERBS = {"hide"}
PICKPOCKET_VERBS = {"pickpocket"}
DISARM_VERBS = {"disarm"}


class NLPCommandParserV2:
    """Placeholder implementation for the upcoming NLP v2 parser."""

    def __init__(self) -> None:
        logger.debug("NLPCommandParserV2 scaffold initialized.")

    def parse(self, text: str) -> Dict[str, Any]:
        """Temporary stub that always returns an UNKNOWN intent."""
        sanitized = self._sanitize_text(text)
        tokens = self._tokens_without_fillers(sanitized)

        social = self._detect_social_command(sanitized)
        if social is not None:
            logger.info(
                "NLPCommandParserV2 detected %s intent with data %s.",
                social["intent"],
                social["data"],
            )
            return social

        read_scan = self._detect_read_or_scan(sanitized)
        if read_scan is not None:
            logger.info(
                "NLPCommandParserV2 detected %s intent with data %s.",
                read_scan["intent"],
                read_scan["data"],
            )
            return read_scan

        equipment = self._detect_equipment_command(sanitized)
        if equipment is not None:
            logger.info(
                "NLPCommandParserV2 detected %s intent with data %s.",
                equipment["intent"],
                equipment["data"],
            )
            return equipment

        combat = self._detect_combat_command(sanitized)
        if combat is not None:
            logger.info(
                "NLPCommandParserV2 detected %s intent with data %s.",
                combat["intent"],
                combat["data"],
            )
            return combat

        stealth = self._detect_stealth_command(sanitized)
        if stealth is not None:
            logger.info(
                "NLPCommandParserV2 detected %s intent with data %s.",
                stealth["intent"],
                stealth["data"],
            )
            return stealth

        reload_cmd = self._detect_weapon_maintenance(sanitized)
        if reload_cmd is not None:
            logger.info(
                "NLPCommandParserV2 detected %s intent with data %s.",
                reload_cmd["intent"],
                reload_cmd["data"],
            )
            return reload_cmd

        system_intent = self._detect_system_command(tokens)
        if system_intent:
            logger.info("NLPCommandParserV2 detected %s system intent.", system_intent)
            return {"intent": system_intent, "data": {}}

        direction = self._detect_direction(tokens)
        if direction:
            logger.info(f"NLPCommandParserV2 detected MOVE intent toward '{direction}'.")
            return {"intent": "MOVE", "data": {"direction": direction}}

        observation = self._detect_observation(sanitized)
        if observation is not None:
            logger.info(f"NLPCommandParserV2 detected LOOK intent with data {observation}.")
            return {"intent": "LOOK", "data": observation}

        access = self._detect_access_command(sanitized)
        if access is not None:
            logger.info(
                "NLPCommandParserV2 detected {} intent with data {}.",
                access["intent"],
                access["data"],
            )
            return access

        inventory = self._detect_inventory(sanitized)
        if inventory is not None:
            logger.info(
                "NLPCommandParserV2 detected {} intent with data {}.",
                inventory["intent"],
                inventory["data"],
            )
            return inventory

        logger.debug(f"NLPCommandParserV2 returning UNKNOWN for input: {text!r}")
        return {"intent": "UNKNOWN", "data": {}}

    @staticmethod
    def _sanitize_text(text: str) -> str:
        lowered = text.lower()
        stripped = re.sub(r"[^a-z\s]", " ", lowered)
        collapsed = re.sub(r"\s+", " ", stripped).strip()
        return collapsed

    def _tokens_without_fillers(self, sanitized: str) -> list[str]:
        tokens = sanitized.split()
        return [tok for tok in tokens if tok not in FILLER_WORDS]

    def _detect_direction(self, tokens: list[str]) -> str | None:
        if not tokens:
            return None

        # Direction alone
        if len(tokens) == 1 and tokens[0] in DIRECTION_MAP:
            return DIRECTION_MAP[tokens[0]]

        # Verb + direction
        if len(tokens) >= 2 and tokens[0] in MOVEMENT_VERBS and tokens[1] in DIRECTION_MAP:
            return DIRECTION_MAP[tokens[1]]

        return None

    def _detect_observation(self, sanitized: str) -> Dict[str, str] | None:
        if not sanitized:
            return None

        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        if verb not in OBSERVATION_VERBS:
            return None

        remainder = tokens[1:]
        if verb == "check" and not remainder:
            return None
        if not remainder:
            return {"scope": "room"}

        if remainder[0] == "around":
            return {"scope": "room"}

        if remainder[0] == "at":
            remainder = remainder[1:]

        trimmed = self._trim_leading_fillers(remainder)
        if not trimmed:
            return {"scope": "room"}

        target = " ".join(trimmed)
        return {"target": target}

    @staticmethod
    def _trim_leading_fillers(tokens: list[str]) -> list[str]:
        trimmed = list(tokens)
        while trimmed and trimmed[0] in FILLER_WORDS:
            trimmed.pop(0)
        return trimmed

    def _detect_system_command(self, tokens: list[str]) -> str | None:
        for token in tokens:
            mapped = SYSTEM_COMMANDS.get(token)
            if mapped:
                return mapped
        return None

    def _detect_access_command(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        remainder = tokens[1:]

        if verb in OPEN_VERBS:
            target = self._build_target_phrase(remainder)
            if target:
                return {"intent": "OPEN", "data": {"target": target}}
            return None

        if verb in CLOSE_VERBS:
            target = self._build_target_phrase(remainder)
            if target:
                return {"intent": "CLOSE", "data": {"target": target}}
            return None

        if verb in LOCK_VERBS:
            lock_data = self._build_lock_unlock_payload(remainder)
            if lock_data:
                return {"intent": "LOCK", "data": lock_data}
            return None

        if verb in UNLOCK_VERBS:
            unlock_data = self._build_lock_unlock_payload(remainder)
            if unlock_data:
                return {"intent": "UNLOCK", "data": unlock_data}
            return None

        return None

    def _detect_social_command(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        remainder = tokens[1:]

        if verb in SOCIAL_TALK_VERBS:
            npc_tokens = self._strip_leading_tokens(remainder, SOCIAL_TALK_PREPOSITIONS)
            npc = self._build_social_entity(npc_tokens)
            if npc:
                return {"intent": "TALK", "data": {"npc": npc}}
            return None

        if verb == SOCIAL_ASK_VERB:
            if not remainder:
                return None
            tokens_no_articles = self._strip_articles(list(remainder))
            if not tokens_no_articles:
                return None
            if "about" in tokens_no_articles:
                idx = tokens_no_articles.index("about")
                npc_tokens = tokens_no_articles[:idx]
                topic_tokens = tokens_no_articles[idx + 1 :]
            else:
                if len(tokens_no_articles) < 2:
                    return None
                npc_tokens = tokens_no_articles[:1]
                topic_tokens = tokens_no_articles[1:]
            npc = self._build_social_entity(npc_tokens)
            topic_tokens = self._strip_articles(list(topic_tokens))
            if not npc or not topic_tokens:
                return None
            return {
                "intent": "ASK",
                "data": {"npc": npc, "topic": " ".join(topic_tokens)},
            }

        if verb in {SOCIAL_GIVE_VERB, SOCIAL_SHOW_VERB}:
            if "to" not in remainder or len(remainder) < 3:
                return None
            idx = remainder.index("to")
            object_phrase = self._build_social_entity(remainder[:idx])
            npc_phrase = self._build_social_entity(remainder[idx + 1 :])
            if not object_phrase or not npc_phrase:
                return None
            intent_label = "GIVE" if verb == SOCIAL_GIVE_VERB else "SHOW"
            return {
                "intent": intent_label,
                "data": {"object": object_phrase, "npc": npc_phrase},
            }

        return None

    def _detect_read_or_scan(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None
        verb = tokens[0]
        if verb in READ_VERBS:
            target_tokens = tokens[1:]
            if not target_tokens or target_tokens[0] in READ_SCAN_INVALID_PREFIXES:
                return None
            target = self._build_social_entity(target_tokens)
            if target:
                return {"intent": "READ", "data": {"target": target}}
            return None
        if verb in SCAN_VERBS:
            target_tokens = tokens[1:]
            if not target_tokens or target_tokens[0] in READ_SCAN_INVALID_PREFIXES:
                return None
            target = self._build_social_entity(target_tokens)
            if target:
                return {"intent": "SCAN", "data": {"target": target}}
            return None
        return None

    def _detect_equipment_command(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        remainder = tokens[1:]

        if verb in EQUIP_VERBS:
            return self._build_equipment_payload("EQUIP", verb, remainder)
        if verb in UNEQUIP_VERBS:
            return self._build_equipment_payload("UNEQUIP", verb, remainder)
        if verb in WEAR_VERBS:
            return self._build_equipment_payload("WEAR", verb, remainder)
        if verb in REMOVE_VERBS:
            return self._build_equipment_payload("REMOVE", verb, remainder)
        if verb in WIELD_VERBS:
            return self._build_equipment_payload("WIELD", verb, remainder)
        return None

    def _detect_inventory(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        take_object = self._match_take(tokens)
        if take_object:
            return {"intent": "TAKE", "data": {"object": take_object}}

        drop_object = self._match_drop(tokens)
        if drop_object:
            return {"intent": "DROP", "data": {"object": drop_object}}

        put_payload = self._match_put(tokens)
        if put_payload:
            return {"intent": "PUT", "data": put_payload}

        return None

    def _match_take(self, tokens: list[str]) -> str | None:
        object_tokens: list[str] | None = None

        if len(tokens) >= 2 and tuple(tokens[:2]) == TAKE_TWO_WORD_VERB:
            object_tokens = tokens[2:]
        elif tokens and tokens[0] == TAKE_VERB:
            object_tokens = tokens[1:]

        if not object_tokens:
            return None

        cleaned = self._strip_articles(object_tokens)
        if not cleaned:
            return None

        return " ".join(cleaned)

    def _match_drop(self, tokens: list[str]) -> str | None:
        if not tokens or tokens[0] != DROP_VERB:
            return None

        cleaned = self._strip_articles(tokens[1:])
        if not cleaned:
            return None
        return " ".join(cleaned)

    def _match_put(self, tokens: list[str]) -> Dict[str, str] | None:
        if not tokens or tokens[0] != PUT_VERB:
            return None

        remainder = tokens[1:]
        if not remainder:
            return None

        prep_index = None
        for idx, token in enumerate(remainder):
            if token in PUT_PREPOSITIONS:
                prep_index = idx
                break

        if prep_index is None:
            return None

        object_tokens = self._strip_articles(remainder[:prep_index])
        container_tokens = self._strip_articles(remainder[prep_index + 1 :])

        if not object_tokens or not container_tokens:
            return None

        return {
            "object": " ".join(object_tokens),
            "container": " ".join(container_tokens),
            "preposition": remainder[prep_index],
        }

    @staticmethod
    def _strip_articles(tokens: list[str]) -> list[str]:
        return [tok for tok in tokens if tok not in ARTICLE_WORDS]

    @staticmethod
    def _strip_leading_tokens(tokens: list[str], removals: set[str]) -> list[str]:
        trimmed = list(tokens)
        while trimmed and trimmed[0] in removals:
            trimmed.pop(0)
        return trimmed

    def _build_social_entity(self, tokens: list[str]) -> str | None:
        cleaned_tokens = self._strip_articles(tokens)
        if not cleaned_tokens:
            return None
        phrase = " ".join(cleaned_tokens)
        if phrase in PRONOUN_BLOCKLIST:
            return None
        return phrase

    def _build_equipment_payload(
        self, intent_label: str, verb: str, tokens: list[str]
    ) -> Dict[str, Any] | None:
        if not tokens or tokens[0] in EQUIP_INVALID_PREFIXES:
            return None
        item = self._build_social_entity(tokens)
        if not item:
            return None
        return {"intent": intent_label, "data": {"target": item, "action": verb}}

    def _detect_combat_command(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        remainder = tokens[1:]

        if verb in ATTACK_VERBS:
            if remainder and remainder[0] in COMBAT_INVALID_PREFIXES:
                return None
            target = self._build_social_entity(remainder)
            if remainder and not target:
                return None
            data: Dict[str, Any] = {}
            if target:
                data["target"] = target
            return {"intent": "ATTACK", "data": data}

        if verb in AIM_VERBS:
            if remainder and remainder[0] in COMBAT_INVALID_PREFIXES:
                return None
            aim_target = self._build_social_entity(remainder)
            if remainder and not aim_target:
                return None
            data: Dict[str, Any] = {}
            if aim_target:
                data["target"] = aim_target
            return {"intent": "AIM", "data": data}

        if verb in SHOOT_VERBS:
            weapon_tokens: list[str] = []
            target_tokens: list[str] = []
            if "at" in remainder:
                idx = remainder.index("at")
                weapon_tokens = remainder[:idx]
                target_tokens = remainder[idx + 1 :]
                if not weapon_tokens or not target_tokens:
                    return None
            else:
                if verb == "fire":
                    weapon_tokens = remainder
                else:
                    target_tokens = remainder
            weapon = self._build_social_entity(weapon_tokens) if weapon_tokens else None
            target = self._build_social_entity(target_tokens) if target_tokens else None
            if weapon_tokens and not weapon:
                return None
            if target_tokens and not target:
                return None
            if not weapon and not target:
                return None
            data: Dict[str, Any] = {}
            if weapon:
                data["weapon"] = weapon
            if target:
                data["target"] = target
            return {"intent": "SHOOT", "data": data}

        if verb in BLOCK_VERBS:
            return {"intent": "BLOCK", "data": {}}

        if verb in DODGE_VERBS:
            return {"intent": "DODGE", "data": {}}

        if verb in FLEE_SINGLE_VERBS or any(
            len(tokens) >= 2 and tuple(tokens[:2]) == pattern for pattern in FLEE_MULTI
        ):
            return {"intent": "FLEE", "data": {}}

        return None

    def _detect_weapon_maintenance(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        remainder = tokens[1:]

        if verb in RELOAD_VERBS:
            if not remainder:
                return None
            if verb == "load":
                if remainder == ["game"]:
                    return None
                if remainder == ["save"]:
                    return None
            weapon_tokens = []
            ammo_tokens: list[str] = []
            if "with" in remainder:
                idx = remainder.index("with")
                weapon_tokens = remainder[:idx]
                ammo_tokens = remainder[idx + 1 :]
                if not weapon_tokens:
                    return None
            else:
                weapon_tokens = remainder

            weapon = self._build_social_entity(weapon_tokens)
            ammo = self._build_social_entity(ammo_tokens) if ammo_tokens else None
            if not weapon:
                return None
            return {
                "intent": "RELOAD",
                "data": {"weapon": weapon, "ammo": ammo} if ammo else {"weapon": weapon},
            }

        if verb in UNLOAD_VERBS:
            if not remainder or remainder[0] in UNLOAD_INVALID_PREFIXES:
                return None
            weapon = self._build_social_entity(remainder)
            if not weapon:
                return None
            return {"intent": "UNLOAD", "data": {"weapon": weapon}}

        if verb in CHECK_VERBS:
            if not remainder:
                return None
            target = self._build_social_entity(remainder)
            if not target or target == "door":
                return None
            return {"intent": "CHECK", "data": {"target": target}}

        return None

    def _detect_stealth_command(self, sanitized: str) -> Dict[str, Any] | None:
        tokens = sanitized.split()
        if not tokens:
            return None

        verb = tokens[0]
        remainder = tokens[1:]

        if verb in SNEAK_VERBS:
            if remainder:
                return None
            return {"intent": "SNEAK", "data": {}}

        if verb in HIDE_VERBS:
            if remainder:
                return None
            return {"intent": "HIDE", "data": {}}

        if verb in PICKPOCKET_VERBS:
            if not remainder:
                return None
            npc = self._build_social_entity(remainder)
            if not npc:
                return None
            return {"intent": "PICKPOCKET", "data": {"npc": npc}}

        if verb in DISARM_VERBS:
            if not remainder:
                return None
            trap = self._build_social_entity(remainder)
            if not trap:
                return None
            return {"intent": "DISARM_TRAP", "data": {"trap": trap}}

        return None

    def _build_target_phrase(self, tokens: list[str]) -> str | None:
        cleaned = self._strip_articles(tokens)
        if not cleaned:
            return None
        return " ".join(cleaned)

    def _build_lock_unlock_payload(self, tokens: list[str]) -> Dict[str, str] | None:
        if not tokens:
            return None

        try:
            delimiter_index = tokens.index(TOOL_DELIMITER)
        except ValueError:
            delimiter_index = -1

        if delimiter_index >= 0:
            object_tokens = tokens[:delimiter_index]
            tool_tokens = tokens[delimiter_index + 1 :]
        else:
            object_tokens = tokens
            tool_tokens: list[str] = []

        target = self._build_target_phrase(object_tokens)
        if not target:
            return None

        payload: Dict[str, str] = {"target": target}
        tool_phrase = self._build_target_phrase(tool_tokens)
        if tool_phrase:
            payload["tool"] = tool_phrase
        return payload
READ_VERBS = {"read"}
SCAN_VERBS = {"scan"}
