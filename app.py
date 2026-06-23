import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import json
import time

import scraper
import ai_engine
import config

# Set theme and appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class AIWebExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Load configuration
        self.app_config = config.load_config()

        # Window properties
        self.title("GetTheData")
        self.geometry("1100x700")
        self.minsize(800, 600)

        # Main grid configuration
        self.grid_columnconfigure(0, weight=0) # Sidebar (fixed width)
        self.grid_columnconfigure(1, weight=1) # Main View (resizable)
        self.grid_rowconfigure(0, weight=1)

        # Threading and execution variables
        self.is_running = False
        self.scraped_data = None
        self.ai_output_data = None

        # Build UI Components
        self.create_sidebar()
        self.create_main_panel()
        
        # Apply loaded configurations to widgets
        self.apply_config_to_widgets()
        self.update_provider_ui()
        self.update_preset_prompt_ui()
        
        # Fetch local Ollama models in background if provider is Ollama
        if "Ollama" in self.provider_menu.get():
            self.load_ollama_models_async()

    def create_sidebar(self):
        """Creates the left configuration sidebar."""
        # Main sidebar container
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Configure sidebar main rows:
        # Row 0: Logo Header (fixed)
        # Row 1: Scrollable content area (expandable)
        # Row 2: Action buttons frame (fixed at the bottom)
        self.sidebar.grid_rowconfigure(0, weight=0)
        self.sidebar.grid_rowconfigure(1, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=0)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # --- LOGO HEADER ---
        self.header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="GetTheData", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#6366f1" # Vibrant Indigo Accent
        )
        self.logo_label.grid(row=0, column=0, sticky="w")
        
        self.sublogo_label = ctk.CTkLabel(
            self.header_frame, 
            text="Fetch and restructure web data using LLMs", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="gray"
        )
        self.sublogo_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # --- SCROLLABLE SETTINGS CONTENT ---
        self.settings_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0)
        self.settings_scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.settings_scroll.grid_columnconfigure(0, weight=1)

        # --- SECTION: TARGET WEBSITE ---
        self.section_input = ctk.CTkLabel(
            self.settings_scroll, text="1. Target Website", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="white"
        )
        self.section_input.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        self.url_entry = ctk.CTkEntry(
            self.settings_scroll, placeholder_text="https://example.com/article"
        )
        self.url_entry.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # --- SECTION: AI PROVIDER ---
        self.section_ai = ctk.CTkLabel(
            self.settings_scroll, text="2. AI Enhancer Configuration", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="white"
        )
        self.section_ai.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")

        # Provider Selector
        self.provider_label = ctk.CTkLabel(self.settings_scroll, text="Provider:", font=ctk.CTkFont(size=12))
        self.provider_label.grid(row=5, column=0, padx=20, pady=(0, 2), sticky="w")
        self.provider_menu = ctk.CTkOptionMenu(
            self.settings_scroll, values=["Gemini", "Ollama (Local)"],
            command=self.on_provider_change
        )
        self.provider_menu.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Gemini API Key Field (Conditional)
        self.api_key_frame = ctk.CTkFrame(self.settings_scroll, fg_color="transparent")
        self.api_key_frame.grid_columnconfigure(0, weight=1)
        self.api_key_label = ctk.CTkLabel(self.api_key_frame, text="Gemini API Key:", font=ctk.CTkFont(size=12))
        self.api_key_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        
        self.api_key_entry = ctk.CTkEntry(
            self.api_key_frame, placeholder_text="Enter Gemini API Key...", show="*"
        )
        self.api_key_entry.grid(row=1, column=0, sticky="ew")
        
        self.show_key_btn = ctk.CTkButton(
            self.api_key_frame, text="👁️", width=40, 
            command=self.toggle_api_key_visibility
        )
        self.show_key_btn.grid(row=1, column=1, padx=(5, 0), sticky="e")
        self.api_key_frame.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Ollama API Endpoint Field (Conditional)
        self.ollama_frame = ctk.CTkFrame(self.settings_scroll, fg_color="transparent")
        self.ollama_frame.grid_columnconfigure(0, weight=1)
        self.ollama_url_label = ctk.CTkLabel(self.ollama_frame, text="Ollama Service URL:", font=ctk.CTkFont(size=12))
        self.ollama_url_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.ollama_url_entry = ctk.CTkEntry(
            self.ollama_frame, placeholder_text="http://localhost:11434"
        )
        self.ollama_url_entry.grid(row=1, column=0, sticky="ew")
        self.ollama_url_entry.bind("<FocusOut>", lambda e: self.load_ollama_models_async())
        self.ollama_url_entry.bind("<Return>", lambda e: self.load_ollama_models_async())
        self.ollama_frame.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Model Selector Label (Gridding of actual dropdown/entry done in update_provider_ui)
        self.model_label = ctk.CTkLabel(self.settings_scroll, text="Model Name:", font=ctk.CTkFont(size=12))
        self.model_label.grid(row=9, column=0, padx=20, pady=(0, 2), sticky="w")
        
        self.model_menu_gemini = ctk.CTkOptionMenu(
            self.settings_scroll, values=["gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-3.1-pro-preview", "gemini-1.5-pro", "gemini-1.5-flash"]
        )
        self.model_entry_ollama = ctk.CTkComboBox(
            self.settings_scroll, values=["llama3", "mistral", "gemma", "phi3"]
        )

        # --- SECTION: RESTRUCTURING PRESETS ---
        self.section_preset = ctk.CTkLabel(
            self.settings_scroll, text="3. Restructure Goal", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="white"
        )
        self.section_preset.grid(row=11, column=0, padx=20, pady=(10, 5), sticky="w")

        preset_names = [p["name"] for p in ai_engine.PRESETS]
        self.preset_menu = ctk.CTkOptionMenu(
            self.settings_scroll, values=preset_names,
            command=self.on_preset_change
        )
        self.preset_menu.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Custom Prompt Box
        self.custom_prompt_frame = ctk.CTkFrame(self.settings_scroll, fg_color="transparent")
        self.custom_prompt_frame.grid_columnconfigure(0, weight=1)
        self.custom_prompt_label = ctk.CTkLabel(self.custom_prompt_frame, text="Custom AI Instruction:", font=ctk.CTkFont(size=12))
        self.custom_prompt_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.custom_prompt_text = ctk.CTkTextbox(self.custom_prompt_frame, height=100)
        self.custom_prompt_text.grid(row=1, column=0, sticky="ew")
        self.custom_prompt_frame.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="ew")

        # --- FIXED BOTTOM ACTION PANEL ---
        self.action_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, padx=20, pady=(15, 25), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(
            self.action_frame, 
            text="✨ Fetch & Restructure", 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4f46e5", hover_color="#6366f1",
            command=self.start_process,
            height=40
        )
        self.run_btn.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        self.reset_btn = ctk.CTkButton(
            self.action_frame, 
            text="Reset Config", 
            fg_color="#334155", hover_color="#475569",
            command=self.reset_settings,
            height=30
        )
        self.reset_btn.grid(row=1, column=0, sticky="ew")

    def create_main_panel(self):
        """Creates the right side main content panel with tab views."""
        self.main_panel = ctk.CTkFrame(self, fg_color="#090d16", corner_radius=0)
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_panel.grid_rowconfigure(0, weight=1)
        self.main_panel.grid_columnconfigure(0, weight=1)

        # Tab Control
        self.tab_view = ctk.CTkTabview(self.main_panel, segmented_button_selected_color="#4f46e5", segmented_button_unselected_hover_color="#312e81")
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 10))

        # Add tabs
        self.tab_ai = self.tab_view.add("✨ Restructured AI Output")
        self.tab_raw = self.tab_view.add("📄 Scraped Web Content")
        self.tab_meta = self.tab_view.add("🔍 Metadata & JSON")

        self.setup_tab_content(self.tab_ai, "ai")
        self.setup_tab_content(self.tab_raw, "raw")
        self.setup_tab_content(self.tab_meta, "meta")

        # Bottom Status Bar
        self.status_bar = ctk.CTkFrame(self.main_panel, height=40, fg_color="#111827")
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_bar, 
            text="Ready. Enter a URL and configure settings to start.",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af"
        )
        self.status_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(self.status_bar, width=200, height=8, progress_color="#6366f1")
        self.progress_bar.grid(row=0, column=1, padx=15, pady=8, sticky="e")
        self.progress_bar.set(0)

    def setup_tab_content(self, tab, name):
        """Sets up the layout inside a single tab."""
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=0)
        tab.grid_columnconfigure(0, weight=1)

        # Text Area
        text_box = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas" if name == "meta" else "Segoe UI", size=13))
        text_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Save reference
        if name == "ai":
            self.ai_textbox = text_box
        elif name == "raw":
            self.raw_textbox = text_box
        elif name == "meta":
            self.meta_textbox = text_box

        # Button Frame (Bottom)
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        copy_btn = ctk.CTkButton(
            btn_frame, text="📋 Copy to Clipboard", width=150,
            command=lambda n=name: self.copy_to_clipboard(n)
        )
        copy_btn.pack(side="left", padx=(0, 10))

        export_btn = ctk.CTkButton(
            btn_frame, text="💾 Export to File...", width=150,
            fg_color="#334155", hover_color="#475569",
            command=lambda n=name: self.export_to_file(n)
        )
        export_btn.pack(side="left")

    # --- WIDGET SYNC AND UPDATE EVENT HANDLERS ---
    
    def apply_config_to_widgets(self):
        """Pre-populates GUI widgets from the loaded config.json."""
        self.url_entry.insert(0, self.app_config.get("last_url", ""))
        
        provider = self.app_config.get("default_provider", "Gemini")
        if provider not in ["Gemini", "Ollama (Local)"]:
            provider = "Gemini"
        self.provider_menu.set(provider)
        
        self.api_key_entry.insert(0, self.app_config.get("gemini_api_key", ""))
        self.ollama_url_entry.insert(0, self.app_config.get("ollama_url", "http://localhost:11434"))
        
        gemini_model = self.app_config.get("gemini_model", "gemini-3.5-flash")
        self.model_menu_gemini.set(gemini_model)
        
        ollama_model = self.app_config.get("ollama_model", "llama3")
        self.model_entry_ollama.set(ollama_model)

        preset_idx = self.app_config.get("preset_index", 0)
        if preset_idx < len(ai_engine.PRESETS):
            self.preset_menu.set(ai_engine.PRESETS[preset_idx]["name"])
        else:
            self.preset_menu.set(ai_engine.PRESETS[0]["name"])

        self.custom_prompt_text.insert("1.0", self.app_config.get("custom_prompt", ""))

    def on_provider_change(self, selected_provider):
        """Called when user changes AI service provider."""
        self.update_provider_ui()
        if "Ollama" in selected_provider:
            self.load_ollama_models_async()

    def update_provider_ui(self):
        """Hides/shows config options based on selected AI service provider."""
        provider = self.provider_menu.get()
        if "Gemini" in provider:
            # Show Gemini fields
            self.api_key_frame.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")
            self.model_menu_gemini.grid(row=10, column=0, padx=20, pady=(0, 15), sticky="ew")
            # Hide Ollama fields
            self.ollama_frame.grid_remove()
            self.model_entry_ollama.grid_remove()
        else:
            # Show Ollama fields
            self.ollama_frame.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
            self.model_entry_ollama.grid(row=10, column=0, padx=20, pady=(0, 15), sticky="ew")
            # Hide Gemini fields
            self.api_key_frame.grid_remove()
            self.model_menu_gemini.grid_remove()

    def on_preset_change(self, selected_preset_name):
        """Called when user selects a preset restructuring task."""
        self.update_preset_prompt_ui()

    def update_preset_prompt_ui(self):
        """Enables/disables custom prompt depending on preset selection."""
        selected_name = self.preset_menu.get()
        preset = next((p for p in ai_engine.PRESETS if p["name"] == selected_name), None)
        
        if preset:
            # If it's custom
            if selected_name == "Custom Action...":
                self.custom_prompt_frame.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="ew")
                self.custom_prompt_text.configure(state="normal")
            else:
                self.custom_prompt_frame.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="ew")
                # Clear and insert default prompt, disable editing
                self.custom_prompt_text.configure(state="normal")
                self.custom_prompt_text.delete("1.0", "end")
                self.custom_prompt_text.insert("1.0", preset["system_prompt"])
                self.custom_prompt_text.configure(state="disabled")

    def load_ollama_models_async(self):
        """Fetches Ollama models in a background thread and updates the combobox."""
        url = self.ollama_url_entry.get().strip() or "http://localhost:11434"
        thread = threading.Thread(target=self._fetch_ollama_models, args=(url,), daemon=True)
        thread.start()

    def _fetch_ollama_models(self, url):
        models = ai_engine.get_ollama_models(url)
        if models:
            self.after(0, lambda: self.update_ollama_combobox(models, connected=True))
        else:
            default_fallbacks = ["llama3.2", "llama3.2:1b", "qwen2.5:1.5b", "gemma2:2b", "llama3", "mistral", "phi3"]
            self.after(0, lambda: self.update_ollama_combobox(default_fallbacks, connected=False))

    def update_ollama_combobox(self, models, connected=True):
        # Update combobox values list
        self.model_entry_ollama.configure(values=models)
        
        current = self.model_entry_ollama.get().strip()
        if connected and models:
            # If current selection is empty or not in the list, auto-select the first model
            if not current or current not in models:
                self.model_entry_ollama.set(models[0])
                self.update_status(f"Connected to Ollama. Selected model: {models[0]}", text_color="#34d399")
            else:
                self.update_status(f"Connected to Ollama successfully. Active model: {current}", text_color="#34d399")
        elif not connected:
            self.update_status("Could not connect to local Ollama service. Using fallback model list.", text_color="#fbbf24")

    def toggle_api_key_visibility(self):
        """Toggles show/hide on Gemini API Key field."""
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.configure(show="")
            self.show_key_btn.configure(text="🔒")
        else:
            self.api_key_entry.configure(show="*")
            self.show_key_btn.configure(text="👁️")

    # --- SAVE SETTINGS & CONFIGS ---

    def gather_current_config(self) -> dict:
        """Gathers GUI widget values to write to settings config."""
        preset_name = self.preset_menu.get()
        preset_idx = 0
        for idx, p in enumerate(ai_engine.PRESETS):
            if p["name"] == preset_name:
                preset_idx = idx
                break

        return {
            'gemini_api_key': self.api_key_entry.get().strip(),
            'default_provider': self.provider_menu.get(),
            'gemini_model': self.model_menu_gemini.get(),
            'ollama_model': self.model_entry_ollama.get().strip(),
            'ollama_url': self.ollama_url_entry.get().strip(),
            'preset_index': preset_idx,
            'custom_prompt': self.custom_prompt_text.get("1.0", "end-1c") if preset_name == "Custom Action..." else self.app_config.get("custom_prompt", ""),
            'last_url': self.url_entry.get().strip()
        }

    def reset_settings(self):
        """Resets the application settings to default."""
        if messagebox.askyesno("Reset Config", "Are you sure you want to reset settings to default values?"):
            self.app_config = config.DEFAULT_CONFIG.copy()
            config.save_config(self.app_config)
            
            # Clear widgets
            self.url_entry.delete(0, "end")
            self.api_key_entry.delete(0, "end")
            self.ollama_url_entry.delete(0, "end")
            self.model_entry_ollama.set("")
            self.custom_prompt_text.delete("1.0", "end")
            
            # Re-apply defaults
            self.apply_config_to_widgets()
            self.update_provider_ui()
            self.update_preset_prompt_ui()
            self.update_status("Configuration reset to defaults.", 0)

    # --- CORE BACKGROUND BUSINESS LOGIC ---

    def update_status(self, text, progress_val=None, text_color="#9ca3af"):
        """Thread-safe status bar update helper."""
        self.status_label.configure(text=text, text_color=text_color)
        if progress_val is not None:
            self.progress_bar.set(progress_val)
        self.update_idletasks()

    def start_process(self):
        """Fires off the scraper and AI restructurer in a separate background thread."""
        if self.is_running:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Validation Error", "Please enter a valid website URL.")
            return

        # Save config settings automatically
        current_cfg = self.gather_current_config()
        
        provider = current_cfg.get("default_provider", "Gemini")
        if "Ollama" in provider:
            ollama_url = current_cfg.get("ollama_url", "http://localhost:11434")
            models = ai_engine.get_ollama_models(ollama_url)
            if not models:
                has_gemini_key = bool(current_cfg.get("gemini_api_key", "").strip())
                if has_gemini_key:
                    if messagebox.askyesno(
                        "Ollama Connection Failed",
                        f"Could not connect to local Ollama service at {ollama_url}.\n\n"
                        "Please ensure Ollama is installed and running.\n\n"
                        "Since you have a Gemini API Key configured, would you like to switch the provider to Gemini and proceed?"
                    ):
                        self.provider_menu.set("Gemini")
                        self.update_provider_ui()
                        current_cfg = self.gather_current_config()
                    else:
                        return
                else:
                    if not messagebox.askyesno(
                        "Ollama Connection Failed",
                        f"Could not connect to local Ollama service at {ollama_url}.\n\n"
                        "Please ensure Ollama is installed and running.\n\n"
                        "Would you like to try connecting anyway?"
                    ):
                        return

        config.save_config(current_cfg)
        self.app_config = current_cfg

        # Clear outputs
        self.raw_textbox.delete("1.0", "end")
        self.ai_textbox.delete("1.0", "end")
        self.meta_textbox.delete("1.0", "end")
        self.scraped_data = None
        self.ai_output_data = None

        # Lock UI
        self.is_running = True
        self.run_btn.configure(state="disabled", text="⚡ Processing...")
        self.reset_btn.configure(state="disabled")

        # Spawn Thread
        thread = threading.Thread(target=self.run_background_task, args=(url,), daemon=True)
        thread.start()

    def run_background_task(self, url):
        """The target function running in background thread."""
        start_time = time.time()
        
        # Step 1: Scrape Website
        self.update_status(f"Scraping {url}...", 0.25)
        scrape_res = scraper.scrape_url(url)
        
        if not scrape_res['success']:
            self.update_status(f"Scraping Error: {scrape_res['error']}", 0.0, "#f87171")
            self.raw_textbox.insert("1.0", f"Error during scraping:\n\n{scrape_res['error']}")
            self.meta_textbox.insert("1.0", json.dumps(scrape_res, indent=4))
            self.unlock_ui()
            return

        # Scrape Success - Update UI
        self.scraped_data = scrape_res
        self.raw_textbox.insert("1.0", scrape_res['content'])
        self.meta_textbox.insert("1.0", json.dumps(scrape_res, indent=4))

        # Check content size
        if scrape_res['word_count'] == 0:
            self.update_status("Scraping finished but no content was extracted.", 1.0, "#fbbf24")
            self.ai_textbox.insert("1.0", "No content extracted to analyze.")
            self.unlock_ui()
            return

        # Step 2: Call AI model
        provider = self.app_config['default_provider']
        self.update_status(f"Sending content to AI ({provider})...", 0.6)
        
        # Select active system prompt
        preset_name = self.preset_menu.get()
        if preset_name == "Custom Action...":
            system_prompt = self.custom_prompt_text.get("1.0", "end-1c").strip()
        else:
            preset = next((p for p in ai_engine.PRESETS if p["name"] == preset_name), None)
            system_prompt = preset["system_prompt"] if preset else ""

        # Restrict prompt text size to avoid token limit issues (max 50,000 characters roughly)
        max_char_len = 80000
        scraped_text = scrape_res['content']
        if len(scraped_text) > max_char_len:
            scraped_text = scraped_text[:max_char_len] + "\n\n[Content truncated by app to fit context limit...]"

        user_prompt = (
            f"Here is the website content scraped from: {url}\n"
            f"Page Title: {scrape_res['title']}\n"
            f"Page Meta Description: {scrape_res['description']}\n\n"
            f"Web Page Content:\n"
            f"\"\"\"\n{scraped_text}\n\"\"\""
        )

        success = False
        ai_text = ""
        
        if "Gemini" in provider:
            api_key = self.app_config['gemini_api_key']
            model = self.app_config['gemini_model']
            success, ai_text = ai_engine.call_gemini(api_key, model, system_prompt, user_prompt)
        else:
            url_endpoint = self.app_config['ollama_url']
            model = self.app_config['ollama_model']
            success, ai_text = ai_engine.call_ollama(url_endpoint, model, system_prompt, user_prompt)

        elapsed = time.time() - start_time
        
        if success:
            self.ai_output_data = ai_text
            self.ai_textbox.insert("1.0", ai_text)
            
            # Switch to restructured tab automatically to showcase result
            self.tab_view.set("✨ Restructured AI Output")
            self.update_status(f"Completed successfully in {elapsed:.2f}s!", 1.0, "#34d399")
        else:
            self.ai_textbox.insert("1.0", f"AI Error:\n\n{ai_text}")
            self.update_status("AI Restructuring failed.", 0.0, "#f87171")
            messagebox.showerror("AI Connection Error", ai_text)

        self.unlock_ui()

    def unlock_ui(self):
        """Thread-safe UI unlock."""
        self.is_running = False
        self.run_btn.configure(state="normal", text="✨ Fetch & Restructure")
        self.reset_btn.configure(state="normal")

    # --- EXPORT & CLIPBOARD UTILITIES ---

    def copy_to_clipboard(self, tab_name):
        """Copies the text box contents of specified tab to system clipboard."""
        text = ""
        if tab_name == "ai":
            text = self.ai_textbox.get("1.0", "end-1c")
        elif tab_name == "raw":
            text = self.raw_textbox.get("1.0", "end-1c")
        elif tab_name == "meta":
            text = self.meta_textbox.get("1.0", "end-1c")

        if not text.strip():
            self.update_status("Nothing to copy!", text_color="#fbbf24")
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_status("Copied to clipboard!", text_color="#34d399")

    def export_to_file(self, tab_name):
        """Opens file dialog to save current tab data to disk."""
        text = ""
        def_ext = ".txt"
        file_types = [("Text files", "*.txt"), ("All files", "*.*")]
        
        if tab_name == "ai":
            text = self.ai_textbox.get("1.0", "end-1c")
            def_ext = ".md"
            file_types = [("Markdown files", "*.md"), ("Text files", "*.txt")]
        elif tab_name == "raw":
            text = self.raw_textbox.get("1.0", "end-1c")
            def_ext = ".txt"
        elif tab_name == "meta":
            text = self.meta_textbox.get("1.0", "end-1c")
            def_ext = ".json"
            file_types = [("JSON files", "*.json")]

        if not text.strip():
            messagebox.showwarning("Empty Content", "There is no content in this tab to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=def_ext,
            filetypes=file_types,
            title="Export content"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.update_status(f"Saved content to {os.path.basename(filepath)}!", text_color="#34d399")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not write file:\n{str(e)}")

if __name__ == "__main__":
    app = AIWebExtractorApp()
    app.mainloop()
