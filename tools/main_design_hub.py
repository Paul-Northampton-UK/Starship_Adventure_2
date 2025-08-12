# tools/main_design_hub.py
import customtkinter as ctk
from loguru import logger
import sys
from pathlib import Path

# --- Add project root to Python path ---
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from tools.object_editor.new_ctk_object_editor import NewObjectEditorFrame

class GameDesignHub:
    """
    Main interface for non-technical game designers.
    Provides access to all design tools and game management.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Starship Adventure 2 - Game Design Hub")
        self.root.geometry("1200x800")

        self.object_editor_frame = None # To hold the reference


        # Set the main theme
        ctk.set_appearance_mode("Dark")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Create a container for the main content
        main_container = ctk.CTkFrame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a tab view
        self.tab_view = ctk.CTkTabview(main_container)
        self.tab_view.pack(fill="both", expand=True)

        # Add tabs for each tool
        self.add_tool_tabs()

    def add_tool_tabs(self):
        """Adds all the tool tabs to the main view."""
        tools = {
            "Game Library": self.create_placeholder_tab,
            "Room Editor": self.create_placeholder_tab,
            "Object Editor": self.create_object_editor_tab,
            "Puzzle Designer": self.create_placeholder_tab,
            "Dialogue System": self.create_placeholder_tab,
            "Response Editor": self.create_placeholder_tab,
        }

        for tool_name, creation_func in tools.items():
            tab = self.tab_view.add(tool_name)
            creation_func(tab, tool_name)

        # Normalize header widths across hub tabs
        self._normalize_tab_header_widths(self.tab_view, min_width=160)

    def _normalize_tab_header_widths(self, tabview, *, min_width: int = 140, label_padx: int = 10, label_pady: int = 6):
        """Force tab headers to have a consistent minimum width and padding (hub-wide)."""
        try:
            sb = tabview._segmented_button  # private access; safe fallback below
            buttons = getattr(sb, "_buttons_dict", None) or {}
            for _, segment_btn in buttons.items():
                segment_btn.configure(width=min_width)
            if hasattr(sb, "_label_padx"):
                sb._label_padx = label_padx
            if hasattr(sb, "_label_pady"):
                sb._label_pady = label_pady
            if hasattr(sb, "_update_dimensions_event"):
                sb._update_dimensions_event()
        except Exception:
            try:
                tab_names = getattr(tabview, "_name_list", []) or []
                tabview._segmented_button.configure(width=min_width * max(1, len(tab_names)))
            except Exception:
                pass

    def create_placeholder_tab(self, tab, tool_name):
        """Creates a placeholder UI for a tool tab."""
        label = ctk.CTkLabel(
            tab,
            text=f"{tool_name} Interface - Coming Soon!",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        label.pack(pady=20, padx=20)

        placeholder_text = (
            f"This is the placeholder for the {tool_name}.\\n"
            "Here you will be able to create, edit, and manage "
            f"all aspects of the game's {tool_name.lower().replace(' ', '_')}."
        )
        placeholder_label = ctk.CTkLabel(tab, text=placeholder_text, wraplength=400)
        placeholder_label.pack(pady=10, padx=20)

    def create_object_editor_tab(self, tab, tool_name):
        """Creates the object editor UI in its tab."""
        self.object_editor_frame = NewObjectEditorFrame(tab)
        self.object_editor_frame.pack(fill="both", expand=True)

    def on_closing(self):
        """Handle the window closing event."""
        logger.info("Design Hub is closing.")
        if self.object_editor_frame:
            self.object_editor_frame.shutdown()
        self.root.destroy()

def main():
    """Main entry point for the design hub."""
    try:
        root = ctk.CTk()
        app = GameDesignHub(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)  # Ensure clean exit
        root.mainloop()
    except Exception as e:
        logger.error(f"Design hub crashed: {e}")
        raise

if __name__ == "__main__":
    main()
