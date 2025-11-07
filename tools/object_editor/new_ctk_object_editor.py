# tools/object_editor/new_ctk_object_editor.py
import customtkinter as ctk
from loguru import logger
from ruamel.yaml import YAML
from tkinter import messagebox
from tools.object_editor.object_data_manager import ObjectDataManager
from engine.content_root import get_content_root
from engine.schemas import ObjectCategory
from typing import Optional
from pathlib import Path
from engine.validate_pack import validate_pack
from datetime import datetime, timezone


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

class NewObjectEditorFrame(ctk.CTkFrame):
    """
    A new and improved frame for creating, viewing, and editing game objects.
    """
    def __init__(self, master):
        super().__init__(master)
        logger.info("Initializing NewObjectEditorFrame...")
        self.data_manager = ObjectDataManager()
        # Compute content root label for display
        try:
            project_root = Path(__file__).resolve().parents[2]
            config_path = project_root / "game_config.yaml"
            active_pack = None
            if config_path.is_file():
                yaml = YAML()
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.load(f) or {}
                    if isinstance(cfg, dict):
                        active_pack = cfg.get("active_pack")
            self._content_root = get_content_root(active_pack)
            self._content_banner = f"Content: {self._content_root}"
        except Exception:
            self._content_root = Path(__file__).parent.parent.parent / "data"
            self._content_banner = f"Content: {self._content_root}"
        self.object_ids = self.data_manager.get_object_ids()
        self.room_ids = self.data_manager.get_room_ids()
        self.all_categories = [cat.value for cat in ObjectCategory]
        # Dirty-state and context
        self._dirty: bool = False
        self._suppress_dirty: bool = False
        self.current_object_id: Optional[str] = None
        # In-memory consumables UI meta (not persisted to schema)
        self._consumables_meta = {"health_delta": None, "per_turn_delta": None, "duration_turns": None}

        # Main layout: Top bar, then main content/side panel
        self.grid_rowconfigure(0, weight=0) # Top controls - no expand
        self.grid_rowconfigure(1, weight=1) # Main area - expand
        self.grid_columnconfigure(0, weight=1) # Main content area
        self.grid_columnconfigure(1, weight=0) # Side panel - fixed width

        # === BARS LAYOUT BEGIN ===
        # --- Top Controls Frame ---
        top_controls_frame = ctk.CTkFrame(self)
        top_controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        self.create_top_controls(top_controls_frame)

        # --- Main Content Area (Tabs) ---
        main_content_frame = ctk.CTkFrame(self)
        main_content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        main_content_frame.grid_columnconfigure(0, weight=1)
        main_content_frame.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(main_content_frame)

        # Initialize help state BEFORE building tabs
        self._help_texts = {}
        self._help_widget_to_key = {}
        self._focused_help_key = None
        self._hover_help_key = None
        self._help_default_message = (
            "Welcome. Hover over any field or section to learn what it does, or click a control to keep its help visible."
        )

        self.tab_view.grid(row=0, column=0, sticky="nsew")
        self.setup_tabs()  # safe now

        # --- Side Panel (Help/Validation) ---
        side_panel_frame = ctk.CTkFrame(self, width=250)
        side_panel_frame.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(5, 10))
        side_panel_frame.grid_rowconfigure(0, weight=1)
        side_panel_frame.grid_rowconfigure(1, weight=1)
        self.create_side_panel_content(side_panel_frame)
        self._set_help_message(self._help_default_message)
        self._attach_global_help_bindings()

        logger.info("NewObjectEditorFrame initialized successfully.")
        # Initial counts
        self.refresh_counts()

        # --- Status Bar (bottom) ---
        try:
            # Ensure grid accommodates status row
            self.grid_rowconfigure(999, weight=0)
            self.grid_columnconfigure(0, weight=1)
            status = ctk.CTkFrame(self, height=36)
            status.grid(row=999, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 6))
            status.grid_columnconfigure(0, weight=0)  # validate
            status.grid_columnconfigure(1, weight=1)  # path stretches
            status.grid_columnconfigure(2, weight=0)  # close

            self.validate_btn = ctk.CTkButton(status, text="Validate Pack", width=120, command=self._on_validate_pack)
            self.validate_btn.grid(row=0, column=0, padx=(8, 8), pady=6, sticky="w")

            self.content_path_label = ctk.CTkLabel(status, text=self._content_banner, anchor="w")
            self.content_path_label.grid(row=0, column=1, padx=(0, 8), pady=6, sticky="ew")

            self.close_btn = ctk.CTkButton(status, text="Close", width=100, command=self._on_close_editor)
            self.close_btn.grid(row=0, column=2, padx=(8, 8), pady=6, sticky="e")
        except Exception:
            pass
        # === BARS LAYOUT END ===

    def _on_validate_pack(self):
        try:
            errors = validate_pack(self._content_root)
            if errors:
                msg = "Validation errors:\n\n" + "\n".join(f"- {e}" for e in errors)
                messagebox.showwarning("Pack Validation", msg)
            else:
                messagebox.showinfo("Pack Validation", "All checks passed.")
        except Exception as e:
            messagebox.showerror("Pack Validation", f"Validation failed: {e}")

    def _on_close_editor(self):
        try:
            self.event_generate("<<RequestCloseObjectEditor>>")
        except Exception:
            pass
        # Fallback: close window if host doesn't handle the virtual event
        try:
            self.winfo_toplevel().destroy()
        except Exception:
            pass

    def create_top_controls(self, frame):
        """Creates the persistent controls at the top of the editor."""
        frame.grid_columnconfigure(1, weight=0) 

        select_label = ctk.CTkLabel(frame, text="Select Object:")
        select_label.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")

        self.object_load_combobox = ctk.CTkComboBox(frame, values=[""] + self.object_ids, width=250, command=self.on_object_selected)
        self.object_load_combobox.grid(row=0, column=1, padx=0, pady=10, sticky="w")

        reload_button = ctk.CTkButton(frame, text="Reload", width=70, command=self.on_reload_button)
        reload_button.grid(row=0, column=2, padx=(5,0), pady=10)

        new_button = ctk.CTkButton(frame, text="New", width=60, command=self.on_new_button)
        new_button.grid(row=0, column=3, padx=5, pady=10)

        self.save_button = ctk.CTkButton(frame, text="Save", width=70, command=self.on_save_button, state="disabled")
        self.save_button.grid(row=0, column=4, padx=(5,0), pady=10)

        delete_button = ctk.CTkButton(frame, text="Delete", width=70, fg_color="#b33a3a", hover_color="#992f2f", command=self.on_delete_button)
        delete_button.grid(row=0, column=5, padx=5, pady=10)
        
        total_frame = ctk.CTkFrame(frame, fg_color="transparent")
        total_frame.grid(row=0, column=6, padx=(10, 10), pady=10, sticky="e")
        total_label = ctk.CTkLabel(total_frame, text="Total Objects:")
        total_label.pack(side="left")
        self.total_objects_label = ctk.CTkLabel(total_frame, text=str(len(self.object_ids)), width=40, height=25, fg_color="grey20", corner_radius=5)
        self.total_objects_label.pack(side="left", padx=(5,0))
        
        frame.grid_columnconfigure(6, weight=1)
        frame.grid_columnconfigure(7, weight=0)

        # Register help for top bar controls
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "select_object": "Select Object\n\nChoose an object ID to load into the editor.",
                "reload": "Reload\n\nLoad the selected object's data into the form.",
                "new": "New\n\nClear fields to create a new object.",
                "save": "Save\n\nValidate and write changes to the YAML.",
                "delete": "Delete\n\nRemove the current object from YAML (after confirmation).",
                "total_objects": "Total Objects\n\nCount of objects currently in your data files.",
            })
            self._register_help(select_label, "select_object")
            self._register_help(self.object_load_combobox, "select_object")
            self._register_help(reload_button, "reload")
            self._register_help(new_button, "new")
            self._register_help(self.save_button, "save")
            self._register_help(delete_button, "delete")
            self._register_help(total_label, "total_objects")
            self._register_help(self.total_objects_label, "total_objects")
        except Exception:
            pass

    def create_side_panel_content(self, side_panel_frame):
        """Creates and populates the contextual help and validation panels."""
        help_frame = ctk.CTkFrame(side_panel_frame)
        help_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        help_label = ctk.CTkLabel(help_frame, text="Contextual Help", font=ctk.CTkFont(size=14, weight="bold"))
        help_label.pack(pady=5, padx=10, anchor="w")
        self.help_text = ctk.CTkTextbox(help_frame, wrap="word", state="disabled")
        self.help_text.pack(expand=True, fill="both", padx=10, pady=(0, 10))

        validation_frame = ctk.CTkFrame(side_panel_frame)
        validation_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        validation_label = ctk.CTkLabel(validation_frame, text="Live Validation", font=ctk.CTkFont(size=14, weight="bold"))
        validation_label.pack(pady=5, padx=10, anchor="w")
        self.validation_text = ctk.CTkTextbox(validation_frame, wrap="word", state="disabled")
        self.validation_text.pack(expand=True, fill="both", padx=10, pady=(0, 10))

    def _set_help_message(self, text: str) -> None:
        try:
            self.help_text.configure(state="normal")
            self.help_text.delete("1.0", "end")
            self.help_text.insert("end", text)
            self.help_text.configure(state="disabled")
        except Exception:
            pass

    # === HELP SYSTEM BEGIN ===
    def _ensure_help_registry(self) -> None:
        if not hasattr(self, "_help_texts") or self._help_texts is None:
            self._help_texts = {}
        if not hasattr(self, "_help_widget_to_key") or self._help_widget_to_key is None:
            self._help_widget_to_key = {}

    def _get_help_key_for(self, widget):
        """
        Resolve a help key by walking up the widget's parent chain until a
        registered ancestor is found in self._help_widget_to_key.
        Returns the key string or None if not found.
        """
        try:
            w = widget
            while w is not None:
                key = self._help_widget_to_key.get(w)
                if key:
                    return key
                w = getattr(w, "master", None)
        except Exception:
            pass
        return None

    def _register_help(self, widget, key: str):
        self._ensure_help_registry()
        self._help_widget_to_key[widget] = key

        def show_hover(e):
            if self._focused_help_key:
                return
            k = self._get_help_key_for(e.widget)
            if not k:
                return
            if k != self._hover_help_key:
                self._hover_help_key = k
                self._set_help_message(self._help_texts.get(k, self._help_default_message))

        def clear_hover(e):
            if self._focused_help_key:
                return
            # Only clear if the pointer is NOT over the same registered widget/ancestor anymore
            top = self.winfo_toplevel()
            x, y = top.winfo_pointerx(), top.winfo_pointery()
            under = top.winfo_containing(x, y)
            k_now = self._get_help_key_for(under)
            if k_now == self._hover_help_key:
                return
            self._hover_help_key = None
            self._set_help_message(self._help_default_message)

        def on_focus_in(e):
            k = self._get_help_key_for(e.widget)
            if k:
                self._focused_help_key = k
                self._hover_help_key = None
                self._set_help_message(self._help_texts.get(k, self._help_default_message))

        def on_focus_out(_e):
            self._focused_help_key = None
            if self._hover_help_key:
                self._set_help_message(self._help_texts.get(self._hover_help_key, self._help_default_message))
            else:
                self._set_help_message(self._help_default_message)

        widget.bind("<Enter>", show_hover, add="+")
        widget.bind("<Leave>", clear_hover, add="+")
        widget.bind("<FocusIn>", on_focus_in, add="+")
        widget.bind("<FocusOut>", on_focus_out, add="+")

    def _attach_global_help_bindings(self):
        top = self.winfo_toplevel()

        def on_motion(event):
            # If focused, only allow motion to update when still over the focused widget/ancestor
            if self._focused_help_key:
                key = self._get_help_key_for(event.widget)
                if key != self._focused_help_key:
                    return
            key = self._get_help_key_for(event.widget)
            if key and key != self._hover_help_key:
                self._hover_help_key = key
                self._set_help_message(self._help_texts.get(key, self._help_default_message))

        def on_focus_in(event):
            key = self._get_help_key_for(event.widget)
            if key:
                self._focused_help_key = key
                self._hover_help_key = None  # prevent hover from immediately overwriting
                self._set_help_message(self._help_texts.get(key, self._help_default_message))

        def on_focus_out(_event):
            self._focused_help_key = None
            if self._hover_help_key:
                self._set_help_message(self._help_texts.get(self._hover_help_key, self._help_default_message))
            else:
                self._set_help_message(self._help_default_message)

        def _clear_focus_lock_to_hover_under_pointer():
            # Determine widget currently under the pointer and show its hover help (or default)
            top_local = self.winfo_toplevel()
            x, y = top_local.winfo_pointerx(), top_local.winfo_pointery()
            under = top_local.winfo_containing(x, y)
            k_now = self._get_help_key_for(under)
            self._focused_help_key = None
            if k_now:
                self._hover_help_key = k_now
                self._set_help_message(self._help_texts.get(k_now, self._help_default_message))
            else:
                self._hover_help_key = None
                self._set_help_message(self._help_default_message)

        def on_any_click(event):
            # If we're focus-locked and the click is NOT on the same control/ancestor, unlock
            if self._focused_help_key:
                k = self._get_help_key_for(event.widget)
                if k != self._focused_help_key:
                    _clear_focus_lock_to_hover_under_pointer()

        def on_escape(_event):
            # Always unlock on Esc
            _clear_focus_lock_to_hover_under_pointer()

        top.bind('<Motion>', on_motion, add="+")
        top.bind('<FocusIn>', on_focus_in, add="+")
        top.bind('<FocusOut>', on_focus_out, add="+")
        top.bind('<Button-1>', on_any_click, add="+")
        top.bind('<Button-2>', on_any_click, add="+")
        top.bind('<Button-3>', on_any_click, add="+")
        top.bind('<Escape>', on_escape, add="+")


    def setup_tabs(self):
        """Creates and configures the editor tabs."""
        logger.info("Setting up editor tabs.")
        self.tab_view.add("Basic Info")
        self.tab_view.add("Properties")
        self.tab_view.add("Attributes")
        self.tab_view.add("YAML Preview")

        self.create_basic_info_tab(self.tab_view.tab("Basic Info"))
        self.create_properties_tab(self.tab_view.tab("Properties"))
        self.create_attributes_tab(self.tab_view.tab("Attributes"))
        self.create_yaml_preview_tab(self.tab_view.tab("YAML Preview"))

        # Normalize top-level tab header widths
        self._normalize_tab_header_widths(self.tab_view, min_width=140)

        logger.info("Editor tabs created.")
        # Register help for tab headers
        self._register_tab_headers_help()

    def _register_tab_headers_help(self):
        try:
            # Main tabs
            sb = self.tab_view._segmented_button
            for name, btn in (getattr(sb, "_buttons_dict", {}) or {}).items():
                key = f"tab_{name.lower().replace(' ', '_')}"
                default_map = {
                    "tab_basic_info": "Basic Info\n\nCore identifiers and descriptive fields.",
                    "tab_properties": "Properties\n\nToggle abilities and behaviors for the object.",
                    "tab_attributes": "Attributes\n\nDetailed interactions, digital content, and states.",
                    "tab_yaml_preview": "YAML Preview\n\nRead-only view of the saved YAML. Use Copy to place on clipboard.",
                }
                if key not in self._help_texts:
                    self._help_texts[key] = default_map.get(key, f"{name}\n\nSection: {name}")
                self._register_help(btn, key)
        except Exception:
            pass

    def _register_segbutton_headers_help(self, tabview, key_prefix: str, default_suffix: str = "Section group."):
        """
        Attach contextual help to a CTkTabview's segmented-button header.
        Safe against missing/private attributes.
        """
        try:
            sb = getattr(tabview, "_segmented_button", None)
            buttons = getattr(sb, "_buttons_dict", None)
            if not buttons:
                return
            for text, btn in buttons.items():
                key = f"{key_prefix}_{str(text).strip().lower().replace(' ', '_')}"
                if key not in self._help_texts:
                    self._help_texts[key] = f"{text}\n\n{default_suffix}"
                self._register_help(btn, key)
        except Exception:
            # Don't let header-binding failures affect the app
            pass

    def _autowire_help_for_container(self, container, key_prefix: str, default_suffix: str = "Control."):
        """
        Recursively register hover help for common CTk widgets inside 'container'
        that do not already have a help key. Uses widget text when available.
        """
        try:
            stack = [container]
            while stack:
                root = stack.pop()
                for w in getattr(root, "winfo_children", lambda: [])():
                    stack.append(w)
                    if w in self._help_widget_to_key:
                        continue
                    cls = w.__class__.__name__
                    eligible = cls.startswith("CTk") and any(
                        part in cls for part in ("Label", "Entry", "ComboBox", "Checkbox", "Button", "Textbox", "OptionMenu", "Switch")
                    )
                    if not eligible:
                        continue
                    text = ""
                    try:
                        if hasattr(w, "cget"):
                            txt = w.cget("text")
                            text = txt if isinstance(txt, str) else ""
                    except Exception:
                        pass
                    base = text.strip() or cls
                    key = f"{key_prefix}_{base.lower().replace(' ', '_')}_{w.winfo_id()}"
                    if key not in self._help_texts:
                        self._help_texts[key] = f"{base}\n\n{default_suffix}"
                    self._register_help(w, key)
        except Exception:
            pass

    def create_placeholder_tab(self, tab, tool_name):
        """Creates a placeholder UI for a tool tab."""
        label = ctk.CTkLabel(tab, text=f"{tool_name} Content - Coming Soon!", font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(pady=20, padx=20)

    def _set_validation_message(self, text: str) -> None:
        """Updates the validation panel text area with a message."""
        try:
            self.validation_text.configure(state="normal")
            self.validation_text.delete("1.0", "end")
            self.validation_text.insert("end", text)
            self.validation_text.configure(state="disabled")
        except Exception:
            pass

    def _update_area_options_for_room(self, room_id: Optional[str]) -> None:
        """Refreshes the Area combobox values based on the given room id and enables/disables it."""
        room_id = room_id or ""
        area_ids = [""]
        if room_id:
            area_ids += self.data_manager.get_area_ids_for_room(room_id)
        state = "normal" if len(area_ids) > 1 else "disabled"
        try:
            self.area_combobox.configure(values=area_ids, state=state)
            # Default to blank selection; specific selection handled by caller
            self.area_combobox.set("")
        except Exception:
            pass

    def _update_save_button_state(self) -> None:
        try:
            if hasattr(self, "save_button"):
                allow = self._dirty and not getattr(self, "_validation_errors", [])
                self.save_button.configure(state=("normal" if allow else "disabled"))
        except Exception:
            pass

    def _mark_dirty(self, *_):
        if self._suppress_dirty:
            return
        self._dirty = True
        self._update_save_button_state()
        self.update_preview_event()

    def _on_user_change(self, *_):
        self._mark_dirty()

    def _confirm_discard_if_dirty(self) -> bool:
        if not self._dirty:
            return True
        return messagebox.askyesno("Unsaved changes", "Unsaved changes will be lost. Continue?")

    def on_reload_button(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        self.on_load_button()

    def on_save_button(self) -> None:
        try:
            data = self._apply_save_transforms(self._collect_object_dict())
            current_id = self.current_object_id or data.get("id")
            if not current_id:
                messagebox.showwarning("Save", "No object selected to save.")
                return
            # Validation gate: block save if errors
            try:
                self._run_validation_and_update_panel(data)
                if getattr(self, "_validation_errors", []):
                    messagebox.showerror("Save", "Cannot save due to blocking issues:\n\n- " + "\n- ".join(self._validation_errors))
                    return
            except Exception:
                pass
            # Overwrite confirm if ID exists
            if current_id in self.data_manager.get_object_ids():
                if not messagebox.askyesno("Overwrite object?", f"Saving will overwrite '{current_id}'. Continue?"):
                    return
            # Merge with existing or build new skeleton, then persist via existing manager
            existing = self.data_manager.get_object_by_id(current_id) or {}
            updated = dict(existing)
            # Replace with minimal dict we collected (keeps schema keys intact)
            updated.update(data)
            # data already includes timestamps/object number via _apply_save_transforms
            updated = data

            ok1 = False
            if existing:
                ok1 = self.data_manager.update_object(current_id, updated)
            else:
                ok1 = self.data_manager.add_object(updated)
            ok2 = self.data_manager.save_all_changes()
            if ok1 and ok2:
                self._dirty = False
                self._update_save_button_state()
                messagebox.showinfo("Save", f"Object '{current_id}' saved.")
                # Refresh object list in case ID changed
                self.object_ids = self.data_manager.get_object_ids()
                self.object_load_combobox.configure(values=[""] + self.object_ids)
                self.refresh_counts()
                # Keep current selection
                self.current_object_id = updated.get("id", current_id)
                self.object_load_combobox.set(self.current_object_id)
            else:
                messagebox.showerror("Save", "Failed to save changes.")
        except Exception as e:
            logger.exception("Save failed")
            messagebox.showerror("Save", f"Save failed: {e}")

    def on_delete_button(self) -> None:
        obj_id = self.current_object_id or (self.object_load_combobox.get() or "").strip()
        if not obj_id:
            messagebox.showwarning("Delete", "No object selected.")
            return
        if not messagebox.askyesno("Delete", f"Delete object '{obj_id}'? This cannot be undone."):
            return
        if not self.data_manager.delete_object(obj_id):
            messagebox.showerror("Delete", f"Failed to delete '{obj_id}'.")
            return
        if not self.data_manager.save_all_changes():
            messagebox.showwarning("Delete", "Deleted in memory but failed to save files.")
        # Refresh UI lists
        self.object_ids = self.data_manager.get_object_ids()
        self.object_load_combobox.configure(values=[""] + self.object_ids)
        self.refresh_counts()
        # Clear fields
        self.clear_all_fields()
        self.current_object_id = None
        self._dirty = False
        self._update_save_button_state()

    def on_new_button(self) -> None:
        if not self._confirm_discard_if_dirty():
            return
        self.clear_all_fields()
        self.current_object_id = None
        self._dirty = False
        self._update_save_button_state()
        self.refresh_counts()
        # Enable ID entry for new object creation and focus it
        try:
            self.object_id_entry.configure(state="normal")
            self.object_id_entry.focus_set()
            # Pre-fill next available object number into Object No. entry
            if hasattr(self.data_manager, "get_next_object_number") and hasattr(self, "object_count_entry"):
                try:
                    self.object_count_entry.configure(state="normal")
                    self.object_count_entry.delete(0, "end")
                    self.object_count_entry.insert(0, str(self.data_manager.get_next_object_number()))
                finally:
                    self.object_count_entry.configure(state="disabled")
        except Exception:
            pass

    def on_object_selected(self, _value: str) -> None:
        """Callback for the object combobox selection; loads immediately when a choice is made."""
        if not self._confirm_discard_if_dirty():
            # revert selection
            if self.current_object_id:
                self.object_load_combobox.set(self.current_object_id)
            return
        self.on_reload_button()

    # Back-compat shim: some call sites expect on_load_button
    def on_load_button(self) -> None:
        """Alias for reload behavior; loads selected object into fields."""
        selected_id = (self.object_load_combobox.get() or "").strip()
        if not selected_id:
            self._set_validation_message("Select an object ID from the dropdown, then click Reload.")
            return
        obj = self.data_manager.get_object_by_id(selected_id)
        if not obj:
            self._set_validation_message(f"Object '{selected_id}' not found in data.")
            return
        try:
            self.populate_fields(obj)
            room_id, area_id = self.data_manager.find_object_location(selected_id)
            self.location_combobox.set(room_id or "")
            self._update_area_options_for_room(room_id)
            if area_id:
                try:
                    self.area_combobox.set(area_id)
                except Exception:
                    pass
            self._set_validation_message(f"Loaded object '{selected_id}'.")
            self.update_preview_event()
            self.current_object_id = selected_id
            self._dirty = False
            self._update_save_button_state()
            self.refresh_counts()
        except Exception as e:
            logger.exception("Failed to populate fields from loaded object")
            self._set_validation_message(f"Error loading object '{selected_id}': {e}")

    def create_basic_info_tab(self, tab):
        """Creates the UI for the Basic Info tab with a structured, justified layout."""
        content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=(50, 12))

        # Configure grid columns: 0=labels, 1=main fields (flex), 2=spacer, 3=small right labels, 4=small right entries
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=0)
        content_frame.grid_columnconfigure(3, weight=0)
        content_frame.grid_columnconfigure(4, weight=0)
        content_frame.grid_columnconfigure(3, weight=0)

        LABEL_WIDTH = 120
        PAD_Y = (10, 10) # Increased vertical padding
        TEXT_WIDTH = 420
        COMBO_WIDTH = 260
        SMALL_WIDTH = 80

        # --- Row 0: Object ID + Count ---
        id_label = ctk.CTkLabel(content_frame, text="Object ID:", width=LABEL_WIDTH, anchor="w")
        id_label.grid(row=0, column=0, padx=10, pady=PAD_Y, sticky="w")
        self.object_id_entry = ctk.CTkEntry(content_frame, placeholder_text="e.g., bridge_torch", width=TEXT_WIDTH)
        self.object_id_entry.grid(row=0, column=1, padx=10, pady=PAD_Y, sticky="w")
        self.object_id_entry.bind("<KeyRelease>", self._on_user_change)
        # Make ID read-only by default; enabled only when creating a new object
        self.object_id_entry.configure(state="disabled")
        
        self.object_no_label = ctk.CTkLabel(content_frame, text="Object No.:", anchor="e")
        self.object_no_label.grid(row=0, column=3, padx=(16,6), pady=PAD_Y, sticky="e")
        self.object_no_label.configure(width=0)
        if not hasattr(self, "object_count_entry") or self.object_count_entry is None:
            self.object_count_entry = ctk.CTkEntry(content_frame, width=SMALL_WIDTH)
            self.object_count_entry.configure(state="disabled")
        self.object_count_entry.grid(row=0, column=4, padx=(0,10), pady=PAD_Y, sticky="w")
        try:
            self.object_count_entry.configure(state="readonly")
        except Exception:
            pass
        # Ensure no rowspan is used
        self.object_no_label.grid_configure(rowspan=1)
        self.object_count_entry.grid_configure(rowspan=1)

        # --- Row 1: Name and Is Plural ---
        name_label = ctk.CTkLabel(content_frame, text="Name:", width=LABEL_WIDTH, anchor="w")
        name_label.grid(row=1, column=0, padx=10, pady=PAD_Y, sticky="w")

        name_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        # allow the row to expand so the checkbox isn't clipped
        name_row.grid(row=1, column=1, padx=(10,0), pady=PAD_Y, sticky="ew")
        name_row.grid_columnconfigure(0, weight=1)   # entry grows
        name_row.grid_columnconfigure(1, weight=0)   # checkbox hugs entry

        self.name_entry = ctk.CTkEntry(name_row, placeholder_text="e.g., Emergency Torch", width=TEXT_WIDTH)
        self.name_entry.grid(row=0, column=0, sticky="ew")
        self.name_entry.bind("<KeyRelease>", self._on_user_change)

        # Move Is Plural? to main content_frame so Name can keep full width
        self.is_plural_checkbox = ctk.CTkCheckBox(content_frame, text="Is Plural?")
        self.is_plural_checkbox.grid(row=1, column=2, padx=(10, 0), pady=PAD_Y, sticky="w")
        self.is_plural_checkbox.configure(command=self._mark_dirty)
        self.is_plural_checkbox.lift()

        # --- Row 2: Synonyms ---
        synonyms_label = ctk.CTkLabel(content_frame, text="Synonyms (CSV):", width=LABEL_WIDTH, anchor="w")
        synonyms_label.grid(row=2, column=0, padx=10, pady=PAD_Y, sticky="w")
        self.synonyms_entry = ctk.CTkEntry(content_frame, placeholder_text="e.g., light, torch", width=TEXT_WIDTH)
        self.synonyms_entry.grid(row=2, column=1, columnspan=1, padx=10, pady=PAD_Y, sticky="w")
        self.synonyms_entry.bind("<KeyRelease>", self._on_user_change)
        
        # --- Row 3: Category ---
        category_label = ctk.CTkLabel(content_frame, text="Category:", width=LABEL_WIDTH, anchor="w")
        category_label.grid(row=3, column=0, padx=10, pady=PAD_Y, sticky="w")
        self.category_combobox = ctk.CTkComboBox(content_frame, values=self.all_categories, width=COMBO_WIDTH)
        self.category_combobox.grid(row=3, column=1, padx=10, pady=PAD_Y, sticky="w")
        self.category_combobox.configure(command=self._on_user_change)

        # --- Row 4: Location & Area ---
        location_label = ctk.CTkLabel(content_frame, text="Location:", width=LABEL_WIDTH, anchor="w")
        location_label.grid(row=4, column=0, padx=10, pady=PAD_Y, sticky="w")
        self.location_combobox = ctk.CTkComboBox(content_frame, values=[""] + self.room_ids, width=COMBO_WIDTH)
        self.location_combobox.grid(row=4, column=1, padx=10, pady=PAD_Y, sticky="w")
        def _on_location_change(value):
            self._update_area_options_for_room(value)
            self._mark_dirty()
        self.location_combobox.configure(command=_on_location_change)

        # --- Row 5: Area ---
        area_label = ctk.CTkLabel(content_frame, text="Area in Room:", width=LABEL_WIDTH, anchor="w")
        area_label.grid(row=5, column=0, padx=10, pady=PAD_Y, sticky="w")
        self.area_combobox = ctk.CTkComboBox(content_frame, values=[""], state="disabled", width=COMBO_WIDTH)
        self.area_combobox.grid(row=5, column=1, padx=10, pady=PAD_Y, sticky="w")
        self.area_combobox.configure(command=self._on_user_change)
        
        # --- Row 6: Weight and Size (clustered subframe) ---
        weight_label = ctk.CTkLabel(content_frame, text="Weight:", width=LABEL_WIDTH, anchor="w")
        weight_label.grid(row=6, column=0, padx=10, pady=PAD_Y, sticky="w")

        # Cluster weight and size tightly in a subframe anchored left
        ws_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        ws_frame.grid(row=6, column=1, columnspan=3, padx=10, pady=PAD_Y, sticky="w")

        self.weight_entry = ctk.CTkEntry(ws_frame, width=SMALL_WIDTH)
        self.weight_entry.grid(row=0, column=0, padx=(0,6), sticky="w")
        self.weight_entry.bind("<KeyRelease>", self._on_user_change)

        size_label = ctk.CTkLabel(ws_frame, text="Size:", anchor="w")
        size_label.grid(row=0, column=1, padx=(6,6), sticky="w")

        self.size_entry = ctk.CTkEntry(ws_frame, width=SMALL_WIDTH)
        self.size_entry.grid(row=0, column=2, padx=(0,0), sticky="w")
        self.size_entry.bind("<KeyRelease>", self._on_user_change)
        
        # --- Row 7: Description (fixed height) ---
        description_label = ctk.CTkLabel(content_frame, text="Description:", width=LABEL_WIDTH, anchor="w")
        description_label.grid(row=7, column=0, padx=10, pady=PAD_Y, sticky="nw")

        # Create the textbox BEFORE registering help
        self.description_textbox = ctk.CTkTextbox(content_frame, height=200, wrap="word")
        self.description_textbox.grid(row=7, column=1, columnspan=3, padx=10, pady=PAD_Y, sticky="ew")
        content_frame.grid_rowconfigure(7, weight=0)  # keep description row fixed height
        self.description_textbox.bind("<KeyRelease>", self._on_user_change)

        # Now register help (no broad try/except)
        self._ensure_help_registry()
        self._help_texts.update({
            "id": "Object ID\n\nA unique snake_case identifier for the object. Example: 'plasma_torch'. Do: keep short, unique. Don't: include spaces.",
            "name": "Display Name\n\nPlayer-facing name. Keep it clear, 2–4 words. Example: 'Plasma Torch'.",
            "synonyms": "Synonyms\n\nComma-separated alternative names for parser matching. Example: 'torch, cutter, welder'.",
            "category": "Category\n\nHigh-level object type used by the engine (e.g., 'tool', 'container', 'key_item').",
            "location": "Default Location\n\nWhere this object initially lives. Example: 'engineering_bay'.",
            "area": "Area\n\nLogical sub-region within the location (optional). Example: 'workbench'.",
            "weight": "Weight\n\nNumeric (kg). Used for carry rules. Example: '2.5'.",
            "size": "Size\n\nFree text or preset (e.g., 'small', 'medium', 'large').",
            "object_number": "Object No.\n\nRead-only unique number for this object.",
            "size_label": "Size\n\nGeneral size descriptor for the engine.",
            "description": "Description\n\nExamine text shown to the player. Keep it evocative and concise.",
            "is_plural": "Is Plural?\n\nMarks the object name as plural (e.g., 'slippers'). Affects grammar and messages.",
        })

        pairs = [
            (id_label, "id"), (self.object_id_entry, "id"),
            (name_label, "name"), (self.name_entry, "name"),
            (synonyms_label, "synonyms"), (self.synonyms_entry, "synonyms"),
            (category_label, "category"), (self.category_combobox, "category"),
            (location_label, "location"), (self.location_combobox, "location"),
            (area_label, "area"), (self.area_combobox, "area"),
            (weight_label, "weight"), (self.weight_entry, "weight"),
            (self.object_no_label, "object_number"), (self.object_count_entry, "object_number"),
            (size_label, "size_label"), (self.size_entry, "size"),
            (description_label, "description"), (self.description_textbox, "description"),
        ]

        for w, key in pairs:
            self._register_help(w, key)

        # Register contextual help for the Is Plural? checkbox
        self._register_help(self.is_plural_checkbox, "is_plural")

        # Timestamps row (read-only)
        created_label = ctk.CTkLabel(content_frame, text="Created:", width=LABEL_WIDTH, anchor="w")
        created_label.grid(row=8, column=0, padx=10, pady=PAD_Y, sticky="w")
        self.created_at_entry = ctk.CTkEntry(content_frame)
        self.created_at_entry.configure(state="disabled")
        self.created_at_entry.grid(row=8, column=1, padx=10, pady=PAD_Y, sticky="w")

        updated_label = ctk.CTkLabel(content_frame, text="Modified:", width=LABEL_WIDTH, anchor="w")
        updated_label.grid(row=8, column=2, padx=10, pady=PAD_Y, sticky="w")
        self.updated_at_entry = ctk.CTkEntry(content_frame)
        self.updated_at_entry.configure(state="disabled")
        self.updated_at_entry.grid(row=8, column=3, padx=10, pady=PAD_Y, sticky="w")

    def create_properties_tab(self, tab):
        """Creates the Properties tab with two rows of sub-tabs (60/40 split)."""
        container = ctk.CTkFrame(tab)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        # 60/40 vertical split for top/bottom tabviews
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=3)  # top – 60%
        container.grid_rowconfigure(1, weight=2)  # bottom – 40%

        # Top row tabview wrapped for padded headers
        top_wrap = ctk.CTkFrame(container)
        top_wrap.grid(row=0, column=0, sticky="nsew", padx=14, pady=(6, 8))
        top_wrap.grid_columnconfigure(0, weight=1)
        top_wrap.grid_rowconfigure(0, weight=1)
        self.properties_tabview_top = ctk.CTkTabview(top_wrap)
        self.properties_tabview_top.pack(fill="both", expand=True, padx=10, pady=6)

        # Bottom row tabview wrapped for padded headers
        bottom_wrap = ctk.CTkFrame(container)
        bottom_wrap.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 6))
        bottom_wrap.grid_columnconfigure(0, weight=1)
        bottom_wrap.grid_rowconfigure(0, weight=1)
        self.properties_tabview_bottom = ctk.CTkTabview(bottom_wrap)
        self.properties_tabview_bottom.pack(fill="both", expand=True, padx=10, pady=6)

        # Fallback: widen segmented buttons if accessible
        try:
            self.properties_tabview_top._segmented_button.configure(width=720)
            self.properties_tabview_bottom._segmented_button.configure(width=720)
        except Exception:
            pass
    # === HELP SYSTEM END ===

        # Initialize property checkboxes dictionary
        self.prop_checks = {}

        # Define tab names by rows
        top_tabs = [
            "Core Behaviours",
            "Storage",
            "Locking",
            "Wearability",
            "Weapons",
            "Consumables",
        ]
        bottom_tabs = [
            "Device & Tech",
            "Fantasy & Magic",
            "Crafting & Social",
            "Physical & Material",
            "Extended",
        ]

        # Map of tab name to its container frame
        self._prop_tabs = {}
        for name in top_tabs:
            self.properties_tabview_top.add(name)
            self._prop_tabs[name] = self.properties_tabview_top.tab(name)
        for name in bottom_tabs:
            self.properties_tabview_bottom.add(name)
            self._prop_tabs[name] = self.properties_tabview_bottom.tab(name)

        # Normalize header widths for properties tabviews
        self._normalize_tab_header_widths(self.properties_tabview_top, min_width=140)
        self._normalize_tab_header_widths(self.properties_tabview_bottom, min_width=140)

        # Build each sub-tab into its mapped container
        self._build_core_behaviours_tab()
        self._build_storage_tab()
        self._build_locking_tab()
        self._build_wearability_tab()
        self._build_weapons_tab()
        self._build_consumables_tab()
        self._build_device_tech_tab()
        self._build_fantasy_magic_tab()
        self._build_crafting_social_tab()
        self._build_physical_material_tab()
        self._build_extended_tab()
        # Attach numeric clamp binders once all controls exist
        self._bind_numeric_clamp()

        # Register hover help on the Properties header buttons (both rows)
        try:
            self._register_segbutton_headers_help(self.properties_tabview_top, "prop_hdr_top", "Properties group.")
        except Exception:
            pass
        try:
            self._register_segbutton_headers_help(self.properties_tabview_bottom, "prop_hdr_bottom", "Properties group.")
        except Exception:
            pass

    def _grid4(self, frame):
        """Configure a 4-column evenly spaced grid for a frame."""
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=1)

    def _prep_props_grid(self, parent, cols: int = 4):
        """Prepare a properties grid with uniform column widths."""
        for i in range(cols):
            parent.grid_columnconfigure(i, weight=1, uniform="props")

    def _normalize_tab_header_widths(self, tabview, *, min_width: int = 140, label_padx: int = 10, label_pady: int = 6):
        """Force tab headers to have a consistent minimum width and padding."""
        try:
            sb = tabview._segmented_button  # private
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

    def _normalize_tab_header_widths_smaller(self, tabview):
        """Helper to slightly reduce header widths when there are many tabs."""
        try:
            self._normalize_tab_header_widths(tabview, min_width=120, label_padx=8, label_pady=4)
        except Exception:
            pass

    def _attach_entry_like_methods_to_combobox(self, combo: ctk.CTkComboBox) -> None:
        """Allow CTkComboBox to behave like an Entry for existing code paths (delete/insert)."""
        try:
            combo.delete = lambda start, end: combo.set("")
            combo.insert = lambda index, text: combo.set(str(text))
        except Exception:
            pass

    def _clamp_int_0_100(self, combo: ctk.CTkComboBox) -> None:
        """Clamp the value in the given combo to an integer within [0, 100]."""
        try:
            raw = (combo.get() or "").strip()
            val = int(float(raw)) if raw not in (None, "") else 0
            if val < 0:
                val = 0
            if val > 100:
                val = 100
            combo.set(str(val))
        except Exception:
            combo.set("0")
        self._on_user_change()

    def _clamp_int_range(self, combo: ctk.CTkComboBox, min_val: int, max_val: int) -> None:
        try:
            raw = (combo.get() or "").strip()
            val = int(float(raw)) if raw not in (None, "") else min_val
            if val < min_val:
                val = min_val
            if val > max_val:
                val = max_val
            combo.set(str(val))
        except Exception:
            combo.set(str(min_val))
        self._on_user_change()

    def _build_core_behaviours_tab(self):
        tab = self._prop_tabs["Core Behaviours"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        # First checkbox: Initially Visible (top-left)
        try:
            self.initial_visible_checkbox = ctk.CTkCheckBox(fr, text="Initially Visible", command=self._mark_dirty)
            self.initial_visible_checkbox.grid(row=0, column=0, padx=14, pady=10, sticky="w")
        except Exception:
            pass

        # Place Open near Initially Visible (top-level state, but UI grouped here)
        try:
            self.is_open_checkbox = ctk.CTkCheckBox(fr, text="Open", command=self._mark_dirty)
            self.is_open_checkbox.grid(row=0, column=1, padx=14, pady=10, sticky="w")
        except Exception:
            pass

        # Order next: Takeable, Interactive, then the remaining
        props = [
            ("is_takeable", "Takeable"),
            ("is_interactive", "Interactive"),
            ("is_openable_closable", "Openable/Closable"),
            ("is_lockable", "Lockable"),
            ("is_movable", "Movable"),
            ("is_secret", "Secret"),
            ("is_hidden", "Hidden"),
            ("is_modular", "Modular"),
            ("is_transferable", "Transferable"),
            ("is_stored", "Stored"),
        ]
        # Start at index 2 so 'Open' occupies row 0, col 1 without overlap
        self._create_checks_grid(fr, props, start_index=2)

        # Register contextual help for Core Behaviours
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "initial_state": "Initially Visible\n\nIf checked, the object starts visible in its location. Uncheck for hidden/revealed later.",
                "is_open": "Open\n\nTop-level open state for openable items. Requires Openable/Closable to make sense.",
                "is_takeable": "Takeable\n\nPlayer can pick up and carry the object.",
                "is_interactive": "Interactive\n\nSupports specific actions beyond generic verbs.",
                "is_openable_closable": "Openable/Closable\n\nCan be opened and closed (doors, containers, books).",
                "is_movable": "Movable\n\nCan be pushed or pulled without being taken.",
                "is_secret": "Secret\n\nHidden or special, typically discovered via puzzles.",
                "is_hidden": "Hidden\n\nNot initially visible; might require searching.",
                "is_modular": "Modular\n\nCan accept modules or upgrades.",
                "is_transferable": "Transferable\n\nDigital content can be moved or copied.",
                "is_stored": "Stored\n\nPrimarily data or placed inside another object initially.",
            })
            # Labels/checkboxes
            self._register_help(self.initial_visible_checkbox, "initial_state")
            self._register_help(self.is_open_checkbox, "is_open")
            for key, cb in [("is_takeable", self.prop_checks.get("is_takeable")),
                            ("is_interactive", self.prop_checks.get("is_interactive")),
                            ("is_openable_closable", self.prop_checks.get("is_openable_closable")),
                            ("is_movable", self.prop_checks.get("is_movable")),
                            ("is_secret", self.prop_checks.get("is_secret")),
                            ("is_hidden", self.prop_checks.get("is_hidden")),
                            ("is_modular", self.prop_checks.get("is_modular")),
                            ("is_transferable", self.prop_checks.get("is_transferable")),
                            ("is_stored", self.prop_checks.get("is_stored"))]:
                if cb:
                    self._register_help(cb, key)
        except Exception:
            pass

    def _build_physical_material_tab(self):
        tab = self._prop_tabs["Physical & Material"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        props = [
            ("is_electronic", "Electronic"),
            ("is_conductive", "Conductive"),
            ("is_magnetic", "Magnetic"),
            ("is_flammable", "Flammable"),
            ("is_fragile", "Fragile"),
            ("is_destroyable", "Destroyable"),
            ("is_toxic", "Toxic"),
            ("is_dangerous", "Dangerous"),
            ("is_buoyant", "Buoyant"),
            ("is_repairable", "Repairable"),
            ("can_be_disassembled", "Disassemblable"),
        ]
        self._create_checks_grid(fr, props)

    def _build_wearability_tab(self):
        tab = self._prop_tabs["Wearability"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        # Row 0: Wearable toggle
        self.prop_checks["is_wearable"] = ctk.CTkCheckBox(
            fr, text="Wearable", command=lambda: [self.toggle_wearability_fields(), self._mark_dirty()]
        )
        self.prop_checks["is_wearable"].grid(row=0, column=0, padx=10, pady=(8, 6), sticky="w")
        # Row 1: Wear Area and Layer controls
        ctk.CTkLabel(fr, text="Wear Area:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.wear_area_combo = ctk.CTkComboBox(
            fr,
            values=["head", "torso", "arms", "legs", "feet", "hands", "neck", "waist"],
            state="disabled",
            width=200,
            command=self._on_user_change,
        )
        self.wear_area_combo.grid(row=1, column=1, padx=(6, 10), pady=8, sticky="w")
        ctk.CTkLabel(fr, text="Layer:").grid(row=1, column=2, padx=10, pady=8, sticky="e")
        self.wear_layer_entry = ctk.CTkComboBox(fr, values=["1", "2", "3", "4", "5"], state="disabled", width=90)
        self._attach_entry_like_methods_to_combobox(self.wear_layer_entry)
        self.wear_layer_entry.grid(row=1, column=3, padx=(6, 10), pady=8, sticky="w")
        self.wear_layer_entry.bind("<KeyRelease>", self._on_user_change)
        self.wear_layer_entry.bind("<FocusOut>", self._on_user_change)

        # Help bindings
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "is_wearable": "Wearable\n\nItem can be worn by the player.",
                "wear_area": "Wear Area\n\nBody area where this is worn (e.g., head, torso).",
                "wear_layer": "Wear Layer\n\nLayer order (e.g., 1 inner … 5 outer).",
            })
            self._register_help(self.prop_checks.get("is_wearable"), "is_wearable")
            self._register_help(self.wear_area_combo, "wear_area")
            self._register_help(self.wear_layer_entry, "wear_layer")
        except Exception:
            pass

    def _build_consumables_tab(self):
        tab = self._prop_tabs["Consumables"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        # Container uses grid for tight vertical placement
        fr.grid_columnconfigure(0, weight=1)
        # Row 0: checkbox grid (anchored NW)
        checkbox_frame = ctk.CTkFrame(fr, fg_color="transparent")
        checkbox_frame.grid(row=0, column=0, sticky="nw", padx=10, pady=(10, 6))
        self._prep_props_grid(checkbox_frame)
        props = [
            ("is_edible", "Edible"),
            ("is_drinkable", "Drinkable"),
            ("is_usable", "Usable"),
            ("is_food", "Food"),
            ("is_cookable", "Cookable"),
            ("is_consumable", "Consumable"),
        ]
        self._create_checks_grid(checkbox_frame, props)
        # Row 1: Always-visible numeric controls (disabled until checked)
        PADX, PADY = 14, 10
        controls_frame = ctk.CTkFrame(fr, fg_color="transparent")
        controls_frame.grid(row=1, column=0, sticky="w", padx=10, pady=(6, 8))
        for i in range(6):
            controls_frame.grid_columnconfigure(i, weight=1 if i in (1,3,5) else 0)

        ctk.CTkLabel(controls_frame, text="Health Δ:").grid(row=0, column=0, padx=PADX, pady=PADY, sticky="e")
        self.cons_health_combo = ctk.CTkComboBox(controls_frame, values=[str(v) for v in [-100,-50,-25,-10,10,25,50,100]], width=90, state="disabled", command=lambda *_: self._on_user_change())
        self._attach_entry_like_methods_to_combobox(self.cons_health_combo)
        self.cons_health_combo.grid(row=0, column=1, padx=(6, PADX), pady=PADY, sticky="w")
        self.cons_health_combo.bind("<FocusOut>", lambda e: [self._clamp_int_range(self.cons_health_combo, -100, 100), self._update_consumables_meta()])

        ctk.CTkLabel(controls_frame, text="Per-Turn Δ:").grid(row=0, column=2, padx=PADX, pady=PADY, sticky="e")
        self.cons_per_turn_combo = ctk.CTkComboBox(controls_frame, values=[str(v) for v in [-50,-25,-10,-5,5,10,25,50]], width=90, state="disabled", command=lambda *_: self._on_user_change())
        self._attach_entry_like_methods_to_combobox(self.cons_per_turn_combo)
        self.cons_per_turn_combo.grid(row=0, column=3, padx=(6, PADX), pady=PADY, sticky="w")
        self.cons_per_turn_combo.bind("<FocusOut>", lambda e: [self._clamp_int_range(self.cons_per_turn_combo, -50, 50), self._update_consumables_meta()])

        ctk.CTkLabel(controls_frame, text="Duration:").grid(row=0, column=4, padx=PADX, pady=PADY, sticky="e")
        self.cons_duration_combo = ctk.CTkComboBox(controls_frame, values=[str(v) for v in [1,2,3,5,10,15,20]], width=90, state="disabled", command=lambda *_: self._on_user_change())
        self._attach_entry_like_methods_to_combobox(self.cons_duration_combo)
        self.cons_duration_combo.grid(row=0, column=5, padx=(6, PADX), pady=PADY, sticky="w")
        self.cons_duration_combo.bind("<FocusOut>", lambda e: [self._clamp_int_range(self.cons_duration_combo, 1, 20), self._update_consumables_meta()])

        # Place a stretchy spacer row below to consume extra space
        fr.grid_rowconfigure(3, weight=1)

        # Wire consumable toggle to enable/disable
        if "is_consumable" in self.prop_checks:
            self.prop_checks["is_consumable"].configure(command=lambda: [self.toggle_consumable_fields(), self._mark_dirty()])
        self.toggle_consumable_fields()

        # Help bindings
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "is_edible": "Edible\n\nCan be eaten.",
                "is_drinkable": "Drinkable\n\nCan be drunk.",
                "is_usable": "Usable\n\nSingle-use or general-purpose consumable.",
                "is_food": "Food\n\nSpecifically food.",
                "is_cookable": "Cookable\n\nCan be cooked to change state.",
                "is_consumable": "Consumable\n\nIs consumed on use.",
                "cons_health": "Health Δ\n\nInstant health change when consumed.",
                "cons_per_turn": "Per-Turn Δ\n\nRecurring effect per turn.",
                "cons_duration": "Duration\n\nTurns the per-turn effect lasts.",
            })
            for key, cb in [("is_edible", self.prop_checks.get("is_edible")),
                            ("is_drinkable", self.prop_checks.get("is_drinkable")),
                            ("is_usable", self.prop_checks.get("is_usable")),
                            ("is_food", self.prop_checks.get("is_food")),
                            ("is_cookable", self.prop_checks.get("is_cookable")),
                            ("is_consumable", self.prop_checks.get("is_consumable"))]:
                if cb:
                    self._register_help(cb, key)
            self._register_help(self.cons_health_combo, "cons_health")
            self._register_help(self.cons_per_turn_combo, "cons_per_turn")
            self._register_help(self.cons_duration_combo, "cons_duration")
        except Exception:
            pass

    def _update_consumables_meta(self) -> None:
        try:
            self._consumables_meta["health_delta"] = int((self.cons_health_combo.get() or "").strip()) if self.cons_health_combo.cget("state") == "normal" else None
        except Exception:
            self._consumables_meta["health_delta"] = None
        try:
            self._consumables_meta["per_turn_delta"] = int((self.cons_per_turn_combo.get() or "").strip()) if self.cons_per_turn_combo.cget("state") == "normal" else None
        except Exception:
            self._consumables_meta["per_turn_delta"] = None
        try:
            self._consumables_meta["duration_turns"] = int((self.cons_duration_combo.get() or "").strip()) if self.cons_duration_combo.cget("state") == "normal" else None
        except Exception:
            self._consumables_meta["duration_turns"] = None

    def _build_device_tech_tab(self):
        tab = self._prop_tabs["Device & Tech"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        # Device & Tech flags (weapon settings moved to Weapons tab)
        tech_props = [
            ("is_networked", "Networked"),
            ("is_operational", "Operational"),
            ("requires_power", "Requires Power"),
            ("is_hackable", "Hackable"),
            ("is_rechargeable", "Rechargeable"),
            ("is_fuel_source", "Fuel Source"),
            ("is_activatable", "Activatable"),
        ]
        self._create_checks_grid(fr, tech_props)

        # Help bindings
        try:
            self._ensure_help_registry()
            tips = {
                "is_networked": "Networked\n\nConnected to a network; interactions may have remote effects.",
                "is_operational": "Operational\n\nCan be turned on/off or otherwise operated.",
                "requires_power": "Requires Power\n\nNeeds power to function; ties to Power State.",
                "is_hackable": "Hackable\n\nCan be hacked using appropriate tools/skills.",
                "is_rechargeable": "Rechargeable\n\nPower can be replenished.",
                "is_fuel_source": "Fuel Source\n\nProvides fuel for devices/systems.",
                "is_activatable": "Activatable\n\nRequires specific activation sequence/condition.",
            }
            self._help_texts.update(tips)
            for k in tips:
                cb = self.prop_checks.get(k)
                if cb:
                    self._register_help(cb, k)
        except Exception:
            pass

    def _build_weapons_tab(self):
        tab = self._prop_tabs["Weapons"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        # Row 0: Weapon toggle
        self.prop_checks["is_weapon"] = ctk.CTkCheckBox(
            fr, text="Weapon", command=lambda: [self.toggle_weapon_fields(), self._mark_dirty()]
        )
        self.prop_checks["is_weapon"].grid(row=0, column=0, padx=10, pady=(8, 6), sticky="w")
        # Row 1: Damage / Range with numeric combos allowing typing
        ctk.CTkLabel(fr, text="Damage:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        dmg_values = [str(v) for v in range(10, 101, 10)]
        self.damage_entry = ctk.CTkComboBox(fr, values=dmg_values, state="disabled", width=90)
        self._attach_entry_like_methods_to_combobox(self.damage_entry)
        self.damage_entry.grid(row=1, column=1, padx=(6, 10), pady=8, sticky="w")
        self.damage_entry.bind("<KeyRelease>", self._on_user_change)
        self.damage_entry.bind("<FocusOut>", lambda e: self._clamp_int_0_100(self.damage_entry))

        ctk.CTkLabel(fr, text="Range:").grid(row=1, column=2, padx=10, pady=8, sticky="e")
        self.range_entry = ctk.CTkComboBox(fr, values=dmg_values, state="disabled", width=90)
        self._attach_entry_like_methods_to_combobox(self.range_entry)
        self.range_entry.grid(row=1, column=3, padx=(6, 10), pady=8, sticky="w")
        self.range_entry.bind("<KeyRelease>", self._on_user_change)
        self.range_entry.bind("<FocusOut>", lambda e: self._clamp_int_0_100(self.range_entry))

        # Help bindings
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "is_weapon": "Weapon\n\nItem can be used as a weapon.",
                "damage": "Damage\n\nBase damage dealt by this weapon.",
                "range": "Range\n\nEffective range for this weapon.",
            })
            self._register_help(self.prop_checks.get("is_weapon"), "is_weapon")
            self._register_help(self.damage_entry, "damage")
            self._register_help(self.range_entry, "range")
        except Exception:
            pass

    def _build_fantasy_magic_tab(self):
        tab = self._prop_tabs["Fantasy & Magic"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        props = [
            ("is_magical", "Magical"),
            ("is_cursed", "Cursed"),
            ("is_enchanted", "Enchanted"),
            ("requires_attunement", "Requires Attunement"),
            ("is_quest_item", "Quest Item"),
        ]
        self._create_checks_grid(fr, props)

    def _build_crafting_social_tab(self):
        tab = self._prop_tabs["Crafting & Social"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        props = [
            ("is_crafting_material", "Crafting Material"),
            ("has_blueprint", "Has Blueprint"),
            ("is_owned", "Owned"),
            ("is_illegal", "Illegal"),
            ("is_evidence", "Evidence"),
            ("is_tradeable", "Tradeable"),
            ("is_craftable", "Craftable"),
        ]
        self._create_checks_grid(fr, props)

    def _build_storage_tab(self):
        tab = self._prop_tabs["Storage"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        # Left ~30%, Right ~70%
        fr.grid_columnconfigure(0, weight=1)
        fr.grid_columnconfigure(1, weight=2)
        fr.grid_rowconfigure(1, weight=1)  # contents box expands

        # Row 0: storage toggle left; capacity + liquids grouped on right
        self.prop_checks["is_storage"] = ctk.CTkCheckBox(
            fr, text="Is Storage", command=lambda: [self.toggle_storage_fields(), self._mark_dirty()]
        )
        self.prop_checks["is_storage"].grid(row=0, column=0, padx=10, pady=(8, 6), sticky="w")

        right_r0 = ctk.CTkFrame(fr, fg_color="transparent")
        right_r0.grid(row=0, column=1, sticky="ew", padx=10, pady=(8, 6))
        right_r0.grid_columnconfigure(0, weight=0)
        right_r0.grid_columnconfigure(1, weight=0)
        right_r0.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(right_r0, text="Capacity:").grid(row=0, column=0, padx=(0,6), pady=0, sticky="e")
        self.storage_capacity_entry = ctk.CTkEntry(right_r0, width=90, state="disabled")
        self.storage_capacity_entry.grid(row=0, column=1, padx=(0,10), pady=0, sticky="w")
        self.storage_capacity_entry.bind("<KeyRelease>", self._on_user_change)
        self.prop_checks["can_store_liquids"] = ctk.CTkCheckBox(right_r0, text="Can Store Liquids", state="disabled", command=self._on_user_change)
        self.prop_checks["can_store_liquids"].grid(row=0, column=2, padx=(6,0), pady=0, sticky="e")

        # Row 1: contents area (expands)
        self.storage_contents_text = ctk.CTkTextbox(fr, height=180, state="disabled")
        self.storage_contents_text.grid(row=1, column=0, padx=10, pady=(6, 6), sticky="nsew")

        # Row 2: item selector and actions
        right_stack = ctk.CTkFrame(fr, fg_color="transparent")
        right_stack.grid(row=1, column=1, padx=10, pady=(6, 6), sticky="n")
        ctk.CTkLabel(right_stack, text="Item:").pack(padx=0, pady=(0,6))
        self.storage_item_select = ctk.CTkComboBox(right_stack, values=self.object_ids, state="disabled", width=280)
        self.storage_item_select.pack(padx=0, pady=(0,8))
        btns = ctk.CTkFrame(right_stack, fg_color="transparent")
        btns.pack(padx=0, pady=(0,0))
        self.storage_add_button = ctk.CTkButton(btns, text="Add", width=70, state="disabled", command=self._on_storage_add)
        self.storage_add_button.pack(side="left", padx=(0,8))
        self.storage_remove_button = ctk.CTkButton(btns, text="Remove", width=90, state="disabled", command=self._on_storage_remove)
        self.storage_remove_button.pack(side="left")
        
        # Internal list model for contents
        self.storage_contents: list[str] = []

        # Help bindings
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "is_storage": "Is Storage\n\nThis object can contain other items.",
                "storage_capacity": "Capacity\n\nMaximum items/units this container holds.",
                "can_store_liquids": "Stores Liquids\n\nContainer can hold liquids.",
                "storage_contents": "Storage Contents\n\nList of initial items inside this container.",
            })
            self._register_help(self.prop_checks.get("is_storage"), "is_storage")
            self._register_help(self.storage_capacity_entry, "storage_capacity")
            self._register_help(self.prop_checks.get("can_store_liquids"), "can_store_liquids")
            self._register_help(self.storage_contents_text, "storage_contents")
        except Exception:
            pass

    def _build_locking_tab(self):
        tab = self._prop_tabs["Locking"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        fr.grid_columnconfigure(0, weight=0)
        fr.grid_columnconfigure(1, weight=1)

        # Row 0: Is Locked toggle
        self.is_locked_checkbox = ctk.CTkCheckBox(fr, text="Is Locked?", command=lambda: [self.toggle_lock_fields(), self._mark_dirty()])
        self.is_locked_checkbox.grid(row=0, column=0, padx=10, pady=(10, 6), sticky="w")

        # Row 1: Lock Type
        ctk.CTkLabel(fr, text="Lock Type:").grid(row=1, column=0, padx=10, pady=6, sticky="e")
        self.lock_type_combo = ctk.CTkComboBox(fr, values=["", "key", "code", "biometric"], state="disabled", width=160, command=self._on_user_change)
        self.lock_type_combo.grid(row=1, column=1, padx=10, pady=6, sticky="w")

        # Row 2: Lock Code
        ctk.CTkLabel(fr, text="Lock Code:").grid(row=2, column=0, padx=10, pady=6, sticky="e")
        self.lock_code_entry = ctk.CTkEntry(fr, state="disabled", width=200)
        self.lock_code_entry.grid(row=2, column=1, padx=10, pady=6, sticky="w")
        self.lock_code_entry.bind("<KeyRelease>", self._on_user_change)

        # Row 3: Key Object ID
        ctk.CTkLabel(fr, text="Key Object ID:").grid(row=3, column=0, padx=10, pady=6, sticky="e")
        try:
            key_ids = [""] + self.data_manager.get_key_object_ids()
        except Exception:
            key_ids = [""]
        self.lock_key_combo = ctk.CTkComboBox(fr, values=key_ids, state="disabled", width=240, command=self._on_user_change)
        self.lock_key_combo.grid(row=3, column=1, padx=10, pady=6, sticky="w")

        # Help bindings
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "is_locked": "Is Locked\n\nInitial lock state. Requires Openable/Closable to be meaningful.",
                "lock_type": "Lock Type\n\nMechanism: key, code, or biometric.",
                "lock_code": "Lock Code\n\nRequired code if Lock Type is 'code'.",
                "lock_key_id": "Key Object ID\n\nSpecific key object if Lock Type is 'key'.",
            })
            self._register_help(self.is_locked_checkbox, "is_locked")
            self._register_help(self.lock_type_combo, "lock_type")
            self._register_help(self.lock_code_entry, "lock_code")
            self._register_help(self.lock_key_combo, "lock_key_id")
        except Exception:
            pass

    def toggle_lock_fields(self):
        enable = bool(self.is_locked_checkbox.get() if hasattr(self, "is_locked_checkbox") else 0)
        state = "normal" if enable else "disabled"
        try:
            if hasattr(self, "lock_type_combo"): self.lock_type_combo.configure(state=state)
            if hasattr(self, "lock_code_entry"): self.lock_code_entry.configure(state=state)
            if hasattr(self, "lock_key_combo"): self.lock_key_combo.configure(state=state)
        except Exception:
            pass

    def _build_extended_tab(self):
        tab = self._prop_tabs["Extended"]
        fr = ctk.CTkFrame(tab)
        fr.pack(fill="both", expand=True, padx=10, pady=5)
        self._prep_props_grid(fr)
        props = [
            ("dialogue_related", "Dialogue Related"),
            ("quest_giver", "Quest Giver"),
            # Use is_tradable in Crafting & Social tab; avoid duplicate here
            ("follows_player", "Follows Player"),
            ("hostile", "Hostile"),
            ("environmental_hazard", "Environmental Hazard"),
            ("audio_emitter", "Audio Emitter"),
            ("decorative", "Decorative"),
            ("collectible", "Collectible"),
            ("lore_item", "Lore Item"),
        ]
        self._create_checks_grid(fr, props)

    def _create_checks_grid(self, parent, props, start_index: int = 0):
        """Lay out boolean properties in a 4-column grid and register in self.prop_checks."""
        PADX, PADY = 14, 10
        max_row = 0
        for i, (key, label) in enumerate(props):
            row = (start_index + i) // 4
            col = (start_index + i) % 4
            cb = ctk.CTkCheckBox(parent, text=label, command=self._mark_dirty)
            cb.grid(row=row, column=col, padx=PADX, pady=PADY, sticky="w")
            self.prop_checks[key] = cb
            # Ensure help exists for every checkbox
            self._ensure_help_registry()
            label_text = label
            if key not in self._help_texts:
                self._help_texts[key] = f"{label_text}\n\nToggle this property: {label_text.lower()}."
            self._register_help(cb, key)
            max_row = max(max_row, row)
        # Add a stretchy row to avoid top-left cramming and use space nicely
        parent.grid_rowconfigure(max_row + 1, weight=1)

    def toggle_wearability_fields(self):
        self.toggle_wearability_fields_with_arg()

    def toggle_wearability_fields_with_arg(self, *, enable: bool | None = None):
        if enable is None:
            enable = bool(self.prop_checks.get("is_wearable").get() if self.prop_checks.get("is_wearable") else 0)
        state = "normal" if enable else "disabled"
        if hasattr(self, "wear_area_combo"):
            self.wear_area_combo.configure(state=state)
        if hasattr(self, "wear_layer_entry"):
            self.wear_layer_entry.configure(state=state)

    def toggle_weapon_fields(self):
        self.toggle_weapon_fields_with_arg()

    def toggle_weapon_fields_with_arg(self, *, enable: bool | None = None):
        if enable is None:
            enable = bool(self.prop_checks.get("is_weapon").get() if self.prop_checks.get("is_weapon") else 0)
        state = "normal" if enable else "disabled"
        if hasattr(self, "damage_entry"):
            self.damage_entry.configure(state=state)
        if hasattr(self, "range_entry"):
            self.range_entry.configure(state=state)

    def toggle_storage_fields(self):
        self.toggle_storage_fields_with_arg()

    def toggle_storage_fields_with_arg(self, *, enable: bool | None = None):
        if enable is None:
            enable = bool(self.prop_checks.get("is_storage").get() if self.prop_checks.get("is_storage") else 0)
        state = "normal" if enable else "disabled"
        if hasattr(self, "storage_capacity_entry"):
            self.storage_capacity_entry.configure(state=state)
        # alias for liquids checkbox
        try:
            self.storage_liquids_check = self.prop_checks.get("can_store_liquids")
            if self.storage_liquids_check:
                self.storage_liquids_check.configure(state=state)
        except Exception:
            pass
        # Keep contents textbox readable; do not disable its state here
        if hasattr(self, "storage_item_select"):
            self.storage_item_select.configure(state=state)
        if hasattr(self, "storage_add_button"):
            self.storage_add_button.configure(state=state)
        if hasattr(self, "storage_remove_button"):
            self.storage_remove_button.configure(state=state)

    def _clamp_int(self, value_str: str, lo: int, hi: int) -> str:
        try:
            v = int(str(value_str).strip())
        except Exception:
            return ""
        return str(max(lo, min(hi, v)))

    def _bind_numeric_clamp(self):
        # Weapons (0..100)
        if hasattr(self, "damage_entry") and self.damage_entry is not None:
            try:
                self.damage_entry.bind("<FocusOut>", lambda e: self.damage_entry.set(self._clamp_int(self.damage_entry.get(), 0, 100)))
            except Exception:
                pass
        if hasattr(self, "range_entry") and self.range_entry is not None:
            try:
                self.range_entry.bind("<FocusOut>", lambda e: self.range_entry.set(self._clamp_int(self.range_entry.get(), 0, 100)))
            except Exception:
                pass
        # Consumables
        if hasattr(self, "cons_health_combo"):
            self.cons_health_combo.bind("<FocusOut>", lambda e: self.cons_health_combo.set(self._clamp_int(self.cons_health_combo.get(), -100, 100)))
        if hasattr(self, "cons_per_turn_combo"):
            self.cons_per_turn_combo.bind("<FocusOut>", lambda e: self.cons_per_turn_combo.set(self._clamp_int(self.cons_per_turn_combo.get(), -50, 50)))
        if hasattr(self, "cons_duration_combo"):
            self.cons_duration_combo.bind("<FocusOut>", lambda e: self.cons_duration_combo.set(self._clamp_int(self.cons_duration_combo.get(), 1, 20)))

    def toggle_consumable_fields(self):
        is_consumable = self.prop_checks.get("is_consumable").get() if self.prop_checks.get("is_consumable") else 0
        state = "normal" if is_consumable else "disabled"
        try:
            self.cons_health_combo.configure(state=state)
            self.cons_per_turn_combo.configure(state=state)
            self.cons_duration_combo.configure(state=state)
            if not is_consumable:
                # Disable and clear values
                self.cons_health_combo.set("")
                self.cons_per_turn_combo.set("")
                self.cons_duration_combo.set("")
                self._consumables_meta = {"health_delta": None, "per_turn_delta": None, "duration_turns": None}
        except Exception:
            pass

    def _refresh_storage_contents_text(self):
        try:
            self.storage_contents_text.configure(state="normal")
            self.storage_contents_text.delete("1.0", "end")
            if self.storage_contents:
                for oid in self.storage_contents:
                    self.storage_contents_text.insert("end", f"{oid}\n")
            self.storage_contents_text.configure(state="disabled")
        except Exception:
            pass

    def _on_storage_add(self):
        item_id = (self.storage_item_select.get() or "").strip()
        if not item_id:
            return
        if item_id not in self.storage_contents:
            self.storage_contents.append(item_id)
            self._refresh_storage_contents_text()
            self._on_user_change()

    def _on_storage_remove(self):
        item_id = (self.storage_item_select.get() or "").strip()
        if not item_id:
            return
        if item_id in self.storage_contents:
            self.storage_contents.remove(item_id)
            self._refresh_storage_contents_text()
            self._on_user_change()

    def gather_data_from_fields(self):
        """Gathers all data from the form fields into a dictionary."""
        data = {}
        
        # Basic Info fields
        data["id"] = self.object_id_entry.get().strip()
        data["name"] = self.name_entry.get().strip()
        data["is_plural"] = self.is_plural_checkbox.get()
        data["synonyms"] = [s.strip() for s in self.synonyms_entry.get().split(",") if s.strip()]
        data["category"] = self.category_combobox.get()
        data["location"] = self.location_combobox.get()
        data["area"] = self.area_combobox.get()
        
        # Weight and Size
        weight_val = self.weight_entry.get().strip()
        data["weight"] = float(weight_val) if weight_val else None
        
        size_val = self.size_entry.get().strip()
        data["size"] = float(size_val) if size_val else None
        
        data["description"] = self.description_textbox.get("1.0", "end").strip()
        
        # Properties from checkboxes
        for prop_key, checkbox in self.prop_checks.items():
            data[prop_key] = checkbox.get()
        
        # Detail fields for special properties
        if data.get("is_wearable"):
            data["wear_area"] = self.wear_area_combo.get()
            try:
                data["wear_layer"] = int(self.wear_layer_entry.get()) if (self.wear_layer_entry.get() or "").strip() else None
            except Exception:
                data["wear_layer"] = None
        
        if data.get("is_weapon"):
            damage_val = self.damage_entry.get().strip()
            data["damage"] = float(damage_val) if damage_val else None
            
            range_val = self.range_entry.get().strip()
            data["range"] = float(range_val) if range_val else None
        
        if data.get("is_storage"):
            capacity_val = self.storage_capacity_entry.get().strip()
            data["storage_capacity"] = float(capacity_val) if capacity_val else None
            # Storage contents as simple list of IDs
            data["storage_contents"] = list(self.storage_contents)
        else:
            data["storage_contents"] = []
        
        return data

    def populate_fields(self, data: dict) -> None:
        """Populate ALL UI fields from a loaded object dict (mirrors old editor behavior)."""
        if not data:
            return
        if not hasattr(self, "_suppress_dirty"):
            self._suppress_dirty = False
        self._suppress_dirty = True
        try:
            # Basic Info
            # Temporarily enable ID field to set text, then disable to keep it read-only
            try:
                self.object_id_entry.configure(state="normal")
            except Exception:
                pass
            self.object_id_entry.delete(0, "end"); self.object_id_entry.insert(0, data.get("id", "") or "")
            self.object_id_entry.configure(state="disabled")
            self.name_entry.delete(0, "end");      self.name_entry.insert(0, data.get("name", "") or "")
            self.is_plural_checkbox.select() if data.get("is_plural") else self.is_plural_checkbox.deselect()
            self.category_combobox.set(data.get("category", "") or "")
            self.synonyms_entry.delete(0, "end"); self.synonyms_entry.insert(0, ", ".join(data.get("synonyms", []) or []))
            self.description_textbox.delete("1.0", "end"); self.description_textbox.insert("1.0", data.get("description") or "")
            self.weight_entry.delete(0, "end"); self.weight_entry.insert(0, str(data.get("weight", "") or ""))
            self.size_entry.delete(0, "end");   self.size_entry.insert(0, str(data.get("size", "") or ""))
            # Count (int) and Object # (read-only)
            if hasattr(self, "object_count_entry"):
                try:
                    self.object_count_entry.configure(state="normal")
                    self.object_count_entry.delete(0, "end")
                    # Prefer object_number; fallback to legacy count
                    onum = data.get("object_number")
                    if not isinstance(onum, int):
                        legacy = data.get("count")
                        onum = legacy if isinstance(legacy, int) else ""
                    if isinstance(onum, int):
                        self.object_count_entry.insert(0, str(onum))
                    self.object_count_entry.configure(state="disabled")
                except Exception:
                    pass
            # Timestamps
            try:
                self.created_at_entry.configure(state="normal")
                self.created_at_entry.delete(0, "end")
                if data.get("created_at"):
                    self.created_at_entry.insert(0, data.get("created_at"))
                self.created_at_entry.configure(state="disabled")
            except Exception:
                pass
            try:
                self.updated_at_entry.configure(state="normal")
                self.updated_at_entry.delete(0, "end")
                if data.get("updated_at"):
                    self.updated_at_entry.insert(0, data.get("updated_at"))
                self.updated_at_entry.configure(state="disabled")
            except Exception:
                pass

            # Location / Area
            room_id, area_id = (None, None)
            if hasattr(self.data_manager, "find_object_location"):
                room_id, area_id = self.data_manager.find_object_location(data.get("id", ""))
            self.location_combobox.set(room_id or "")
            self._update_area_options_for_room(room_id)
            if area_id:
                try: self.area_combobox.set(area_id)
                except Exception: pass

            # Properties
            props = data.get("properties", {}) or {}
            # Set all known property checkboxes
            for key, chk in getattr(self, "prop_checks", {}).items():
                if props.get(key): chk.select()
                else: chk.deselect()
            # Initially Visible? (default True if missing)
            try:
                if hasattr(self, "initial_visible_checkbox"):
                    if data.get("initial_state", True):
                        self.initial_visible_checkbox.select()
                    else:
                        self.initial_visible_checkbox.deselect()
            except Exception:
                pass

            # Wearability
            is_wearable = bool(props.get("is_wearable"))
            self.toggle_wearability_fields_with_arg(enable=is_wearable)
            if hasattr(self, "wear_area_combo"):  self.wear_area_combo.set((props.get("wear_area") or ""))
            if hasattr(self, "wear_layer_entry"): self.wear_layer_entry.set(str(props.get("wear_layer") or "")) if hasattr(self.wear_layer_entry, "set") else None

            # Weapons
            is_weapon = bool(props.get("is_weapon"))
            self.toggle_weapon_fields_with_arg(enable=is_weapon)
            if hasattr(self, "damage_entry"):
                if props.get("damage") is not None:
                    if hasattr(self.damage_entry, "set"): self.damage_entry.set(str(props.get("damage")))
                else:
                    if hasattr(self.damage_entry, "set"): self.damage_entry.set("")
            if hasattr(self, "range_entry"):
                if props.get("range") is not None:
                    if hasattr(self.range_entry, "set"): self.range_entry.set(str(props.get("range")))
                else:
                    if hasattr(self.range_entry, "set"): self.range_entry.set("")

            # Storage
            is_storage = bool(props.get("is_storage"))
            self.toggle_storage_fields_with_arg(enable=is_storage)
            if hasattr(self, "storage_capacity_entry"):
                self.storage_capacity_entry.delete(0, "end")
                if props.get("storage_capacity") is not None:
                    self.storage_capacity_entry.insert(0, str(props.get("storage_capacity")))
            try:
                self.storage_liquids_check = self.prop_checks.get("can_store_liquids")
                if self.storage_liquids_check:
                    self.storage_liquids_check.select() if props.get("can_store_liquids") else self.storage_liquids_check.deselect()
            except Exception:
                pass
            contents = data.get("storage_contents", []) or []
            if hasattr(self, "storage_contents_text"):
                try:
                    self.storage_contents_text.configure(state="normal")
                    self.storage_contents_text.delete("1.0", "end")
                    self.storage_contents_text.insert("1.0", "\n".join([str(x) for x in contents]))
                    self.storage_contents_text.configure(state="disabled")
                except Exception:
                    pass

            # Consumables meta (optional)
            if not hasattr(self, "_consumables_meta"):
                self._consumables_meta = {"health_delta": None, "per_turn_delta": None, "duration_turns": None}
            meta = data.get("meta", {}) or {}
            cmeta = meta.get("consumables", {}) if isinstance(meta, dict) else {}
            hd = cmeta.get("health_delta") if isinstance(cmeta, dict) else data.get("health_delta")
            pt = cmeta.get("per_turn_delta") if isinstance(cmeta, dict) else data.get("per_turn_delta")
            du = cmeta.get("duration_turns") if isinstance(cmeta, dict) else data.get("duration_turns")
            self._consumables_meta.update({"health_delta": hd, "per_turn_delta": pt, "duration_turns": du})
            try:
                if hasattr(self, "cons_health_combo") and hd is not None: self.cons_health_combo.set(str(hd))
                if hasattr(self, "cons_per_turn_combo")   and pt is not None:   self.cons_per_turn_combo.set(str(pt))
                if hasattr(self, "cons_duration_combo")   and du is not None:   self.cons_duration_combo.set(str(du))
            except Exception:
                pass
        finally:
            self._suppress_dirty = False
            self._dirty = False
            self._update_save_button_state()
            self.update_preview_event()

    def clear_all_fields(self) -> None:
        try:
            # Clear basic fields
            # Keep ID read-only by default when clearing
            self.object_id_entry.configure(state="normal")
            self.object_id_entry.delete(0, "end")
            self.object_id_entry.configure(state="disabled")
            self.name_entry.delete(0, "end")
            self.is_plural_checkbox.deselect()
            self.synonyms_entry.delete(0, "end")
            self.category_combobox.set("")
            self.location_combobox.set("")
            self.area_combobox.set("")
            self.weight_entry.delete(0, "end")
            self.size_entry.delete(0, "end")
            self.description_textbox.delete("1.0", "end")
            # Clear properties
            for _, cb in self.prop_checks.items():
                try:
                    cb.deselect()
                except Exception:
                    pass
            # Wear/Weapon/Storage fields
            try:
                self.wear_area_combo.set("")
                self.wear_layer_entry.set("")
            except Exception:
                pass
            try:
                self.damage_entry.set("")
                self.range_entry.set("")
            except Exception:
                pass
            self.storage_capacity_entry.delete(0, "end")
            self.storage_contents = []
            self._refresh_storage_contents_text()
            self.toggle_wearability_fields()
            self.toggle_weapon_fields()
            self.toggle_storage_fields()
            self._consumables_meta = {"health_delta": None, "per_turn_delta": None, "duration_turns": None}
        except Exception:
            pass

    def update_preview_event(self):
        """Updates the YAML preview when properties change."""
        try:
            data = self._apply_save_transforms(self._collect_object_dict())
            logger.debug(f"Preview updated with data: {data}")
            self._run_validation_and_update_panel(data)
            self._update_yaml_preview(data)
        except Exception as e:
            logger.error(f"Error updating preview: {e}")

    def refresh_counts(self):
        """Update per-object Count entry and the Total Objects label."""
        # total objects in the library
        if hasattr(self, "total_objects_label"):
            try:
                total = len(self.data_manager.get_object_ids())
                self.total_objects_label.configure(text=str(total))
            except Exception:
                pass
        # Per-object Count box is handled when populating a specific object

    def _collect_object_dict(self) -> dict:
        """Build a minimal object dict from UI, omitting false/empty values."""
        obj: dict = {}
        # Basic Info
        _id = (self.object_id_entry.get() or "").strip()
        if _id:
            obj["id"] = _id
        _name = (self.name_entry.get() or "").strip()
        if _name:
            obj["name"] = _name
        if self.is_plural_checkbox.get() == 1:
            obj["is_plural"] = True
        desc = self.description_textbox.get("1.0", "end-1c").strip()
        if desc:
            obj["description"] = desc
        syn = (self.synonyms_entry.get() or "").strip()
        if syn:
            syn_list = [s.strip() for s in syn.split(",") if s.strip()]
            if syn_list:
                obj["synonyms"] = syn_list
        cat = (self.category_combobox.get() or "").strip()
        if cat:
            obj["category"] = cat
        w = (self.weight_entry.get() or "").strip()
        if w:
            try:
                obj["weight"] = float(w) if "." in w else int(w)
            except Exception:
                pass
        sz = (self.size_entry.get() or "").strip()
        if sz:
            try:
                obj["size"] = float(sz) if "." in sz else int(sz)
            except Exception:
                pass
        # Location & Area
        loc = (self.location_combobox.get() or "").strip()
        if loc:
            obj["location"] = loc
        area = (self.area_combobox.get() or "").strip()
        if area:
            obj["area_location"] = area
        # Count
        # No longer write legacy 'count' field
        # Timestamps from UI (if present)
        try:
            ca = (self.created_at_entry.get() or "").strip()
            if ca:
                obj["created_at"] = ca
        except Exception:
            pass
        try:
            ua = (self.updated_at_entry.get() or "").strip()
            if ua:
                obj["updated_at"] = ua
        except Exception:
            pass
        # Object number (read-only field)
        try:
            on_raw = (self.object_count_entry.get() or "").strip()
            if on_raw:
                onum = int(on_raw)
                if onum > 0:
                    obj["object_number"] = onum
        except Exception:
            pass
        # Properties
        props: dict = {}
        for key, chk in getattr(self, "prop_checks", {}).items():
            if chk.get() == 1:
                props[key] = True
        # Initially Visible? -> write initial_state: false when unchecked
        try:
            if hasattr(self, "initial_visible_checkbox") and self.initial_visible_checkbox.get() == 0:
                obj["initial_state"] = False
        except Exception:
            pass
        # Is Open? as top-level state (lives in Core Behaviours UI)
        try:
            if hasattr(self, "is_open_checkbox") and self.is_open_checkbox.get() == 1:
                obj["is_open"] = True
        except Exception:
            pass
        # Is Open? (top-level)
        try:
            if hasattr(self, "is_open_checkbox") and self.is_open_checkbox.get() == 1:
                obj["is_open"] = True
        except Exception:
            pass
        # Wearability
        if props.get("is_wearable"):
            wa = (self.wear_area_combo.get() if hasattr(self, "wear_area_combo") else "") or ""
            wl = (self.wear_layer_entry.get() if hasattr(self, "wear_layer_entry") else "") or ""
            if wa.strip():
                props["wear_area"] = wa.strip()
            if str(wl).strip():
                try:
                    wl_int = int(str(wl).strip())
                    props["wear_layer"] = wl_int
                except Exception:
                    pass
        # Weapons
        if props.get("is_weapon"):
            if hasattr(self, "damage_entry"):
                dmg = (self.damage_entry.get() or "").strip()
                if dmg:
                    try:
                        props["damage"] = int(dmg)
                    except Exception:
                        pass
            if hasattr(self, "range_entry"):
                rng = (self.range_entry.get() or "").strip()
                if rng:
                    try:
                        props["range"] = int(rng)
                    except Exception:
                        pass
        # Storage
        if props.get("is_storage"):
            cap = (self.storage_capacity_entry.get() or "").strip() if hasattr(self, "storage_capacity_entry") else ""
            if cap:
                try:
                    props["storage_capacity"] = float(cap) if "." in cap else int(cap)
                except Exception:
                    pass
            try:
                if hasattr(self, "storage_liquids_check") and self.storage_liquids_check and self.storage_liquids_check.get() == 1:
                    props["can_store_liquids"] = True
            except Exception:
                pass
        if props:
            obj["properties"] = props
        # Top-level storage_contents
        if hasattr(self, "storage_contents_text"):
            try:
                contents = self.storage_contents_text.get("1.0", "end-1c").splitlines()
                contents = [c.strip() for c in contents if c.strip()]
                if contents:
                    obj["storage_contents"] = contents
            except Exception:
                pass
        # Locking (top-level)
        try:
            if hasattr(self, "is_locked_checkbox") and self.is_locked_checkbox.get() == 1:
                obj["is_locked"] = True
            if hasattr(self, "lock_type_combo"):
                lt = (self.lock_type_combo.get() or "").strip()
                if lt:
                    obj["lock_type"] = lt
            if hasattr(self, "lock_code_entry"):
                lc = (self.lock_code_entry.get() or "").strip()
                if lc:
                    obj["lock_code"] = lc
            if hasattr(self, "lock_key_combo"):
                lk = (self.lock_key_combo.get() or "").strip()
                if lk:
                    obj["lock_key_id"] = lk
        except Exception:
            pass
        # States (non-locking)
        try:
            if hasattr(self, "power_state_combo"):
                ps = (self.power_state_combo.get() or "").strip()
                if ps:
                    obj["power_state"] = ps
            if hasattr(self, "state_desc_textbox"):
                raw = self.state_desc_textbox.get("1.0", "end-1c").strip()
                if raw:
                    lines = [ln for ln in raw.splitlines() if ":" in ln]
                    sd = {}
                    for ln in lines:
                        k, v = ln.split(":", 1)
                        k = k.strip(); v = v.strip()
                        if k:
                            sd[k] = v
                    if sd:
                        obj["state_descriptions"] = sd
        except Exception:
            pass
        # Interactions
        try:
            inter = {}
            if hasattr(self, "inter_req_state_entry"):
                csv = (self.inter_req_state_entry.get() or "").strip()
                if csv:
                    inter["required_state"] = [s.strip() for s in csv.split(",") if s.strip()]
            if hasattr(self, "inter_req_items_entry"):
                csv = (self.inter_req_items_entry.get() or "").strip()
                if csv:
                    inter["required_items"] = [s.strip() for s in csv.split(",") if s.strip()]
            if hasattr(self, "inter_actions_entry"):
                csv = (self.inter_actions_entry.get() or "").strip()
                if csv:
                    inter["primary_actions"] = [s.strip() for s in csv.split(",") if s.strip()]
            if hasattr(self, "inter_effects_text"):
                eff_raw = self.inter_effects_text.get("1.0", "end-1c").strip()
                if eff_raw:
                    eff = {k.strip(): v.strip() for line in eff_raw.splitlines() if ":" in line for k, v in [line.split(":", 1)]}
                    if eff:
                        inter["effects"] = eff
            if hasattr(self, "inter_success_text"):
                sm = self.inter_success_text.get("1.0", "end-1c").strip()
                if sm:
                    inter["success_message"] = sm
            if hasattr(self, "inter_failure_text"):
                fm = self.inter_failure_text.get("1.0", "end-1c").strip()
                if fm:
                    inter["failure_message"] = fm
            if inter:
                obj["interaction"] = inter
        except Exception:
            pass
        # Digital Content
        try:
            if hasattr(self, "digital_content_text"):
                dc_raw = self.digital_content_text.get("1.0", "end-1c").strip()
                if dc_raw:
                    obj["digital_content"] = self._parse_digital_multiline_to_dict(dc_raw)
        except Exception:
            pass
        # Optional Consumables meta (kept out of schema)
        if hasattr(self, "_consumables_meta"):
            hd = self._consumables_meta.get("health_delta")
            pt = self._consumables_meta.get("per_turn_delta")
            du = self._consumables_meta.get("duration_turns")
            meta_block = {}
            con_block = {}
            if hd not in (None, ""):
                try: con_block["health_delta"] = int(hd)
                except Exception: pass
            if pt not in (None, ""):
                try: con_block["per_turn_delta"] = int(pt)
                except Exception: pass
            if du not in (None, ""):
                try: con_block["duration_turns"] = int(du)
                except Exception: pass
            if con_block:
                meta_block["consumables"] = con_block
            if meta_block:
                obj["meta"] = meta_block
        return obj

    def create_yaml_preview_tab(self, tab):
        """Creates the YAML Preview tab with a polished, theme-aligned layout."""
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Outer wrapper for consistent padding
        wrap = ctk.CTkFrame(tab, fg_color="transparent")
        wrap.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        # Header bar with title, current object id, and actions
        header_bar = ctk.CTkFrame(wrap)
        header_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
        header_bar.grid_columnconfigure(0, weight=1)

        title_font = ctk.CTkFont(size=14, weight="bold")
        self.yaml_header_label = ctk.CTkLabel(header_bar, text="YAML Preview - reflects saved data", font=title_font)
        self.yaml_header_label.grid(row=0, column=0, padx=10, pady=8, sticky="w")

        self.copy_yaml_btn = ctk.CTkButton(header_bar, text="Copy", width=70, command=self._copy_yaml_preview_to_clipboard)
        self.copy_yaml_btn.grid(row=0, column=1, padx=10, pady=8, sticky="e")

        # Framed preview area for visual structure
        preview_frame = ctk.CTkFrame(wrap, corner_radius=8, border_width=1)
        preview_frame.grid(row=1, column=0, sticky="nsew")
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        mono_font = ctk.CTkFont(family="Consolas", size=13)
        self.yaml_preview_text = ctk.CTkTextbox(preview_frame, state="disabled", font=mono_font, wrap="none")
        self.yaml_preview_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        try:
            # Improve contrast/readability on dark theme
            self.yaml_preview_text.configure(text_color="white")
        except Exception:
            pass
        # Register help for YAML preview area and controls
        try:
            self._ensure_help_registry()
            self._help_texts.update({
                "yaml_header": "YAML Preview\n\nShows exactly what will be saved to objects.yaml for the current object.",
                "yaml_copy": "Copy YAML\n\nCopies the preview text to the clipboard.",
                "yaml_preview": "Preview Text\n\nRead-only YAML representation. Hover to review formatting; click elsewhere to resume hover help.",
            })
            self._register_help(self.yaml_header_label, "yaml_header")
            self._register_help(self.copy_yaml_btn, "yaml_copy")
            self._register_help(self.yaml_preview_text, "yaml_preview")
        except Exception:
            pass

    def _update_yaml_preview(self, data: dict) -> None:
        """Render the current object dict as YAML exactly as saved (single-object view)."""
        try:
            if not hasattr(self, "yaml_preview_text"):
                return
            # Build payload matching objects.yaml structure
            payload = {"objects": [data] if data else []}
            # Dump with ruamel.yaml preserving nice indentation
            yaml = YAML()
            yaml.indent(mapping=2, sequence=4, offset=2)
            from io import StringIO
            s = StringIO()
            yaml.dump(payload, s)
            text = s.getvalue()
            # Update header with current object id if available
            try:
                obj_id = (data or {}).get("id") or "unsaved"
                self.yaml_header_label.configure(text=f"YAML Preview - {obj_id}")
            except Exception:
                pass
        except Exception as e:
            text = f"# Error generating YAML preview: {e}"
        try:
            self.yaml_preview_text.configure(state="normal")
            self.yaml_preview_text.delete("1.0", "end")
            self.yaml_preview_text.insert("1.0", text)
            self.yaml_preview_text.configure(state="disabled")
        except Exception:
            pass

    def _copy_yaml_preview_to_clipboard(self) -> None:
        try:
            if not hasattr(self, "yaml_preview_text"):
                return
            text = self.yaml_preview_text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(text)
            # Provide visual feedback on the button
            if hasattr(self, "copy_yaml_btn"):
                try:
                    self.copy_yaml_btn.configure(text="Copied")
                    # Revert back after a short delay
                    self.after(1200, lambda: self.copy_yaml_btn.configure(text="Copy"))
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_save_transforms(self, data: dict) -> dict:
        """Apply save-time transforms (object number, timestamps) to a shallow copy of data."""
        out = dict(data or {})
        # object_number from UI if missing
        try:
            if "object_number" not in out:
                on_text = (self.object_count_entry.get() or "").strip()
                if on_text:
                    on = int(on_text)
                    if on > 0:
                        out["object_number"] = on
        except Exception:
            pass
        # timestamps
        now = _now_utc_iso()
        try:
            created = (self.created_at_entry.get() or "").strip()
        except Exception:
            created = ""
        out["created_at"] = created or now
        out["updated_at"] = now
        return out

    def shutdown(self):
        """Perform any cleanup before the application closes."""
        logger.info("Shutting down NewObjectEditorFrame.")

    def create_attributes_tab(self, tab):
        """Create the Attributes tab with Interactions, Digital Content, and States sub-tabs."""
        container = ctk.CTkFrame(tab)
        container.pack(fill="both", expand=True, padx=10, pady=(10, 10))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.attributes_tabview = ctk.CTkTabview(container)
        self.attributes_tabview.grid(row=0, column=0, sticky="nsew")
        self.attributes_tabview.add("Interactions")
        self.attributes_tabview.add("Digital Content")
        self.attributes_tabview.add("States")
        self._normalize_tab_header_widths_smaller(self.attributes_tabview)

        self._build_interactions_attributes(self.attributes_tabview.tab("Interactions"))
        self._build_digital_attributes(self.attributes_tabview.tab("Digital Content"))
        self._build_states_attributes(self.attributes_tabview.tab("States"))

        # Attributes headers help
        try:
            self._register_segbutton_headers_help(self.attributes_tabview, "attr_hdr", "Attributes group.")
        except Exception:
            pass

        # Auto-register help for all controls inside each Attributes sub-tab
        try:
            tabs = getattr(self.attributes_tabview, "_tab_dict", {}) or {}
            for _name, frame in tabs.items():
                self._autowire_help_for_container(frame, "attr_auto", "Attributes control.")
        except Exception:
            pass

    def _build_interactions_attributes(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        PADY = (10, 8)
        ctk.CTkLabel(tab, text="Required State (CSV):").grid(row=0, column=0, padx=12, pady=PADY, sticky="w")
        self.inter_req_state_entry = ctk.CTkEntry(tab)
        self.inter_req_state_entry.grid(row=0, column=1, padx=10, pady=PADY, sticky="ew")
        self.inter_req_state_entry.bind("<KeyRelease>", self._on_user_change)

        ctk.CTkLabel(tab, text="Required Items (CSV):").grid(row=1, column=0, padx=12, pady=PADY, sticky="w")
        self.inter_req_items_entry = ctk.CTkEntry(tab)
        self.inter_req_items_entry.grid(row=1, column=1, padx=10, pady=PADY, sticky="ew")
        self.inter_req_items_entry.bind("<KeyRelease>", self._on_user_change)

        ctk.CTkLabel(tab, text="Primary Actions (CSV):").grid(row=2, column=0, padx=12, pady=PADY, sticky="w")
        self.inter_actions_entry = ctk.CTkEntry(tab)
        self.inter_actions_entry.grid(row=2, column=1, padx=10, pady=PADY, sticky="ew")
        self.inter_actions_entry.bind("<KeyRelease>", self._on_user_change)

        ctk.CTkLabel(tab, text="Effects (key:value per line):").grid(row=3, column=0, padx=12, pady=(10, 4), sticky="nw")
        self.inter_effects_text = ctk.CTkTextbox(tab, height=120)
        self.inter_effects_text.grid(row=3, column=1, padx=10, pady=(10, 4), sticky="nsew")
        self.inter_effects_text.bind("<KeyRelease>", self._on_user_change)

        ctk.CTkLabel(tab, text="Success Message:").grid(row=4, column=0, padx=12, pady=PADY, sticky="nw")
        self.inter_success_text = ctk.CTkTextbox(tab, height=60)
        self.inter_success_text.grid(row=4, column=1, padx=10, pady=PADY, sticky="ew")
        self.inter_success_text.bind("<KeyRelease>", self._on_user_change)

        ctk.CTkLabel(tab, text="Failure Message:").grid(row=5, column=0, padx=12, pady=PADY, sticky="nw")
        self.inter_failure_text = ctk.CTkTextbox(tab, height=60)
        self.inter_failure_text.grid(row=5, column=1, padx=10, pady=PADY, sticky="ew")
        self.inter_failure_text.bind("<KeyRelease>", self._on_user_change)
        tab.grid_rowconfigure(6, weight=1)

    def _build_digital_attributes(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tab, text="Digital Content (file_id: content, use --- as separator):").grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")
        self.digital_content_text = ctk.CTkTextbox(tab, height=200, wrap="word")
        self.digital_content_text.grid(row=1, column=0, padx=10, pady=(4, 10), sticky="nsew")
        self.digital_content_text.bind("<KeyRelease>", self._on_user_change)
        tab.grid_rowconfigure(1, weight=1)

    def _build_states_attributes(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Power State:").grid(row=0, column=0, padx=12, pady=(10, 8), sticky="w")
        self.power_state_combo = ctk.CTkComboBox(tab, values=["", "offline", "emergency", "main_power"], width=180, command=self._on_user_change)
        self.power_state_combo.grid(row=0, column=1, padx=10, pady=(10, 8), sticky="w")

        ctk.CTkLabel(tab, text="State Descriptions (state:description per line):").grid(row=1, column=0, padx=12, pady=(8, 4), sticky="nw")
        self.state_desc_textbox = ctk.CTkTextbox(tab, height=160)
        self.state_desc_textbox.grid(row=1, column=1, padx=10, pady=(8, 10), sticky="nsew")
        self.state_desc_textbox.bind("<KeyRelease>", self._on_user_change)
        tab.grid_rowconfigure(2, weight=1)

    def _parse_digital_multiline_to_dict(self, multiline_string: str) -> dict:
        content_dict = {}
        if not multiline_string:
            return content_dict
        current_key = None
        current_lines = []
        lines = multiline_string.splitlines()
        for i, line in enumerate(lines):
            is_sep = (line.strip() == '---')
            is_last = (i == len(lines) - 1)
            if is_sep or is_last:
                if current_key:
                    if is_last and not is_sep:
                        current_lines.append(line)
                    content_dict[current_key] = "\n".join(current_lines).strip()
                    current_key = None
                    current_lines = []
                continue
            if current_key is None and ':' in line:
                k, first = line.split(':', 1)
                current_key = k.strip()
                if current_key:
                    current_lines.append(first.strip())
                else:
                    current_lines.append(line)
                    current_key = None
            elif current_key is not None:
                current_lines.append(line)
        return content_dict

    def _parse_digital_dict_to_multiline(self, data_dict: Optional[dict]) -> str:
        if not data_dict:
            return ""
        out = []
        first = True
        for k, v in data_dict.items():
            if not first:
                out.append('---')
            out.append(f"{k}: {v}")
            first = False
        return "\n".join(out)

    def _run_validation_and_update_panel(self, data: dict) -> None:
        errors = []
        warnings = []
        if not data.get("id"):
            errors.append("Object ID is required.")
        if not data.get("name"):
            errors.append("Name is required.")
        props = data.get("properties", {}) or {}
        is_openable = bool(props.get("is_openable_closable"))
        is_open = bool(data.get("is_open"))
        is_locked = bool(data.get("is_locked"))
        if is_open and is_locked:
            errors.append("An object cannot be both Open and Locked.")
        if (is_open or is_locked) and not is_openable:
            errors.append("If Open or Locked, 'Openable/Closable' must be checked in Core Behaviours.")
        if is_locked:
            lt = (data.get("lock_type") or "").strip()
            lc = (data.get("lock_code") or "").strip()
            lk = (data.get("lock_key_id") or "").strip()
            if not lt:
                errors.append("When 'Is Locked' is checked, Lock Type is required.")
            else:
                if lt == "key" and not lk:
                    errors.append("Lock Type 'key' requires a Key Object ID.")
                if lt == "code" and not lc:
                    errors.append("Lock Type 'code' requires a Lock Code.")
        if data.get("power_state") and not props.get("requires_power"):
            warnings.append("Power State set but 'Requires Power' is not checked in Device & Tech.")
        parts = []
        if warnings:
            parts.append("Warnings:\n- " + "\n- ".join(warnings))
        if errors:
            parts.append("Blocking issues (cannot save):\n- " + "\n- ".join(errors))
        if not parts:
            parts.append("No issues detected.")
        try:
            self._set_validation_message("\n\n".join(parts))
        except Exception:
            pass
        self._validation_errors = errors
        self._validation_warnings = warnings
        self._update_save_button_state()
