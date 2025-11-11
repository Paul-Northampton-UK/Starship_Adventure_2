# Starship Adventure – Simple Project Guide

## What you're building
Two toys that work together:

1. **Designer:**  
   You click buttons → it builds rooms, objects, puzzles, and saves them as a “game pack”.

2. **Game Engine:**  
   It loads the game pack and lets you play the adventure.

## Where stuff lives
- `engine/` → The brain. Runs the game.
- `packs/<game>/` → Your actual game pieces (rooms, objects, responses).
- `packs/` → Default pieces shared by any game.
- `tools/` → The Designer and helpers.
- `tests/` → Robot quizzes that check everything still works.

## How to run things
- Run the game:  
  `python -m engine.game_loop`
- Run the Designer:  
  `python -m tools.main_design_hub`

## Big idea
Make ANY text adventure by clicking buttons.  
Designer builds the pack → Engine plays it.