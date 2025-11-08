# Starship Adventure Engine â€“ Nonâ€‘Technical Overview

This document explains, in plain language, how the textâ€‘adventure engine works from start to finish. It covers how the engine starts up, how it understands commands you type, and how it hands off work to different parts of the code to produce a response.

## What the engine is

Think of the engine as a conductor. It loads the world data (rooms, objects, responses), keeps track of whatâ€™s going on (your location, items, object states), understands what you type, and then sends the request to the right specialist to do the job (move, look, open, take, etc.).

Key roles:
- Game data loader (reads YAML files)
- Game state tracker (where you are, what you carry, whatâ€™s open/locked)
- Command parser (understands your words)
- Command dispatcher (sends intent to the right handler)
- Response formatter (picks text to display)

## Highâ€‘level flow (from start to response)

1) Start the engine
- The engine starts a loop that displays the current location and waits for your input.

2) Load content
- It reads three YAML files: rooms, objects, and responses.
  - Rooms: locations and their descriptions (plus optional areas within a room)
  - Objects: items and their properties (takeable, openable, locked, etc.)
  - Responses: reusable message templates (friendly text snippets)

3) Initialize game state
- The engine records the starting room and the ship power state.
- It prepares placeholders for inventory, visited places, and perâ€‘object states (like whether a locker is open).

4) Initialize the parser
- The engine loads a small language model so it can recognize words, directions, and objects.
- It adds custom patterns so â€œnorthâ€, â€œgo northâ€, and â€œnorth westâ€ are understood as movement.

5) Main loop
- The engine waits for you to type a command, like â€œopen lockerâ€.
- It parses your text and decides what you meant (your intent), then sends it to the right specialist function.
- The specialist returns one or more messages. The engine formats those messages using the response templates and shows the final text to you.

## The main parts and what they do

- Game loop (engine/game_loop.py)
  - Orchestrates everything: loads files, starts the parser, maps intents to handler functions, shows output.
  - Keeps a â€œmapâ€ from intent (Move, Look, Take, etc.) to a specific handler.

- Game state (engine/game_state.py)
  - Tracks where you are (room and optional subâ€‘area), your inventory (held and worn), and object states (open/closed, locked/unlocked, visible/hidden).
  - Records visited rooms/areas and power state.

- Data loader (engine/yaml_loader.py)
  - Reads YAML files (rooms, objects, responses).
  - Normalizes rooms/objects into dictionaries keyed by their IDs for fast lookup.

- Command parser (engine/nlp_command_parser.py and engine/nlp/*)
  - Understands what you type using a small language model and custom patterns for directions and game terms.
  - Converts text into a Parsed Intent (e.g., INTENT: OPEN, TARGET: locker).

- Command handlers (engine/command_handlers/*)
  - Movement (movement.py): go north/east/etc., and describe where you arrive.
  - Basic commands (basic_commands.py): look, inventory, quit, unknown command.
  - Item actions (item_actions.py): take, drop, put an item into a container, take an item from a container.
  - Equipment (equipment.py): wear or remove items like boots or suits.
  - Search (search.py): search objects or areas to reveal things.
  - Open/Close (open_close_handler.py): open and close doors/containers that can be opened.
  - Lock/Unlock (locking.py): lock/unlock things if you have the right key/code.

- Response formatter
  - Handlers return message â€œkeysâ€ and data, like key: "open_success" with the object name.
  - The engine looks up the matching response template in responses.yaml and fills in any blanks (like the item name).

## A basic runâ€‘through (example)

1) Startup
- The engine reads settings (start room and power) and loads rooms, objects, and responses.
- It shows the first locationâ€™s description.

2) You type â€œnâ€ (for north)
- The parser recognizes this as a MOVE intent with direction "north".
- The game loop calls the movement handler, which checks if thereâ€™s an exit to the north and moves you.
- The handler returns a message key (like "move_success") and the new location description.
- The engine formats and prints: the room title, description, visible objects, and exits.

3) You type â€œopen lockerâ€
- The parser recognizes OPEN intent and the target object "locker".
- The game loop calls the open/close handler.
- The handler checks if the locker is openable and unlocked. If itâ€™s locked, it returns a â€œlockedâ€ message key; otherwise it changes the object state to open and returns â€œopen_successâ€.
- The engine formats the response and prints it.

4) You type â€œunlock lockerâ€
- The parser recognizes UNLOCK intent and target "locker".
- The game loop calls the locking handler.
- The handler verifies you have the correct key (based on object data). If you do, it unlocks the locker and returns "unlock_success". If not, it returns "unlock_fail".

5) You type â€œtake phaserâ€
- The parser recognizes TAKE intent and target "phaser".
- The game loop calls the item actions handler.
- The handler confirms the phaser is present and takeable, moves it into your hand/inventory, and returns "take_success".

6) You type â€œinventoryâ€ (or â€œiâ€)
- The parser recognizes INVENTORY intent.
- The game loop calls the basic commands handler to list what youâ€™re holding and wearing.

## How the engine chooses what to do (routing)

1) Parse
- Turn your text into a Parsed Intent: an intent type plus optional details (direction, target object ID).

2) Map intent to handler
- For example, OPEN -> open_close_handler, MOVE -> movement, TAKE -> item_actions, INVENTORY -> basic_commands.

3) Run the handler
- The handler reads/modifies game state and returns one or more message entries.

4) Format messages
- For each message entry, the engine looks up a response key in responses.yaml and fills in any placeholders.

5) Show the result
- The final text is printed for you to read.

## Where the data lives today (and the direction of travel)

- Today, files are read from the `packs/` folder.
- We are transitioning to â€œGame Packsâ€, where each pack has its own `rooms.yaml`, `objects.yaml`, and `responses.yaml` under `packs/<pack_id>/`.
- A central Hub will help you create/edit/validate/run packs and point the engine at the active pack.

## Why this design works well

- Clear separation of concerns: loading, state, parsing, handling, and formatting are distinct.
- Easy to add new commands: define a new intent and handler, then map it in the game loop.
- Contentâ€‘first: rooms, objects, and responses live in YAML, so content can grow without changing core code.



