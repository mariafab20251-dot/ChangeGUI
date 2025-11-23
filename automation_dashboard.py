"""
AI Automation Dashboard
Complete video automation pipeline from script to publishing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from pathlib import Path
import threading
import logging

logger = logging.getLogger(__name__)


class DashboardStyles:
    """Modern Dark Theme for Dashboard"""
    BG_DARK = '#0d1117'
    BG_CARD = '#161b22'
    BG_INPUT = '#21262d'
    BG_ACCENT = '#1f6feb'

    TEXT_WHITE = '#f0f6fc'
    TEXT_LIGHT = '#c9d1d9'
    TEXT_MEDIUM = '#8b949e'

    ACCENT_PRIMARY = '#238636'
    ACCENT_WARNING = '#d29922'
    ACCENT_DANGER = '#da3633'
    ACCENT_INFO = '#1f6feb'
    ACCENT_PURPLE = '#8957e5'


class AutomationDashboard:
    """Main Automation Dashboard Window"""

    def __init__(self, parent=None):
        self.parent = parent
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("🤖 AI Video Automation Dashboard")
        self.window.geometry("1400x900")
        self.window.configure(bg=DashboardStyles.BG_DARK)

        # Settings storage
        self.settings_file = Path("automation_settings.json")
        self.settings = self.load_settings()

        # Account storage
        self.accounts = self.settings.get('accounts', {
            'youtube': [],
            'tiktok': [],
            'instagram': [],
            'facebook': []
        })

        self.create_ui()

    def load_settings(self):
        """Load dashboard settings"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_settings(self):
        """Save dashboard settings"""
        self.settings['accounts'] = self.accounts
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def create_ui(self):
        """Create the main dashboard UI"""
        # Header
        self.create_header()

        # Main content with notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Style the notebook
        style = ttk.Style()
        style.configure('TNotebook', background=DashboardStyles.BG_DARK)
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 10, 'bold'))

        # Create tabs
        self.create_pipeline_tab()
        self.create_script_tab()
        self.create_voice_tab()
        self.create_visuals_tab()
        self.create_accounts_tab()
        self.create_queue_tab()

    def create_header(self):
        """Create dashboard header"""
        header = tk.Frame(self.window, bg=DashboardStyles.BG_CARD, height=80)
        header.pack(fill='x', padx=10, pady=(10, 0))
        header.pack_propagate(False)

        # Title
        tk.Label(header, text="🤖 AI Video Automation Pipeline",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 18, 'bold')).pack(side='left', padx=20, pady=20)

        # Video type selector
        type_frame = tk.Frame(header, bg=DashboardStyles.BG_CARD)
        type_frame.pack(side='right', padx=20)

        tk.Label(type_frame, text="Video Type:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 10))

        self.video_type_var = tk.StringVar(value='shorts')
        ttk.Combobox(type_frame, textvariable=self.video_type_var,
                    values=['shorts', 'long-form'],
                    state='readonly', width=15).pack(side='left')

    def create_pipeline_tab(self):
        """Create the main pipeline overview tab"""
        tab = tk.Frame(self.notebook, bg=DashboardStyles.BG_DARK)
        self.notebook.add(tab, text='📊 Pipeline Overview')

        # Pipeline steps visualization
        pipeline_frame = tk.Frame(tab, bg=DashboardStyles.BG_DARK)
        pipeline_frame.pack(fill='x', padx=20, pady=20)

        steps = [
            ('📝', 'Script', 'Content & Prompts', DashboardStyles.ACCENT_INFO),
            ('🎙️', 'Voice', 'TTS Generation', DashboardStyles.ACCENT_PRIMARY),
            ('🎨', 'Visuals', 'Images/Videos', DashboardStyles.ACCENT_PURPLE),
            ('🎬', 'Compose', 'Process Video', DashboardStyles.ACCENT_WARNING),
            ('📤', 'Publish', 'Upload & Schedule', DashboardStyles.ACCENT_DANGER),
        ]

        for i, (icon, title, desc, color) in enumerate(steps):
            step_frame = tk.Frame(pipeline_frame, bg=DashboardStyles.BG_CARD,
                                 highlightbackground=color, highlightthickness=2)
            step_frame.pack(side='left', expand=True, fill='both', padx=5, pady=5)

            tk.Label(step_frame, text=icon, font=('Segoe UI', 24),
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE).pack(pady=(15, 5))
            tk.Label(step_frame, text=title, font=('Segoe UI', 12, 'bold'),
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE).pack()
            tk.Label(step_frame, text=desc, font=('Segoe UI', 9),
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM).pack(pady=(0, 15))

            # Arrow between steps
            if i < len(steps) - 1:
                tk.Label(pipeline_frame, text="→", font=('Segoe UI', 20),
                        bg=DashboardStyles.BG_DARK, fg=DashboardStyles.TEXT_MEDIUM).pack(side='left')

        # Quick Actions
        actions_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        actions_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(actions_frame, text="Quick Actions",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 14, 'bold')).pack(anchor='w', padx=20, pady=(15, 10))

        btn_frame = tk.Frame(actions_frame, bg=DashboardStyles.BG_CARD)
        btn_frame.pack(fill='x', padx=20, pady=(0, 15))

        tk.Button(btn_frame, text="🚀 Start New Project",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=20, pady=10,
                 command=self.start_new_project).pack(side='left', padx=5)

        tk.Button(btn_frame, text="📂 Import Existing",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=20, pady=10,
                 command=self.import_project).pack(side='left', padx=5)

        tk.Button(btn_frame, text="📋 Load Template",
                 bg=DashboardStyles.ACCENT_PURPLE, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=20, pady=10,
                 command=self.load_template).pack(side='left', padx=5)

        # Recent projects
        recent_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        recent_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(recent_frame, text="Recent Projects",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 14, 'bold')).pack(anchor='w', padx=20, pady=(15, 10))

        # Project list (placeholder)
        self.project_list = tk.Listbox(recent_frame, bg=DashboardStyles.BG_INPUT,
                                       fg=DashboardStyles.TEXT_LIGHT,
                                       font=('Segoe UI', 10),
                                       selectbackground=DashboardStyles.ACCENT_INFO,
                                       height=8)
        self.project_list.pack(fill='both', expand=True, padx=20, pady=(0, 15))
        self.project_list.insert(tk.END, "No recent projects")

    def create_script_tab(self):
        """Create the script generation tab"""
        tab = tk.Frame(self.notebook, bg=DashboardStyles.BG_DARK)
        self.notebook.add(tab, text='📝 Script Generator')

        # Create scrollable frame
        canvas = tk.Canvas(tab, bg=DashboardStyles.BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=DashboardStyles.BG_DARK)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Source Selection
        source_frame = tk.Frame(content, bg=DashboardStyles.BG_CARD)
        source_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(source_frame, text="Content Source",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        self.script_source_var = tk.StringVar(value='ai')

        sources = [
            ('ai', '🤖 AI Generate', 'Use LLM to generate script'),
            ('import', '📁 Import File', 'Load existing script with visual prompts'),
        ]

        for value, text, desc in sources:
            frame = tk.Frame(source_frame, bg=DashboardStyles.BG_INPUT)
            frame.pack(fill='x', padx=15, pady=5)

            tk.Radiobutton(frame, text=text, variable=self.script_source_var, value=value,
                          bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_WHITE,
                          selectcolor=DashboardStyles.BG_CARD,
                          font=('Segoe UI', 10, 'bold'),
                          command=self.on_script_source_change).pack(anchor='w', padx=10, pady=(10, 0))
            tk.Label(frame, text=desc, bg=DashboardStyles.BG_INPUT,
                    fg=DashboardStyles.TEXT_MEDIUM, font=('Segoe UI', 9)).pack(anchor='w', padx=30, pady=(0, 10))

        # AI Generation Settings
        self.ai_settings_frame = tk.Frame(content, bg=DashboardStyles.BG_CARD)
        self.ai_settings_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(self.ai_settings_frame, text="AI Generation Settings",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        # LLM Provider
        llm_frame = tk.Frame(self.ai_settings_frame, bg=DashboardStyles.BG_CARD)
        llm_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(llm_frame, text="LLM Provider:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.llm_provider_var = tk.StringVar(value='openai')
        ttk.Combobox(llm_frame, textvariable=self.llm_provider_var,
                    values=['openai', 'openrouter', 'anthropic', 'local'],
                    state='readonly', width=20).pack(side='left', padx=10)

        tk.Button(llm_frame, text="⚙️ Configure API",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.configure_llm_api).pack(side='left', padx=5)

        # Content Template
        template_frame = tk.Frame(self.ai_settings_frame, bg=DashboardStyles.BG_CARD)
        template_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(template_frame, text="Content Template:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.content_template_var = tk.StringVar(value='stoic')
        ttk.Combobox(template_frame, textvariable=self.content_template_var,
                    values=['stoic', 'motivational', 'facts', 'horror', 'educational',
                           'quotes', 'stories', 'custom'],
                    state='readonly', width=20).pack(side='left', padx=10)

        # Number of scripts
        num_frame = tk.Frame(self.ai_settings_frame, bg=DashboardStyles.BG_CARD)
        num_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(num_frame, text="Generate Scripts:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.num_scripts_var = tk.IntVar(value=1)
        tk.Spinbox(num_frame, from_=1, to=100, textvariable=self.num_scripts_var,
                  width=10, bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT).pack(side='left', padx=10)

        # Generate button
        tk.Button(self.ai_settings_frame, text="🚀 Generate Scripts",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 font=('Segoe UI', 11, 'bold'), padx=30, pady=10,
                 command=self.generate_scripts).pack(pady=15)

        # Import Settings
        self.import_settings_frame = tk.Frame(content, bg=DashboardStyles.BG_CARD)

        tk.Label(self.import_settings_frame, text="Import Script File",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        import_btn_frame = tk.Frame(self.import_settings_frame, bg=DashboardStyles.BG_CARD)
        import_btn_frame.pack(fill='x', padx=15, pady=10)

        self.import_file_var = tk.StringVar()
        tk.Entry(import_btn_frame, textvariable=self.import_file_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=50).pack(side='left', padx=(0, 10))

        tk.Button(import_btn_frame, text="Browse",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.browse_script_file).pack(side='left')

        tk.Label(self.import_settings_frame,
                text="Format: Script text with visual prompts marked as [VISUAL: description]",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', padx=15, pady=(0, 15))

        # Output preview
        preview_frame = tk.Frame(content, bg=DashboardStyles.BG_CARD)
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(preview_frame, text="Script Preview",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        self.script_preview = scrolledtext.ScrolledText(preview_frame,
                                                        bg=DashboardStyles.BG_INPUT,
                                                        fg=DashboardStyles.TEXT_LIGHT,
                                                        font=('Consolas', 10),
                                                        height=15)
        self.script_preview.pack(fill='both', expand=True, padx=15, pady=(0, 15))

    def create_voice_tab(self):
        """Create the voice generation tab"""
        tab = tk.Frame(self.notebook, bg=DashboardStyles.BG_DARK)
        self.notebook.add(tab, text='🎙️ Voice Generator')

        # Source Selection
        source_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        source_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(source_frame, text="Voice Source",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        self.voice_source_var = tk.StringVar(value='cloud')

        sources = [
            ('cloud', '☁️ Cloud TTS (Edge-TTS)', 'Free, multiple voices'),
            ('kokoro', '🎯 Kokoro TTS (Local)', 'Free, offline, fast'),
            ('neutts', '🎙️ NeuTTS (Voice Clone)', 'Clone any voice'),
            ('elevenlabs', '🌟 ElevenLabs API', 'Premium quality'),
            ('import', '📁 Import Audio', 'Use existing voiceover'),
        ]

        for value, text, desc in sources:
            frame = tk.Frame(source_frame, bg=DashboardStyles.BG_INPUT)
            frame.pack(fill='x', padx=15, pady=3)

            tk.Radiobutton(frame, text=text, variable=self.voice_source_var, value=value,
                          bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_WHITE,
                          selectcolor=DashboardStyles.BG_CARD,
                          font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(8, 0))
            tk.Label(frame, text=desc, bg=DashboardStyles.BG_INPUT,
                    fg=DashboardStyles.TEXT_MEDIUM, font=('Segoe UI', 9)).pack(anchor='w', padx=30, pady=(0, 8))

        # Voice settings placeholder
        settings_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        settings_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(settings_frame, text="Voice Settings",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        tk.Label(settings_frame, text="Configure voice settings based on selected source above.\nSettings will appear here when you select a source.",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 10)).pack(padx=15, pady=50)

    def create_visuals_tab(self):
        """Create the visuals generation tab"""
        tab = tk.Frame(self.notebook, bg=DashboardStyles.BG_DARK)
        self.notebook.add(tab, text='🎨 Visual Generator')

        # Source Selection
        source_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        source_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(source_frame, text="Visual Source",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        self.visual_source_var = tk.StringVar(value='comfyui')

        sources = [
            ('comfyui', '🎨 ComfyUI (Local)', 'Local AI image generation'),
            ('nanobanana', '🍌 Nano Banana API', 'Cloud image/video generation'),
            ('sora', '🎥 Sora 2 (OpenAI)', 'AI video generation'),
            ('kling', '🌟 Kling AI', 'Video generation'),
            ('hailuo', '🎬 Hailuo AI', 'Video generation'),
            ('metaai', '🤖 Meta AI', 'Image generation'),
            ('local', '📂 Local Folder', 'Use existing images/videos'),
        ]

        for value, text, desc in sources:
            frame = tk.Frame(source_frame, bg=DashboardStyles.BG_INPUT)
            frame.pack(fill='x', padx=15, pady=3)

            tk.Radiobutton(frame, text=text, variable=self.visual_source_var, value=value,
                          bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_WHITE,
                          selectcolor=DashboardStyles.BG_CARD,
                          font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(8, 0))
            tk.Label(frame, text=desc, bg=DashboardStyles.BG_INPUT,
                    fg=DashboardStyles.TEXT_MEDIUM, font=('Segoe UI', 9)).pack(anchor='w', padx=30, pady=(0, 8))

        # Local folder settings
        local_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        local_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(local_frame, text="Local Clips Folder",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        folder_frame = tk.Frame(local_frame, bg=DashboardStyles.BG_CARD)
        folder_frame.pack(fill='x', padx=15, pady=5)

        self.clips_folder_var = tk.StringVar()
        tk.Entry(folder_frame, textvariable=self.clips_folder_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=50).pack(side='left', padx=(0, 10))

        tk.Button(folder_frame, text="Browse",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.browse_clips_folder).pack(side='left')

        tk.Label(local_frame,
                text="Files should be numbered: 1.mp4, 2.mp4, 3.jpg, etc. Will be merged in sequence.",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', padx=15, pady=(5, 15))

    def create_accounts_tab(self):
        """Create the accounts management tab"""
        tab = tk.Frame(self.notebook, bg=DashboardStyles.BG_DARK)
        self.notebook.add(tab, text='👥 Accounts')

        # Platforms
        platforms = [
            ('youtube', '📺 YouTube Channels', 'red'),
            ('tiktok', '🎵 TikTok Accounts', 'black'),
            ('instagram', '📸 Instagram Accounts', 'purple'),
            ('facebook', '📘 Facebook Pages', 'blue'),
        ]

        for platform, title, color in platforms:
            frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
            frame.pack(fill='x', padx=20, pady=5)

            header = tk.Frame(frame, bg=DashboardStyles.BG_CARD)
            header.pack(fill='x', padx=15, pady=(10, 5))

            tk.Label(header, text=title,
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                    font=('Segoe UI', 11, 'bold')).pack(side='left')

            tk.Button(header, text="+ Add",
                     bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                     font=('Segoe UI', 9),
                     command=lambda p=platform: self.add_account(p)).pack(side='right')

            # Account list
            list_frame = tk.Frame(frame, bg=DashboardStyles.BG_CARD)
            list_frame.pack(fill='x', padx=15, pady=(0, 10))

            accounts = self.accounts.get(platform, [])
            if accounts:
                for acc in accounts:
                    acc_frame = tk.Frame(list_frame, bg=DashboardStyles.BG_INPUT)
                    acc_frame.pack(fill='x', pady=2)

                    tk.Label(acc_frame, text=f"  ✓ {acc['name']}",
                            bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                            font=('Segoe UI', 10)).pack(side='left', pady=5)

                    tk.Button(acc_frame, text="✕",
                             bg=DashboardStyles.ACCENT_DANGER, fg='white',
                             font=('Segoe UI', 8),
                             command=lambda p=platform, a=acc: self.remove_account(p, a)).pack(side='right', padx=5, pady=3)
            else:
                tk.Label(list_frame, text="  No accounts added",
                        bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                        font=('Segoe UI', 9, 'italic')).pack(anchor='w', pady=5)

    def create_queue_tab(self):
        """Create the batch queue tab"""
        tab = tk.Frame(self.notebook, bg=DashboardStyles.BG_DARK)
        self.notebook.add(tab, text='📋 Queue')

        # Queue controls
        controls_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        controls_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(controls_frame, text="Batch Processing Queue",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        btn_frame = tk.Frame(controls_frame, bg=DashboardStyles.BG_CARD)
        btn_frame.pack(fill='x', padx=15, pady=(0, 15))

        tk.Button(btn_frame, text="▶️ Start Queue",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(btn_frame, text="⏸️ Pause",
                 bg=DashboardStyles.ACCENT_WARNING, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(btn_frame, text="🗑️ Clear",
                 bg=DashboardStyles.ACCENT_DANGER, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=15, pady=8).pack(side='left', padx=5)

        # Queue list
        queue_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        queue_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Treeview for queue
        columns = ('Status', 'Title', 'Type', 'Progress')
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.queue_tree.heading(col, text=col)
            self.queue_tree.column(col, width=150)

        self.queue_tree.pack(fill='both', expand=True, padx=15, pady=15)

        # Add sample item
        self.queue_tree.insert('', 'end', values=('⏳ Pending', 'Sample Video', 'Shorts', '0%'))

    # Event handlers
    def on_script_source_change(self):
        """Handle script source selection change"""
        source = self.script_source_var.get()
        if source == 'ai':
            self.ai_settings_frame.pack(fill='x', padx=20, pady=10, after=self.ai_settings_frame.master.winfo_children()[0])
            self.import_settings_frame.pack_forget()
        else:
            self.import_settings_frame.pack(fill='x', padx=20, pady=10, after=self.ai_settings_frame.master.winfo_children()[0])
            self.ai_settings_frame.pack_forget()

    def start_new_project(self):
        """Start a new automation project"""
        messagebox.showinfo("New Project", "Starting new project wizard...")

    def import_project(self):
        """Import existing project"""
        file = filedialog.askopenfilename(
            title="Import Project",
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )
        if file:
            messagebox.showinfo("Import", f"Imported: {file}")

    def load_template(self):
        """Load a project template"""
        templates = ['Stoic Shorts', 'Motivational Long', 'Horror Stories', 'Educational Facts']
        # Would show template selector
        messagebox.showinfo("Templates", "Template selector coming soon!")

    def configure_llm_api(self):
        """Configure LLM API settings"""
        messagebox.showinfo("Configure API", "API configuration dialog coming soon!")

    def generate_scripts(self):
        """Generate scripts using AI"""
        num = self.num_scripts_var.get()
        template = self.content_template_var.get()
        provider = self.llm_provider_var.get()

        self.script_preview.delete('1.0', tk.END)
        self.script_preview.insert('1.0', f"Generating {num} {template} script(s) using {provider}...\n\n")
        self.script_preview.insert(tk.END, "This feature will be implemented with actual LLM integration.")

    def browse_script_file(self):
        """Browse for script file"""
        file = filedialog.askopenfilename(
            title="Select Script File",
            filetypes=[('Text Files', '*.txt'), ('JSON Files', '*.json'), ('All Files', '*.*')]
        )
        if file:
            self.import_file_var.set(file)

    def browse_clips_folder(self):
        """Browse for clips folder"""
        folder = filedialog.askdirectory(title="Select Clips Folder")
        if folder:
            self.clips_folder_var.set(folder)

    def add_account(self, platform):
        """Add account for platform"""
        # Would show account addition dialog
        messagebox.showinfo("Add Account", f"Add {platform} account dialog coming soon!")

    def remove_account(self, platform, account):
        """Remove account"""
        if messagebox.askyesno("Remove Account", f"Remove {account['name']}?"):
            self.accounts[platform].remove(account)
            self.save_settings()
            # Refresh UI

    def run(self):
        """Run the dashboard (standalone mode)"""
        self.window.mainloop()


def open_dashboard(parent=None):
    """Open the automation dashboard"""
    dashboard = AutomationDashboard(parent)
    return dashboard


if __name__ == "__main__":
    # Run standalone for testing
    dashboard = AutomationDashboard()
    dashboard.run()
