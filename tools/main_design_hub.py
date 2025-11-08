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
import tkinter as tk

from engine import active_pack
from engine.content_root import get_content_root
from engine.active_pack import get_content_root_from_config
from engine.validate_pack import validate_pack
from tools import pack_discovery
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
        self.engine_process: subprocess.Popen[str] | None = None
        self.add_tool_tabs()
        self.root.bind("<Escape>", lambda event: self.stop_engine())
        self.root.bind("<Control-l>", lambda event: self.clear_console())

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
        list_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(list_frame, text="Available Packs").pack(anchor="w", padx=6, pady=4)
        list_container = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_container.pack(fill="x", padx=6, pady=(0, 6))
        self.pack_list = tk.Listbox(list_container, height=10, exportselection=False, bg="#1f1f1f", fg="#f2f2f2", highlightthickness=0, selectbackground="#365e9d", relief="flat")
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.pack_list.yview)
        self.pack_list.configure(yscrollcommand=scrollbar.set)
        self.pack_list.pack(side="left", fill="x", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ctk.CTkFrame(frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Refresh Packs", command=self.refresh_packs).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(btn_frame, text="Set Active", command=self.set_selected_pack).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(btn_frame, text="Validate Pack", command=self.validate_selected_pack).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.run_button = ctk.CTkButton(btn_frame, text="Run Engine", command=self.run_engine)
        self.run_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        self.stop_button = ctk.CTkButton(btn_frame, text="Stop", command=self.stop_engine, state="disabled")
        self.stop_button.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        console_frame = ctk.CTkFrame(frame)
        console_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ctk.CTkLabel(console_frame, text="Engine Console").pack(anchor="w", padx=6, pady=(6, 4))
        self.log_area = ctk.CTkTextbox(console_frame, height=260)
        self.log_area.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.log_area.configure(state="disabled")

        input_frame = ctk.CTkFrame(console_frame)
        input_frame.pack(fill="x", padx=6, pady=(0, 6))
        input_frame.columnconfigure(0, weight=1)
        self.command_entry = ctk.CTkEntry(input_frame)
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.command_entry.bind("<Return>", self.send_command)
        self.send_button = ctk.CTkButton(input_frame, text="Send", width=80, command=self.send_command)
        self.send_button.grid(row=0, column=1, padx=(0, 6))
        self.clear_button = ctk.CTkButton(input_frame, text="Clear", width=80, command=self.clear_console)
        self.clear_button.grid(row=0, column=2)
        self._toggle_command_input(False)

        self.refresh_packs()

    # Actions --------------------------------------------------------------
    def _discover_packs(self):
        return pack_discovery.list_packs(project_root / "packs")

    def refresh_packs(self):
        packs = self._discover_packs()
        self.pack_list.delete(0, "end")
        for name in packs:
            self.pack_list.insert("end", name)
        self.active_pack_var.set(active_pack.get_active_pack())
        self._log_status(f"Discovered {len(packs)} pack(s).")

    def _selected_pack(self):
        selection = self.pack_list.curselection()
        if not selection:
            return None
        return self.pack_list.get(selection[0])

    def _log_status(self, message: str):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", message + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _toggle_command_input(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.command_entry.configure(state=state)
        self.send_button.configure(state=state)
        if not enabled:
            self.command_entry.delete(0, "end")

    def set_selected_pack(self):
        pack = self._selected_pack()
        if not pack:
            self._log_status("Set Active: select a pack first.")
            return
        try:
            active_pack.set_active_pack(pack)
        except Exception as exc:
            self._log_status(f"Set Active failed: {exc}")
            return
        self.active_pack_var.set(pack)
        self._log_status(f"Active pack set to {pack}")

    def validate_selected_pack(self):
        selected = self._selected_pack()
        try:
            if selected:
                pack = selected
                content_root = get_content_root(pack)
            else:
                pack = active_pack.get_active_pack()
                content_root = get_content_root_from_config()
        except Exception as exc:
            self._log_status(f"Validate failed: {exc}")
            return
        result = validate_pack(content_root, return_warnings=True)
        errors, warnings = result if isinstance(result, tuple) else (result, [])
        self._log_status(f"Validate {pack}: {len(errors)} error(s), {len(warnings)} warning(s)")
        for line in (errors[:3] + warnings[:3]):
            self._log_status(f"  - {line}")

    def clear_console(self, *_):
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")

    def send_command(self, event=None):
        if not self.engine_process or self.engine_process.poll() is not None:
            self._log_status("Engine is not running.")
            return
        if not self.engine_process.stdin:
            self._log_status("Engine stdin unavailable.")
            return
        text = self.command_entry.get()
        if not text.strip():
            return
        try:
            self.engine_process.stdin.write(text + "\n")
            self.engine_process.stdin.flush()
        except Exception as exc:
            self._log_status(f"Send failed: {exc}")
            return
        finally:
            self.command_entry.delete(0, "end")

    def run_engine(self):
        if self.engine_process and self.engine_process.poll() is None:
            self._log_status("Engine already running.")
            return
        try:
            self.engine_process = subprocess.Popen(
                [sys.executable, "-m", "engine.game_loop"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            self._log_status(f"Run Engine failed: {exc}")
            self.engine_process = None
            return

        self._log_status("Engine started...")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._toggle_command_input(True)
        self.command_entry.focus_set()

        def _stream_output(proc: subprocess.Popen[str]):
            assert proc.stdout is not None
            for line in proc.stdout:
                self._log_status(line.rstrip())
            proc.stdout.close()
            self.root.after(0, self._on_engine_exit)

        threading.Thread(target=_stream_output, args=(self.engine_process,), daemon=True).start()

    def _on_engine_exit(self):
        proc = self.engine_process
        self.engine_process = None
        if proc and proc.stdin:
            try:
                proc.stdin.close()
            except Exception:
                pass
        self._log_status("Engine stopped.")
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._toggle_command_input(False)

    def stop_engine(self, *_):
        if not self.engine_process or self.engine_process.poll() is not None:
            self._log_status("Engine is not running.")
            return
        try:
            self.engine_process.terminate()
            self._log_status("Stopping engine...")
            threading.Thread(target=self._await_stop, args=(self.engine_process,), daemon=True).start()
        except Exception as exc:
            self._log_status(f"Stop failed: {exc}")

    def _await_stop(self, proc: subprocess.Popen[str]):
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
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
