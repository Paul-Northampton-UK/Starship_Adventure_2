# tools/main_design_hub.py
import sys
from pathlib import Path

import customtkinter as ctk
from loguru import logger

# --- Add project root to Python path ---
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import subprocess
import threading
import tkinter.messagebox as messagebox
from pathlib import Path

from engine import active_pack
from engine.active_pack import get_content_root_from_config
from engine.validate_pack import validate_pack
from tools.object_editor.new_ctk_object_editor import NewObjectEditorFrame
from tools import pack_discovery


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
            "Game Library": self.create_game_library_tab,
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

    # Game Library UI -----------------------------------------------------
    def create_game_library_tab(self, tab, tool_name):
        """Create the simplified Game Library pane."""
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkLabel(frame, text="Game Library", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=(0, 10))

        info_frame = ctk.CTkFrame(frame)
        info_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(info_frame, text="Active Pack:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.active_pack_var = ctk.StringVar(value=active_pack.get_active_pack())
        ctk.CTkLabel(info_frame, textvariable=self.active_pack_var).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        list_frame = ctk.CTkFrame(frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(list_frame, text="Available Packs").pack(anchor="w", padx=6, pady=4)
        self.pack_list = ctk.CTkTextbox(list_frame, height=200)
        self.pack_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Refresh Packs", command=self.refresh_packs).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="Set Active", command=self.set_selected_pack).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="Validate Pack", command=self.validate_selected_pack).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkButton(btn_frame, text="Run Engine", command=self.run_engine).grid(row=0, column=3, padx=5, pady=5)

        self.log_area = ctk.CTkTextbox(frame, height=120)
        self.log_area.pack(fill="x", padx=10, pady=10)

        self.refresh_packs()

    # Actions --------------------------------------------------------------
    def _discover_packs(self):
        return pack_discovery.list_packs()

    def refresh_packs(self):
        packs = self._discover_packs()
        self.pack_list.configure(state="normal")
        self.pack_list.delete("1.0", "end")
        for name in packs:
            self.pack_list.insert("end", f"{name}\n")
        self.pack_list.configure(state="disabled")
        self.active_pack_var.set(active_pack.get_active_pack())

    def _selected_pack(self):
        try:
            selection = self.pack_list.get("sel.first", "sel.last").strip()
            return selection
        except Exception:
            return None

    def set_selected_pack(self):
        pack = self._selected_pack()
        if not pack:
            messagebox.showwarning("Set Active Pack", "Select a pack first.")
            return
        try:
            active_pack.set_active_pack(pack)
        except Exception as exc:
            messagebox.showerror("Set Active Pack", str(exc))
            return
        self.active_pack_var.set(pack)
        messagebox.showinfo("Set Active Pack", f"Active pack set to {pack}")

    def validate_selected_pack(self):
        pack = self._selected_pack() or active_pack.get_active_pack()
        content_root = Path("packs") / pack
        if not content_root.is_dir():
            messagebox.showerror("Validate Pack", f"Pack not found: {pack}")
            return
        result = validate_pack(content_root, return_warnings=True)
        errors, warnings = result if isinstance(result, tuple) else (result, [])
        msg = f"{pack} validation:\nErrors: {len(errors)}\nWarnings: {len(warnings)}"
        detail_lines = errors[:5] + warnings[:5]
        detail = "\n".join(detail_lines) if detail_lines else "No messages."
        messagebox.showinfo("Validate Pack", f"{msg}\n\n{detail}")

    def run_engine(self):
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "engine.game_loop"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except Exception as exc:
            messagebox.showerror("Run Engine", str(exc))
            return

        self.log_area.configure(state="normal")
        self.log_area.insert("end", "Starting engine...\n")
        self.log_area.configure(state="disabled")

        def _stream_output():
            assert process.stdout is not None
            for line in process.stdout:
                self.log_area.configure(state="normal")
                self.log_area.insert("end", line)
                self.log_area.see("end")
                self.log_area.configure(state="disabled")
            process.stdout.close()

        threading.Thread(target=_stream_output, daemon=True).start()

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
