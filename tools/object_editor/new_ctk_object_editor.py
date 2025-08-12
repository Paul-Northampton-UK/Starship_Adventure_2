# tools/object_editor/new_ctk_object_editor.py
import customtkinter as ctk
from loguru import logger
from tkinter import messagebox
from tools.object_editor.object_data_manager import ObjectDataManager
from engine.schemas import ObjectCategory
from typing import Optional

class NewObjectEditorFrame(ctk.CTkFrame):
    """
    A new and improved frame for creating, viewing, and editing game objects.
    """
    def __init__(self, master):
        super().__init__(master)
        logger.info("Initializing NewObjectEditorFrame...")
        self.data_manager = ObjectDataManager()
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
        self.tab_view.grid(row=0, column=0, sticky="nsew")
        self.setup_tabs()

        # --- Side Panel (Help/Validation) ---
        side_panel_frame = ctk.CTkFrame(self, width=250)
        side_panel_frame.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(5, 10))
        side_panel_frame.grid_rowconfigure(0, weight=1)
        side_panel_frame.grid_rowconfigure(1, weight=1)
        self.create_side_panel_content(side_panel_frame)

        logger.info("NewObjectEditorFrame initialized successfully.")
        # Initial counts
        self.refresh_counts()

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


    def setup_tabs(self):
        """Creates and configures the editor tabs."""
        logger.info("Setting up editor tabs.")
        self.tab_view.add("Basic Info")
        self.tab_view.add("Properties")
        self.tab_view.add("Attributes")
        self.tab_view.add("YAML Preview")

        self.create_basic_info_tab(self.tab_view.tab("Basic Info"))
        self.create_properties_tab(self.tab_view.tab("Properties"))
        self.create_placeholder_tab(self.tab_view.tab("Attributes"), "Attributes")
        self.create_placeholder_tab(self.tab_view.tab("YAML Preview"), "YAML Preview")

        # Normalize top-level tab header widths
        self._normalize_tab_header_widths(self.tab_view, min_width=140)

        logger.info("Editor tabs created.")

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
                self.save_button.configure(state=("normal" if self._dirty else "disabled"))
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
            data = self._collect_object_dict()
            current_id = self.current_object_id or data.get("id")
            if not current_id:
                messagebox.showwarning("Save", "No object selected to save.")
                return
            # Overwrite confirm if ID exists
            if current_id in self.data_manager.get_object_ids():
                if not messagebox.askyesno("Overwrite object?", f"Saving will overwrite '{current_id}'. Continue?"):
                    return
            # Merge with existing or build new skeleton, then persist via existing manager
            existing = self.data_manager.get_object_by_id(current_id) or {}
            updated = dict(existing)
            # Replace with minimal dict we collected (keeps schema keys intact)
            updated.update(data)

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

        # Configure a more rigid grid (no auto-expand)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)   # main input column expands
        content_frame.grid_columnconfigure(2, weight=0)
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
        
        count_label = ctk.CTkLabel(content_frame, text="Count:", anchor="w")
        count_label.grid(row=0, column=2, padx=(20,10), pady=PAD_Y, sticky="w")
        self.object_count_entry = ctk.CTkEntry(content_frame, width=SMALL_WIDTH)
        self.object_count_entry.insert(0, "(Auto)")
        self.object_count_entry.configure(state="disabled")
        self.object_count_entry.grid(row=0, column=3, padx=10, pady=PAD_Y, sticky="w")

        # --- Row 1: Name and Is Plural ---
        name_label = ctk.CTkLabel(content_frame, text="Name:", width=LABEL_WIDTH, anchor="w")
        name_label.grid(row=1, column=0, padx=10, pady=PAD_Y, sticky="w")
        # Nest Name entry and Is Plural checkbox side-by-side in a narrow row frame
        name_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        name_row.grid(row=1, column=1, padx=(10,0), pady=PAD_Y, sticky="w")
        self.name_entry = ctk.CTkEntry(name_row, placeholder_text="e.g., Emergency Torch", width=TEXT_WIDTH)
        self.name_entry.pack(side="left")
        self.name_entry.bind("<KeyRelease>", self._on_user_change)
        
        self.is_plural_checkbox = ctk.CTkCheckBox(name_row, text="Is Plural?")
        self.is_plural_checkbox.pack(side="left", padx=(6, 0))
        self.is_plural_checkbox.configure(command=self._mark_dirty)

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

        ctk.CTkLabel(ws_frame, text="Size:", anchor="w").grid(row=0, column=1, padx=(6,6), sticky="w")

        self.size_entry = ctk.CTkEntry(ws_frame, width=SMALL_WIDTH)
        self.size_entry.grid(row=0, column=2, padx=(0,0), sticky="w")
        self.size_entry.bind("<KeyRelease>", self._on_user_change)
        
        # --- Row 7: Description (fixed height) ---
        description_label = ctk.CTkLabel(content_frame, text="Description:", width=LABEL_WIDTH, anchor="w")
        description_label.grid(row=7, column=0, padx=10, pady=PAD_Y, sticky="nw")
        self.description_textbox = ctk.CTkTextbox(content_frame, height=200, wrap="word")
        self.description_textbox.grid(row=7, column=1, columnspan=3, padx=10, pady=PAD_Y, sticky="ew")
        content_frame.grid_rowconfigure(7, weight=0)  # keep description row fixed height
        self.description_textbox.bind("<KeyRelease>", self._on_user_change)

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

        # Initialize property checkboxes dictionary
        self.prop_checks = {}

        # Define tab names by rows
        top_tabs = [
            "Core Behaviours",
            "Storage",
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
        props = [
            ("is_takeable", "Takeable"),
            ("is_openable_closable", "Openable/Closable"),
            ("is_lockable", "Lockable"),
            ("is_interactive", "Interactive"),
            ("is_movable", "Movable"),
            ("is_secret", "Secret"),
            ("is_hidden", "Hidden"),
            ("is_modular", "Modular"),
            ("is_transferable", "Transferable"),
            ("is_stored", "Stored"),
        ]
        self._create_checks_grid(fr, props)

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
            self.object_id_entry.delete(0, "end"); self.object_id_entry.insert(0, data.get("id", "") or "")
            self.name_entry.delete(0, "end");      self.name_entry.insert(0, data.get("name", "") or "")
            self.is_plural_checkbox.select() if data.get("is_plural") else self.is_plural_checkbox.deselect()
            self.category_combobox.set(data.get("category", "") or "")
            self.synonyms_entry.delete(0, "end"); self.synonyms_entry.insert(0, ", ".join(data.get("synonyms", []) or []))
            self.description_textbox.delete("1.0", "end"); self.description_textbox.insert("1.0", data.get("description") or "")
            self.weight_entry.delete(0, "end"); self.weight_entry.insert(0, str(data.get("weight", "") or ""))
            self.size_entry.delete(0, "end");   self.size_entry.insert(0, str(data.get("size", "") or ""))

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
            self.object_id_entry.delete(0, "end")
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
            data = self._collect_object_dict()
            # This would update the YAML preview tab
            # For now, just log the data
            logger.debug(f"Preview updated with data: {data}")
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
        # Basic Info 'Count' box shows total objects (read-only)
        if hasattr(self, "object_count_entry"):
            try:
                total = len(self.data_manager.get_object_ids())
                self.object_count_entry.configure(state="normal")
                self.object_count_entry.delete(0, "end")
                self.object_count_entry.insert(0, str(total))
                self.object_count_entry.configure(state="disabled")
            except Exception:
                pass

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
        # Properties
        props: dict = {}
        for key, chk in getattr(self, "prop_checks", {}).items():
            if chk.get() == 1:
                props[key] = True
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

    def shutdown(self):
        """Perform any cleanup before the application closes."""
        logger.info("Shutting down NewObjectEditorFrame.")
