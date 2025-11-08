"""Main Game Design Hub UI."""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import customtkinter as ctk
from loguru import logger

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from engine import active_pack  # noqa: E402
from engine.active_pack import (  # noqa: E402
    get_content_root_from_config,
    load_game_config,
    save_game_config,
)
from engine.content_root import get_content_root  # noqa: E402
from engine.validate_pack import validate_pack  # noqa: E402
from tools import pack_discovery  # noqa: E402
from tools.object_editor.new_ctk_object_editor import NewObjectEditorFrame  # noqa: E402
from tools.ui import layout, theme  # noqa: E402


class GameDesignHub(ctk.CTk):
    """CustomTkinter main window for the design hub."""

    def __init__(self) -> None:
        super().__init__()
        theme.apply_theme(self)
        self.title("Starship Adventure 2 - Game Design Hub")
        self.minsize(1000, 650)
        self.resizable(True, True)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._zoom_steps = [80, 90, 100, 110, 125, 150]
        self._zoom = self._load_initial_zoom()
        ctk.set_widget_scaling(self._zoom / 100.0)

        self.font_base: ctk.CTkFont | None = None
        self.font_bold: ctk.CTkFont | None = None
        self.font_mono: ctk.CTkFont | None = None
        self._update_fonts()

        self.bind("<Control-plus>", self._zoom_in)
        self.bind("<Control-equal>", self._zoom_in)
        self.bind("<Control-minus>", self._zoom_out)
        self.bind("<Control-0>", self._zoom_reset)
        self.bind("<Control-l>", self.clear_console)
        self.bind("<Escape>", self.stop_engine)

        self.pack_var = ctk.StringVar(value="")
        self.active_pack_var = ctk.StringVar(value=active_pack.get_active_pack())
        self.zoom_var = ctk.StringVar(value=f"{self._zoom}%")

        self.engine_process: subprocess.Popen[str] | None = None
        self.object_editor_frame: NewObjectEditorFrame | None = None

        self._build_layout()
        self.refresh_packs()

    def _style_buttons(self, *buttons: ctk.CTkButton) -> None:
        for button in buttons:
            layout.style_button(button)

    # ------------------------------------------------------------------ UI setup
    def _build_layout(self) -> None:
        container = ctk.CTkFrame(self, fg_color=theme.CANVAS_BG)
        container.grid(row=1, column=0, sticky=layout.sticky_all(), **layout.pad())
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(container)
        self.tab_view.grid(row=0, column=0, sticky=layout.sticky_all())
        self._add_tabs()

    def _add_tabs(self) -> None:
        tabs: dict[str, Any] = {
            "Game Library": self._build_game_library_tab,
            "Room Editor": self._build_placeholder_tab,
            "Object Editor": self._build_object_editor_tab,
            "Puzzle Designer": self._build_placeholder_tab,
            "Dialogue System": self._build_placeholder_tab,
            "Response Editor": self._build_placeholder_tab,
        }
        for name, builder in tabs.items():
            tab = self.tab_view.add(name)
            builder(tab)

    def _build_placeholder_tab(self, tab: ctk.CTkFrame) -> None:
        tab.configure(fg_color=theme.PANEL_BG)
        label = ctk.CTkLabel(
            tab,
            text="Interface - Coming Soon!",
            font=self.font_bold,
            text_color=theme.TEXT_FG,
        )
        label.pack(**layout.pad())
        placeholder = ctk.CTkLabel(
            tab,
            text="This section is under construction.",
            wraplength=400,
            font=self.font_base,
            text_color=theme.MUTED_FG,
        )
        placeholder.pack(**layout.pad())

    def _build_object_editor_tab(self, tab: ctk.CTkFrame) -> None:
        self.object_editor_frame = NewObjectEditorFrame(tab)
        self.object_editor_frame.pack(fill="both", expand=True)

    def _build_game_library_tab(self, tab: ctk.CTkFrame) -> None:
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(tab, fg_color=theme.PANEL_BG)
        wrapper.grid(row=0, column=0, sticky=layout.sticky_all())
        wrapper.grid_rowconfigure(1, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(wrapper, fg_color=theme.PANEL_BG)
        header.grid(row=0, column=0, sticky="ew", padx=theme.PADDING, pady=(theme.PADDING, theme.GAP))
        header.grid_columnconfigure(0, weight=1)
        self.active_pack_label = ctk.CTkLabel(
            header,
            text=self._active_pack_text(),
            font=self.font_bold,
            text_color=theme.TEXT_FG,
        )
        self.active_pack_label.grid(row=0, column=0, sticky="w")

        zoom_values = [f"{value}%" for value in self._zoom_steps]
        self.zoom_menu = ctk.CTkOptionMenu(
            header,
            variable=self.zoom_var,
            values=zoom_values,
            command=self._on_zoom_select,
            width=110,
            fg_color=theme.ACCENT,
        )
        self.zoom_menu.grid(row=0, column=1, sticky="e")

        content = ctk.CTkFrame(wrapper, fg_color=theme.PANEL_BG)
        content.grid(row=1, column=0, sticky=layout.sticky_all(), padx=theme.PADDING, pady=(0, theme.PADDING))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)

        self.pack_list_frame = ctk.CTkScrollableFrame(content, fg_color=theme.PANEL_BG)
        self.pack_list_frame.grid(row=0, column=0, sticky=layout.sticky_all(), padx=(0, theme.GAP))

        console_container = ctk.CTkFrame(content, fg_color=theme.PANEL_BG)
        console_container.grid(row=0, column=1, sticky=layout.sticky_all(), padx=(theme.GAP, 0))
        console_container.grid_rowconfigure(1, weight=1)
        console_container.grid_columnconfigure(0, weight=1)

        self.console_label = ctk.CTkLabel(
            console_container,
            text="Engine Console",
            font=self.font_base,
            text_color=theme.MUTED_FG,
        )
        self.console_label.grid(row=0, column=0, sticky="w", padx=theme.PADDING, pady=(theme.PADDING, theme.GAP))

        self.console_text = ctk.CTkTextbox(
            console_container,
            wrap="word",
            font=self.font_mono,
        )
        self.console_text.grid(row=1, column=0, sticky=layout.sticky_all(), padx=theme.PADDING, pady=(0, theme.PADDING))
        self.console_text.configure(state="disabled")

        controls = ctk.CTkFrame(wrapper, fg_color=theme.PANEL_BG)
        controls.grid(row=2, column=0, sticky="ew", padx=theme.PADDING, pady=(0, theme.PADDING))
        controls.grid_columnconfigure(0, weight=1)

        button_row = ctk.CTkFrame(controls, fg_color=theme.PANEL_BG)
        button_row.grid(row=0, column=0, sticky="ew")
        for idx in range(5):
            button_row.grid_columnconfigure(idx, weight=1)

        self.refresh_button = ctk.CTkButton(
            button_row, text="Refresh Packs", command=self.refresh_packs, font=self.font_base
        )
        self.refresh_button.grid(row=0, column=0, padx=theme.GAP, pady=theme.GAP, sticky="ew")
        layout.style_button(self.refresh_button)

        self.set_active_button = ctk.CTkButton(
            button_row, text="Set Active", command=self.set_selected_pack, font=self.font_base
        )
        self.set_active_button.grid(row=0, column=1, padx=theme.GAP, pady=theme.GAP, sticky="ew")
        layout.style_button(self.set_active_button)

        self.validate_button = ctk.CTkButton(
            button_row, text="Validate Pack", command=self.validate_selected_pack, font=self.font_base
        )
        self.validate_button.grid(row=0, column=2, padx=theme.GAP, pady=theme.GAP, sticky="ew")
        layout.style_button(self.validate_button)

        self.run_button = ctk.CTkButton(
            button_row, text="Run Engine", command=self.run_engine, font=self.font_base
        )
        self.run_button.grid(row=0, column=3, padx=theme.GAP, pady=theme.GAP, sticky="ew")
        layout.style_button(self.run_button)

        self.stop_button = ctk.CTkButton(
            button_row, text="Stop", state="disabled", command=self.stop_engine, font=self.font_base
        )
        self.stop_button.grid(row=0, column=4, padx=theme.GAP, pady=theme.GAP, sticky="ew")
        layout.style_button(self.stop_button)

        command_row = ctk.CTkFrame(controls, fg_color=theme.PANEL_BG)
        command_row.grid(row=1, column=0, sticky="ew", pady=(theme.GAP, 0))
        command_row.grid_columnconfigure(0, weight=1)

        self.command_entry = ctk.CTkEntry(command_row, font=self.font_base)
        self.command_entry.grid(row=0, column=0, sticky="ew", padx=(0, theme.GAP))
        self.command_entry.bind("<Return>", self.send_command)

        self.send_button = ctk.CTkButton(
            command_row, text="Send", width=90, command=self.send_command, font=self.font_base
        )
        self.send_button.grid(row=0, column=1, padx=(0, theme.GAP))
        layout.style_button(self.send_button)

        self.clear_button = ctk.CTkButton(
            command_row, text="Clear", width=90, command=self.clear_console, font=self.font_base
        )
        self.clear_button.grid(row=0, column=2)
        layout.style_button(self.clear_button)

        self._toggle_command_input(False)

    # ------------------------------------------------------------------ Config helpers
    def _load_initial_zoom(self) -> int:
        cfg = load_game_config()
        try:
            zoom = int(cfg.get("ui", {}).get("zoom", 100))
        except (ValueError, TypeError):
            zoom = 100
        if zoom not in self._zoom_steps:
            zoom = 100
        return zoom

    def _update_fonts(self) -> None:
        scale = self._zoom / 100.0
        base_size = max(9, int(theme.FONT_BASE[1] * scale))
        mono_size = max(9, int(theme.FONT_MONO[1] * scale))
        self.font_base = ctk.CTkFont(family=theme.FONT_BASE[0], size=base_size)
        self.font_bold = ctk.CTkFont(family=theme.FONT_BASE[0], size=base_size, weight="bold")
        self.font_mono = ctk.CTkFont(family=theme.FONT_MONO[0], size=mono_size)

    # ------------------------------------------------------------------ Zoom controls
    def _apply_zoom(self, percent: int) -> None:
        percent = max(min(percent, self._zoom_steps[-1]), self._zoom_steps[0])
        if percent == self._zoom:
            return
        self._zoom = percent
        ctk.set_widget_scaling(percent / 100.0)
        self.zoom_var.set(f"{percent}%")
        cfg = load_game_config()
        cfg.setdefault("ui", {})["zoom"] = percent
        save_game_config(cfg)
        self._update_fonts()
        self._refresh_font_targets()

    def _on_zoom_select(self, value: str) -> None:
        try:
            percent = int(value.rstrip("%"))
        except ValueError:
            percent = 100
        self._apply_zoom(percent)

    def _zoom_in(self, event=None) -> None:
        for step in self._zoom_steps:
            if step > self._zoom:
                self._apply_zoom(step)
                break

    def _zoom_out(self, event=None) -> None:
        for step in reversed(self._zoom_steps):
            if step < self._zoom:
                self._apply_zoom(step)
                break

    def _zoom_reset(self, event=None) -> None:
        self._apply_zoom(100)

    def _refresh_font_targets(self) -> None:
        if self.active_pack_label and self.font_bold:
            self.active_pack_label.configure(font=self.font_bold)
        if getattr(self, "console_label", None) and self.font_base:
            self.console_label.configure(font=self.font_base)
        if getattr(self, "console_text", None) and self.font_mono:
            self.console_text.configure(font=self.font_mono)
        if getattr(self, "command_entry", None) and self.font_base:
            self.command_entry.configure(font=self.font_base)
        for child in self.pack_list_frame.winfo_children():
            if isinstance(child, ctk.CTkRadioButton) and self.font_base:
                child.configure(font=self.font_base)

    # ------------------------------------------------------------------ Pack helpers
    def _active_pack_text(self) -> str:
        return f"Active Pack: {self.active_pack_var.get()}"

    def refresh_packs(self) -> None:
        packs = pack_discovery.list_packs(project_root / "packs")
        for widget in self.pack_list_frame.winfo_children():
            widget.destroy()
        for name in packs:
            radio = ctk.CTkRadioButton(
                self.pack_list_frame,
                text=name,
                variable=self.pack_var,
                value=name,
                font=self.font_base,
            )
            radio.pack(fill="x", padx=theme.PADDING, pady=(0, theme.GAP))
        self._log_status(f"Discovered {len(packs)} pack(s).")
        current = active_pack.get_active_pack()
        self.active_pack_var.set(current)
        self.active_pack_label.configure(text=self._active_pack_text())
        if current in packs:
            self.pack_var.set(current)
        elif packs:
            self.pack_var.set(packs[0])
        else:
            self.pack_var.set("")

    def _selected_pack(self) -> str | None:
        value = self.pack_var.get().strip()
        return value or None

    def set_selected_pack(self) -> None:
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
        self.active_pack_label.configure(text=self._active_pack_text())
        self._log_status(f"Active pack set to {pack}")

    def validate_selected_pack(self) -> None:
        target = self._selected_pack()
        try:
            if target:
                pack = target
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

    # ------------------------------------------------------------------ Console helpers
    def _log_status(self, message: str) -> None:
        self.console_text.configure(state="normal")
        self.console_text.insert("end", message + "\n")
        self.console_text.see("end")
        self.console_text.configure(state="disabled")

    def clear_console(self, event=None) -> None:
        self.console_text.configure(state="normal")
        self.console_text.delete("1.0", "end")
        self.console_text.configure(state="disabled")

    def _toggle_command_input(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in (self.command_entry, self.send_button, self.clear_button):
            widget.configure(state=state)
        if not enabled:
            self.command_entry.delete(0, "end")

    # ------------------------------------------------------------------ Engine process
    def run_engine(self) -> None:
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
        self.after(10, self.command_entry.focus_set)

        def stream_output(proc: subprocess.Popen[str]) -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                self._log_status(line.rstrip())
            proc.stdout.close()
            self.after(0, self._on_engine_exit)

        threading.Thread(target=stream_output, args=(self.engine_process,), daemon=True).start()

    def send_command(self, event=None) -> None:
        if not self.engine_process or self.engine_process.poll() is not None:
            self._log_status("Engine is not running.")
            return
        if not self.engine_process.stdin:
            self._log_status("Engine stdin unavailable.")
            return
        text = self.command_entry.get().strip()
        if not text:
            return
        try:
            self.engine_process.stdin.write(text + "\n")
            self.engine_process.stdin.flush()
        except Exception as exc:
            self._log_status(f"Send failed: {exc}")
            return
        finally:
            self.command_entry.delete(0, "end")

    def stop_engine(self, event=None) -> None:
        if not self.engine_process or self.engine_process.poll() is not None:
            self._log_status("Engine is not running.")
            return
        try:
            self.engine_process.terminate()
            self._log_status("Stopping engine...")
        except Exception as exc:
            self._log_status(f"Stop failed: {exc}")
            return

        def await_stop(proc: subprocess.Popen[str]) -> None:
            try:
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        threading.Thread(target=await_stop, args=(self.engine_process,), daemon=True).start()

    def _on_engine_exit(self) -> None:
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

    # ------------------------------------------------------------------ Lifecycle
    def on_closing(self) -> None:
        if self.engine_process and self.engine_process.poll() is None:
            self.stop_engine()
        if self.object_editor_frame:
            self.object_editor_frame.shutdown()
        self.destroy()


def main() -> None:
    try:
        app = GameDesignHub()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    except Exception as exc:
        logger.error(f"Design hub crashed: {exc}")
        raise


if __name__ == "__main__":
    main()
