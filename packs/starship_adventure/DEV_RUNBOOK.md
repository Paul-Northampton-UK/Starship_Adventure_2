# Developer Runbook (Kid Mode)

## 1) Open the project
Open VSCode → open the Starship folder.

## 2) Turn on your virtual toolbox (venv)
Terminal → run:
.\.venv\Scripts\activate
(You should see (.venv) at the start of the line.)

## 3) Install/repair tools (only if needed)
pip install -r requirements.txt

## 4) Run the robot tests
pytest -q

## 5) Run the game
python -m engine.game_loop

## 6) Run the Designer (the editor)
python -m tools.main_design_hub

## 7) If something explodes
- Make sure you’re in the venv  
- Make sure YAML files are UTF-8  
- Run tests again  
- Ask ChatGPT for the next tiny step