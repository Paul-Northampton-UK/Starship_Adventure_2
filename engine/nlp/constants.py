"""Constants used by the NLP command parser."""

from ..command_defs import CommandIntent # Adjust import path relative to this new location

# Define verb patterns for each intent
VERB_PATTERNS = {
    CommandIntent.MOVE: {
        "verbs": ["go", "walk", "run", "move", "head", "travel", "n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw", "float", "drift"],
        "context_words": ["to", "towards", "into", "through", "north", "south", "east", "west", "up", "down", "northeast", "northwest", "southeast", "southwest", "forward", "backward",
                        "corridor", "hallway", "airlock", "hatch", "vent", "tunnel", "passage", "bridge", "cargo bay", "engineering"],
        "priority": 70
    },
    CommandIntent.LOOK: {
        "verbs": ["look", "l", "examine", "ex", "inspect", "check", "survey"],
        "context_words": ["at", "around", "room", "area", "location", "object", "item", "person", "creature",
                        "console", "panel", "display", "screen", "monitor", "hologram", "terminal", "device"],
        "priority": 65
    },
    CommandIntent.INVENTORY: {
        "verbs": ["inventory", "inv", "i", "items", "stuff", "equipment", "gear", "loadout", "cargo"],
        "context_words": ["carrying", "holding", "wearing", "wielding", "equipped", "stored", "packed", "loaded"],
        "priority": 60
    },
    CommandIntent.QUIT: {
        "verbs": ["quit", "exit", "q", "leave", "logout", "disconnect", "end"],
        "context_words": ["game", "program", "system", "session"],
        "priority": 100
    },
    CommandIntent.HELP: {
        "verbs": ["help", "h", "?", "assist", "guide", "tutorial", "manual", "info", "information"],
        "context_words": ["how", "what", "where", "when", "why", "commands", "controls", "interface"],
        "priority": 50
    },
    CommandIntent.COMMUNICATE: {
        "verbs": ["talk", "speak", "chat", "converse", "contact", "hail", "transmit", "broadcast", "say"],
        "context_words": ["to", "with", "at", "npc", "person", "creature", "alien", "robot", "android", "ai", "computer",
                        "comm", "radio", "intercom", "transmitter", "receiver", "channel", "frequency"],
        "priority": 75
    },
    CommandIntent.COMBAT: {
        "verbs": ["attack", "fight", "hit", "strike", "shoot", "fire", "blast", "discharge", "engage", "neutralize", "kill"],
        "context_words": ["with", "using", "enemy", "monster", "weapon", "sword", "axe", "bow", "target", "opponent", "foe", "creature",
                        "phaser", "blaster", "laser", "pulse", "beam", "alien", "robot", "android", "drone", "hostile", "threat"],
        "priority": 90
    },
    CommandIntent.SEARCH: {
        "verbs": ["search", "find", "locate", "seek", "probe", "detect", "discover", "track"],
        "context_words": ["for", "room", "area", "chest", "key", "item", "object", "person", "creature",
                        "console", "panel", "terminal", "device", "data", "information", "signal", "lifeform", "artifact",
                        "radiation", "energy", "heat", "anomaly", "signature", "frequency", "emission"],
        "priority": 80
    },
    CommandIntent.MANIPULATE: {
        "verbs": ["open", "close", "push", "pull", "turn", "press", "activate", "deactivate", "engage", "disengage",
                 "weld", "repair", "fix", "hack", "override", "bypass", "jump", "modify", "adjust", "calibrate"],
        "context_words": ["door", "chest", "box", "window", "button", "lever", "key", "card", "torch", "computer", "terminal", "screen",
                        "panel", "console", "switch", "control", "hatch", "airlock", "gate", "valve", "circuit", "system"],
        "priority": 85
    },
    CommandIntent.LOCK: {
        "verbs": ["lock"],
        "context_words": ["with", "using", "door", "chest", "box", "locker", "container", "gate", "safe"],
        "priority": 88
    },
    CommandIntent.UNLOCK: {
        "verbs": ["unlock"],
        "context_words": ["with", "using", "door", "chest", "box", "locker", "container", "gate", "safe", "key", "keycard", "card", "code"],
        "priority": 88
    },
    CommandIntent.CLIMB: {
        "verbs": ["climb", "jump", "crawl", "swim", "hover", "fly", "launch", "land"],
        "context_words": ["ladder", "wall", "rope", "gap", "fence", "pit", "tunnel", "vent", "pipe", "space",
                        "platform", "catwalk", "shaft", "conduit", "grav shaft", "elevator", "lift", "jetpack", "thruster"],
        "priority": 75
    },
    CommandIntent.SOCIAL: {
        "verbs": ["give", "show", "trade", "follow", "greet", "salute", "wave", "gesture", "signal"],
        "context_words": ["to", "for", "with", "item", "sword", "key", "potion", "map", "badge", "document", "picture",
                        "credits", "data", "information", "artifact", "device", "tool", "weapon", "equipment", "supplies"],
        "priority": 70
    },
    CommandIntent.ENVIRONMENT: {
        "verbs": ["dig", "cut", "burn", "pour", "light", "extinguish", "fill", "break", "smash", "destroy", "shatter"],
        "context_words": ["with", "using", "into", "onto", "hole", "rope", "torch", "fire", "wall", "door", "window", "box",
                        "object", "item", "glass", "wood", "stone", "metal", "circuit", "panel", "console", "terminal",
                        "system", "device", "equipment", "machinery", "power", "energy", "shield", "barrier"],
        "priority": 85
    },
    CommandIntent.GATHER_INFO: {
        "verbs": ["read", "listen", "smell", "touch", "taste", "study", "scan", "analyze", "monitor"],
        "context_words": ["book", "sign", "note", "scroll", "sound", "music", "noise", "conversation", "food", "flower",
                        "smoke", "potion", "wall", "surface", "object", "material", "data", "information", "signal",
                        "display", "screen", "terminal", "console", "hologram", "sensor", "scanner", "detector"],
        "priority": 75
    },
    CommandIntent.EQUIP: {
        "verbs": ["equip", "wear", "remove", "unequip", "wield", "hold", "power", "charge"],
        "context_words": ["sword", "armor", "shield", "weapon", "helmet", "boots", "gloves", "ring", "tool", "device",
                        "phaser", "blaster", "laser", "suit", "armor", "shield", "generator", "battery", "power pack",
                        "jetpack", "thruster", "scanner", "communicator", "medkit", "toolkit"],
        "priority": 80
    },
    CommandIntent.TIME: {
        "verbs": ["wait", "rest", "sleep", "pause", "meditate", "nap", "stop", "delay", "standby"],
        "context_words": ["for", "until", "while", "briefly", "moment", "time", "cycle", "rotation", "orbit", "period"],
        "priority": 80
    },
    CommandIntent.COMPLEX: {
        "verbs": ["combine", "craft", "build", "create", "construct", "forge", "brew", "synthesize", "fabricate", "assemble"],
        "context_words": ["items", "ingredients", "parts", "materials", "potion", "tool", "weapon", "armor", "shelter",
                        "bridge", "wall", "structure", "device", "machine", "equipment", "circuit", "component",
                        "module", "system", "device", "artifact", "technology", "power", "energy", "shield"],
        "priority": 95
    },
    CommandIntent.TAKE: {
        "verbs": ["take", "grab", "pick", "get", "collect", "acquire", "obtain", "recover", "hold"],
        "context_words": ["up", "item", "object", "torch", "key", "sword", "potion", "book", "scroll", "map", "coin", "gem",
                        "phaser", "blaster", "laser", "tool", "device", "data pad", "access card", "credits", "artifact"],
        "priority": 85
    },
    CommandIntent.DROP: {
        "verbs": ["drop", "put"],
        "context_words": ["down", "item", "object", "backpack", "key", "datapad"],
        "priority": 35
    },
    CommandIntent.PUT: {
        "verbs": ["put", "place", "store", "insert", "stow"],
        "context_words": ["in", "into", "inside", "on", "onto", "backpack", "box", "container", "locker", "chest", "cabinet"],
        "priority": 86
    },
    CommandIntent.TAKE_FROM: {
        "verbs": ["take", "get", "retrieve", "remove", "extract", "withdraw"],
        "context_words": ["from", "out", "inside", "backpack", "box", "container", "locker", "chest", "cabinet"],
        "priority": 87
    },
    "use": {CommandIntent.MANIPULATE: 80},
    "activate": {CommandIntent.MANIPULATE: 80},
    "push": {CommandIntent.MANIPULATE: 70},
    "pull": {CommandIntent.MANIPULATE: 70},
    "turn": {CommandIntent.MANIPULATE: 70},
    "press": {CommandIntent.MANIPULATE: 70},
    "open": {CommandIntent.MANIPULATE: 85},
    "close": {CommandIntent.MANIPULATE: 85},
    "lock": {CommandIntent.MANIPULATE: 50, CommandIntent.LOCK: 90},
    "unlock": {CommandIntent.MANIPULATE: 50, CommandIntent.UNLOCK: 90},
    "read": {CommandIntent.GATHER_INFO: 85}
}

# Define intent priorities (higher number = higher priority)
INTENT_PRIORITIES = {
    CommandIntent.COMBAT: 100,
    CommandIntent.COMPLEX: 95,
    CommandIntent.EQUIP: 90,
    CommandIntent.MANIPULATE: 85,
    CommandIntent.PUT: 86,
    CommandIntent.TAKE_FROM: 87,
    CommandIntent.ENVIRONMENT: 80,
    CommandIntent.CLIMB: 75,
    CommandIntent.SOCIAL: 70,
    CommandIntent.GATHER_INFO: 65,
    CommandIntent.SEARCH: 60,
    CommandIntent.COMMUNICATE: 55,
    CommandIntent.LOOK: 50,
    CommandIntent.MOVE: 45,
    CommandIntent.TAKE: 85,
    CommandIntent.DROP: 35,
    CommandIntent.USE: 30,
    CommandIntent.TIME: 25,
    CommandIntent.INVENTORY: 20,
    CommandIntent.QUIT: 15,
    CommandIntent.HELP: 10,
    CommandIntent.UNKNOWN: -1,
    CommandIntent.LOCK: 88,
    CommandIntent.UNLOCK: 88
}

# Define context words for each intent (optional, used for scoring refinement)
CONTEXT_WORDS = {
    CommandIntent.COMBAT: ["enemy", "target", "weapon", "fight", "battle", "attack", "alien", "monster", "position", "opponent", "foe", "creature", "beast"],
    CommandIntent.EQUIP: ["armor", "weapon", "helmet", "shield", "gear", "equipment", "sword", "staff", "boots", "gloves", "ring", "amulet", "cloak", "bow", "dagger", "axe"],
    CommandIntent.MANIPULATE: ["door", "window", "chest", "light", "lever", "button", "switch", "lock", "panel", "gate", "lid", "hatch", "valve", "box", "cabinet", "safe"],
    CommandIntent.COMPLEX: ["items", "potion", "shelter", "device", "tool", "craft", "materials", "ingredients", "components", "recipe", "blueprint", "formula", "mixture", "weapon", "armor"],
    CommandIntent.ENVIRONMENT: ["hole", "rope", "paper", "water", "fire", "ground", "dirt", "wall", "tree", "rock", "bush", "plant", "torch"],
    CommandIntent.CLIMB: ["ladder", "gap", "tunnel", "river", "wall", "cliff", "mountain", "tree", "rope", "stairs", "platform", "ledge", "bridge", "fence", "pit"],
    CommandIntent.SOCIAL: ["merchant", "guide", "npc", "person", "character", "ally", "item", "map", "friend", "companion", "trader", "villager", "guard", "sword", "key"],
    CommandIntent.GATHER_INFO: ["book", "music", "flowers", "wall", "text", "sign", "sound", "smell", "scroll", "note", "letter", "inscription", "writing", "noise", "conversation"],
    CommandIntent.SEARCH: ["room", "key", "area", "noise", "clue", "evidence", "place", "location", "spot", "corner", "chest", "container", "box", "tunnel", "drawer"],
    CommandIntent.COMMUNICATE: ["npc", "captain", "mission", "story", "quest", "dialogue", "person", "guard", "merchant", "villager", "companion", "friend", "ally"],
    CommandIntent.PUT: ["container", "box", "locker", "backpack", "chest", "shelf", "cabinet"],
    CommandIntent.TAKE_FROM: ["container", "box", "locker", "backpack", "chest", "shelf", "cabinet"]
}

# Add other constants here if needed, e.g., the valid_words set could potentially move here
# Or the direction list from _populate_custom_patterns 