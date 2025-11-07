#!/usr/bin/env python3
"""
Starship Adventure 2 - Main Entry Point
A sci-fi text adventure game with a GUI interface.
"""

import sys
from pathlib import Path

import pygame
from loguru import logger

# Set up logging
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

# Remove default logger to avoid duplicate console output if script is re-run in some envs
logger.remove()

# File logger - logs everything at DEBUG level and above
logger.add(
    log_path / "game_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8"
)

# Console logger - logs INFO level and above for a cleaner terminal
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

class Game:
    """Main game class that handles the game loop and state."""
    
    def __init__(self):
        """Initialize the game."""
        logger.info("Initializing Starship Adventure 2")
        
        # Initialize Pygame
        pygame.init()
        
        # Set up the display
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Starship Adventure 2")
        
        # Set up colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        
        # Set up the game clock
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        
        logger.info("Game initialized successfully")
    
    def handle_events(self):
        """Handle game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update(self):
        """Update game state."""
        pass  # We'll add game logic here later
    
    def draw(self):
        """Draw the game screen."""
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Draw a simple welcome message
        font = pygame.font.Font(None, 36)
        text = font.render("Welcome to Starship Adventure 2!", True, self.WHITE)
        text_rect = text.get_rect(center=(self.screen_width/2, self.screen_height/2))
        self.screen.blit(text, text_rect)
        
        # Update the display
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        logger.info("Starting game loop")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS
        
        logger.info("Game loop ended")
        pygame.quit()
        sys.exit()

def main():
    """Main entry point."""
    try:
        game = Game()
        game.run()
    except Exception as e:
        logger.error(f"Game crashed: {e}")
        raise

if __name__ == "__main__":
    main() 