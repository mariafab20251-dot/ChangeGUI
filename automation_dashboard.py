"""
AI Automation Dashboard
Complete video automation pipeline from script to publishing
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
from pathlib import Path
import threading
import logging
import requests
import os

logger = logging.getLogger(__name__)

# Content templates for different video types
CONTENT_TEMPLATES = {
    'stoic': {
        'name': 'Stoic Wisdom',
        'system_prompt': '''You are a script writer specializing in Stoic philosophy content for viral short-form videos.
Create powerful, thought-provoking scripts that combine ancient Stoic wisdom with modern relevance.
Each script should have clear visual scene descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a viral short-form video script about Stoic philosophy.

Requirements:
- Duration: 30-60 seconds when spoken
- Hook: Start with an attention-grabbing statement
- Include 3-5 visual scene descriptions marked as [VISUAL: description]
- End with a powerful takeaway
- Tone: Deep, contemplative, but accessible

Topic focus: {topic}

Format your response as:
TITLE: [Catchy title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['resilience', 'inner peace', 'control', 'adversity', 'death', 'virtue', 'discipline']
    },
    'motivational': {
        'name': 'Motivational',
        'system_prompt': '''You are an expert motivational content creator for viral videos.
Create inspiring, action-oriented scripts that push viewers to take action.
Include vivid visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a motivational video script that inspires action.

Requirements:
- Duration: 30-60 seconds when spoken
- Hook: Start with a powerful question or statement
- Include 3-5 visual scene descriptions as [VISUAL: description]
- Build emotional momentum
- End with a clear call to action

Topic focus: {topic}

Format your response as:
TITLE: [Catchy title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['success', 'discipline', 'hustle', 'mindset', 'goals', 'failure', 'persistence']
    },
    'facts': {
        'name': 'Amazing Facts',
        'system_prompt': '''You are a facts content creator specializing in mind-blowing, viral-worthy facts.
Create scripts that present fascinating facts in an engaging, surprising way.
Include relevant visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a "Did You Know" style facts video script.

Requirements:
- Duration: 30-60 seconds when spoken
- Hook: Start with the most surprising fact
- Include 3-5 visual scene descriptions as [VISUAL: description]
- Facts should be accurate and verifiable
- End with the most mind-blowing detail

Topic focus: {topic}

Format your response as:
TITLE: [Catchy title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['science', 'history', 'nature', 'technology', 'space', 'human body', 'psychology']
    },
    'horror': {
        'name': 'Horror Stories',
        'system_prompt': '''You are a horror story narrator creating creepy, atmospheric short stories.
Build tension and create vivid, unsettling imagery.
Include dark, atmospheric visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a short horror story for a video.

Requirements:
- Duration: 45-90 seconds when spoken
- Hook: Start with an unsettling detail
- Include 4-6 dark visual scene descriptions as [VISUAL: description]
- Build suspense throughout
- End with a chilling twist

Style: {topic}

Format your response as:
TITLE: [Creepy title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['true crime', 'paranormal', 'psychological', 'urban legend', 'cosmic horror', 'folklore']
    },
    'educational': {
        'name': 'Educational',
        'system_prompt': '''You are an educational content creator making complex topics accessible and engaging.
Explain concepts clearly with memorable examples and visuals.
Include illustrative visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate an educational video script that makes learning engaging.

Requirements:
- Duration: 45-90 seconds when spoken
- Hook: Start with a surprising question or misconception
- Include 3-5 visual scene descriptions as [VISUAL: description]
- Explain clearly with examples
- End with key takeaway

Topic: {topic}

Format your response as:
TITLE: [Catchy educational title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['science', 'history', 'economics', 'psychology', 'philosophy', 'technology']
    },
    'quotes': {
        'name': 'Powerful Quotes',
        'system_prompt': '''You are a quotes content creator combining wisdom with powerful delivery.
Present quotes with context and impact.
Include atmospheric visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a quotes video script with powerful delivery.

Requirements:
- Duration: 30-45 seconds when spoken
- Include 1-3 related quotes
- Provide brief context for each quote
- Include 3-4 visual scene descriptions as [VISUAL: description]
- End with reflection

Theme: {topic}

Format your response as:
TITLE: [Theme-based title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['success', 'love', 'strength', 'wisdom', 'life', 'leadership', 'creativity']
    },
    'stories': {
        'name': 'Short Stories',
        'system_prompt': '''You are a storyteller creating compelling micro-narratives for video.
Craft stories with emotional arcs and vivid imagery.
Include cinematic visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a short story for video narration.

Requirements:
- Duration: 60-90 seconds when spoken
- Hook: Start in the middle of action
- Include 4-6 visual scene descriptions as [VISUAL: description]
- Create emotional connection
- End with meaningful conclusion

Genre/Theme: {topic}

Format your response as:
TITLE: [Story title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['redemption', 'love', 'loss', 'triumph', 'mystery', 'adventure', 'slice of life']
    },
    'custom': {
        'name': 'Custom Template',
        'system_prompt': '''You are a versatile video script writer.
Create engaging scripts based on user requirements.
Include visual descriptions marked with [VISUAL: description].''',
        'user_prompt': '''Generate a video script based on the following requirements:

{topic}

Include visual scene descriptions marked as [VISUAL: description].

Format your response as:
TITLE: [Catchy title]
SCRIPT:
[Your script with [VISUAL: ...] markers]''',
        'topics': ['custom']
    }
}


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

        # Voice settings frame (dynamic based on selection)
        self.voice_settings_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        self.voice_settings_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Create all voice settings frames
        self.create_elevenlabs_settings()
        self.create_generic_voice_settings()

        # Bind selection change
        for child in source_frame.winfo_children():
            if isinstance(child, tk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, tk.Radiobutton):
                        widget.configure(command=self.on_voice_source_change)

        # Initial settings display
        self.on_voice_source_change()

    def create_elevenlabs_settings(self):
        """Create ElevenLabs specific settings"""
        self.elevenlabs_frame = tk.Frame(self.voice_settings_frame, bg=DashboardStyles.BG_CARD)

        tk.Label(self.elevenlabs_frame, text="ElevenLabs Settings",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        # API Key
        api_frame = tk.Frame(self.elevenlabs_frame, bg=DashboardStyles.BG_CARD)
        api_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(api_frame, text="API Key:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.elevenlabs_key_var = tk.StringVar(value=self.settings.get('elevenlabs_api_key', ''))
        tk.Entry(api_frame, textvariable=self.elevenlabs_key_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), show='*', width=40).pack(side='left', padx=10)

        tk.Button(api_frame, text="Save",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.save_elevenlabs_key).pack(side='left', padx=5)

        tk.Button(api_frame, text="Load Voices",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 command=self.load_elevenlabs_voices).pack(side='left', padx=5)

        # Voice Selection
        voice_frame = tk.Frame(self.elevenlabs_frame, bg=DashboardStyles.BG_CARD)
        voice_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(voice_frame, text="Voice:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.elevenlabs_voice_var = tk.StringVar()
        self.elevenlabs_voice_combo = ttk.Combobox(voice_frame, textvariable=self.elevenlabs_voice_var,
                                                   state='readonly', width=30)
        self.elevenlabs_voice_combo.pack(side='left', padx=10)

        # Recommended voices
        recommended = ['Rachel', 'Adam', 'Bella', 'Josh', 'Arnold', 'Antoni', 'Domi', 'Elli']
        self.elevenlabs_voice_combo['values'] = recommended
        if recommended:
            self.elevenlabs_voice_var.set(recommended[0])

        # Voice Settings
        settings_row = tk.Frame(self.elevenlabs_frame, bg=DashboardStyles.BG_CARD)
        settings_row.pack(fill='x', padx=15, pady=5)

        # Stability
        tk.Label(settings_row, text="Stability:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.elevenlabs_stability_var = tk.DoubleVar(value=0.5)
        tk.Scale(settings_row, from_=0, to=1, resolution=0.1,
                orient='horizontal', variable=self.elevenlabs_stability_var,
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                length=100).pack(side='left', padx=(5, 20))

        # Similarity
        tk.Label(settings_row, text="Similarity:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.elevenlabs_similarity_var = tk.DoubleVar(value=0.75)
        tk.Scale(settings_row, from_=0, to=1, resolution=0.1,
                orient='horizontal', variable=self.elevenlabs_similarity_var,
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                length=100).pack(side='left', padx=5)

        # Model selection
        model_frame = tk.Frame(self.elevenlabs_frame, bg=DashboardStyles.BG_CARD)
        model_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(model_frame, text="Model:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.elevenlabs_model_var = tk.StringVar(value='eleven_monolingual_v1')
        ttk.Combobox(model_frame, textvariable=self.elevenlabs_model_var,
                    values=['eleven_monolingual_v1', 'eleven_multilingual_v2', 'eleven_turbo_v2'],
                    state='readonly', width=25).pack(side='left', padx=10)

        # Test button
        tk.Button(self.elevenlabs_frame, text="🔊 Test Voice",
                 bg=DashboardStyles.ACCENT_WARNING, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=15, pady=8,
                 command=self.test_elevenlabs_voice).pack(pady=15)

    def create_generic_voice_settings(self):
        """Create generic voice settings for other sources"""
        self.generic_voice_frame = tk.Frame(self.voice_settings_frame, bg=DashboardStyles.BG_CARD)

        tk.Label(self.generic_voice_frame, text="Voice Settings",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        tk.Label(self.generic_voice_frame,
                text="Voice settings from main GUI will be used.\nCloud TTS, Kokoro, and NeuTTS are configured in the main application.",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 10)).pack(padx=15, pady=20)

        # Import audio option
        import_frame = tk.Frame(self.generic_voice_frame, bg=DashboardStyles.BG_CARD)
        import_frame.pack(fill='x', padx=15, pady=10)

        tk.Label(import_frame, text="Or import existing audio:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        btn_frame = tk.Frame(import_frame, bg=DashboardStyles.BG_CARD)
        btn_frame.pack(fill='x')

        self.import_audio_var = tk.StringVar()
        tk.Entry(btn_frame, textvariable=self.import_audio_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=40).pack(side='left', padx=(0, 10))

        tk.Button(btn_frame, text="Browse",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.browse_import_audio).pack(side='left')

    def on_voice_source_change(self):
        """Handle voice source selection change"""
        source = self.voice_source_var.get()

        # Hide all frames
        self.elevenlabs_frame.pack_forget()
        self.generic_voice_frame.pack_forget()

        # Show appropriate frame
        if source == 'elevenlabs':
            self.elevenlabs_frame.pack(fill='both', expand=True)
        else:
            self.generic_voice_frame.pack(fill='both', expand=True)

    def save_elevenlabs_key(self):
        """Save ElevenLabs API key"""
        self.settings['elevenlabs_api_key'] = self.elevenlabs_key_var.get()
        self.save_settings()
        messagebox.showinfo("Saved", "ElevenLabs API key saved!")

    def load_elevenlabs_voices(self):
        """Load available voices from ElevenLabs"""
        api_key = self.elevenlabs_key_var.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter your ElevenLabs API key first")
            return

        try:
            response = requests.get(
                'https://api.elevenlabs.io/v1/voices',
                headers={'xi-api-key': api_key},
                timeout=30
            )

            if response.status_code == 200:
                voices = response.json().get('voices', [])
                voice_names = [v['name'] for v in voices]
                self.elevenlabs_voice_combo['values'] = voice_names
                if voice_names:
                    self.elevenlabs_voice_var.set(voice_names[0])
                messagebox.showinfo("Success", f"Loaded {len(voice_names)} voices!")
            else:
                messagebox.showerror("Error", f"Failed to load voices: {response.status_code}")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading voices: {str(e)}")

    def test_elevenlabs_voice(self):
        """Test ElevenLabs voice with sample text"""
        api_key = self.elevenlabs_key_var.get()
        voice_name = self.elevenlabs_voice_var.get()

        if not api_key:
            messagebox.showerror("Error", "Please enter your ElevenLabs API key")
            return

        if not voice_name:
            messagebox.showerror("Error", "Please select a voice")
            return

        # First get voice ID
        try:
            response = requests.get(
                'https://api.elevenlabs.io/v1/voices',
                headers={'xi-api-key': api_key},
                timeout=30
            )

            if response.status_code != 200:
                messagebox.showerror("Error", "Failed to fetch voices")
                return

            voices = response.json().get('voices', [])
            voice_id = None
            for v in voices:
                if v['name'] == voice_name:
                    voice_id = v['voice_id']
                    break

            if not voice_id:
                messagebox.showerror("Error", f"Voice '{voice_name}' not found")
                return

            # Generate test audio
            response = requests.post(
                f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
                headers={
                    'xi-api-key': api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'text': 'Hello! This is a test of the ElevenLabs voice synthesis.',
                    'model_id': self.elevenlabs_model_var.get(),
                    'voice_settings': {
                        'stability': self.elevenlabs_stability_var.get(),
                        'similarity_boost': self.elevenlabs_similarity_var.get()
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                # Save to temp file and play
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    f.write(response.content)
                    temp_path = f.name

                # Try to play audio
                try:
                    import subprocess
                    if os.name == 'nt':  # Windows
                        os.startfile(temp_path)
                    else:
                        subprocess.run(['xdg-open', temp_path], check=True)
                except:
                    messagebox.showinfo("Success", f"Audio saved to: {temp_path}")
            else:
                messagebox.showerror("Error", f"Failed to generate audio: {response.status_code}")

        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")

    def browse_import_audio(self):
        """Browse for audio file to import"""
        file = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[('Audio Files', '*.mp3 *.wav *.ogg *.m4a'), ('All Files', '*.*')]
        )
        if file:
            self.import_audio_var.set(file)

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

        # Visual settings frame (dynamic based on selection)
        self.visual_settings_frame = tk.Frame(tab, bg=DashboardStyles.BG_CARD)
        self.visual_settings_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Create all visual settings frames
        self.create_comfyui_settings()
        self.create_local_folder_settings()
        self.create_api_visual_settings()

        # Bind selection change
        for child in source_frame.winfo_children():
            if isinstance(child, tk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, tk.Radiobutton):
                        widget.configure(command=self.on_visual_source_change)

        # Initial settings display
        self.on_visual_source_change()

    def create_comfyui_settings(self):
        """Create ComfyUI specific settings"""
        self.comfyui_frame = tk.Frame(self.visual_settings_frame, bg=DashboardStyles.BG_CARD)

        tk.Label(self.comfyui_frame, text="ComfyUI Settings",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        # Server URL
        url_frame = tk.Frame(self.comfyui_frame, bg=DashboardStyles.BG_CARD)
        url_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(url_frame, text="Server URL:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.comfyui_url_var = tk.StringVar(value=self.settings.get('comfyui_url', 'http://localhost:8188'))
        tk.Entry(url_frame, textvariable=self.comfyui_url_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=35).pack(side='left', padx=10)

        tk.Button(url_frame, text="Test Connection",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.test_comfyui_connection).pack(side='left', padx=5)

        # Workflow file
        workflow_frame = tk.Frame(self.comfyui_frame, bg=DashboardStyles.BG_CARD)
        workflow_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(workflow_frame, text="Workflow JSON:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.comfyui_workflow_var = tk.StringVar()
        tk.Entry(workflow_frame, textvariable=self.comfyui_workflow_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=35).pack(side='left', padx=10)

        tk.Button(workflow_frame, text="Browse",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.browse_comfyui_workflow).pack(side='left', padx=5)

        # Checkpoint/Model
        model_frame = tk.Frame(self.comfyui_frame, bg=DashboardStyles.BG_CARD)
        model_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(model_frame, text="Checkpoint:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.comfyui_checkpoint_var = tk.StringVar(value='dreamshaper_8.safetensors')
        ttk.Combobox(model_frame, textvariable=self.comfyui_checkpoint_var,
                    values=['dreamshaper_8.safetensors', 'sd_xl_base_1.0.safetensors',
                           'juggernautXL_v9.safetensors', 'realvisxlV50_v50Bakedvae.safetensors'],
                    width=35).pack(side='left', padx=10)

        # Image settings
        size_frame = tk.Frame(self.comfyui_frame, bg=DashboardStyles.BG_CARD)
        size_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(size_frame, text="Size:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.comfyui_width_var = tk.IntVar(value=1080)
        tk.Entry(size_frame, textvariable=self.comfyui_width_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=6).pack(side='left', padx=5)

        tk.Label(size_frame, text="x",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.comfyui_height_var = tk.IntVar(value=1920)
        tk.Entry(size_frame, textvariable=self.comfyui_height_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=6).pack(side='left', padx=5)

        # Steps and CFG
        tk.Label(size_frame, text="Steps:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left', padx=(20, 0))

        self.comfyui_steps_var = tk.IntVar(value=20)
        tk.Entry(size_frame, textvariable=self.comfyui_steps_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=4).pack(side='left', padx=5)

        tk.Label(size_frame, text="CFG:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left', padx=(10, 0))

        self.comfyui_cfg_var = tk.DoubleVar(value=7.0)
        tk.Entry(size_frame, textvariable=self.comfyui_cfg_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=4).pack(side='left', padx=5)

        # Output folder
        output_frame = tk.Frame(self.comfyui_frame, bg=DashboardStyles.BG_CARD)
        output_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(output_frame, text="Output Folder:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.comfyui_output_var = tk.StringVar()
        tk.Entry(output_frame, textvariable=self.comfyui_output_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=35).pack(side='left', padx=10)

        tk.Button(output_frame, text="Browse",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=lambda: self.comfyui_output_var.set(
                     filedialog.askdirectory(title="Select Output Folder")
                 )).pack(side='left', padx=5)

        # Save settings button
        tk.Button(self.comfyui_frame, text="Save ComfyUI Settings",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=15, pady=8,
                 command=self.save_comfyui_settings).pack(pady=15)

    def create_local_folder_settings(self):
        """Create local folder settings"""
        self.local_folder_frame = tk.Frame(self.visual_settings_frame, bg=DashboardStyles.BG_CARD)

        tk.Label(self.local_folder_frame, text="Local Clips Folder",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        folder_frame = tk.Frame(self.local_folder_frame, bg=DashboardStyles.BG_CARD)
        folder_frame.pack(fill='x', padx=15, pady=5)

        self.clips_folder_var = tk.StringVar()
        tk.Entry(folder_frame, textvariable=self.clips_folder_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=50).pack(side='left', padx=(0, 10))

        tk.Button(folder_frame, text="Browse",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=self.browse_clips_folder).pack(side='left')

        tk.Label(self.local_folder_frame,
                text="Files should be numbered: 1.mp4, 2.mp4, 3.jpg, etc.\nWill be merged in sequence matching visual prompts.",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', padx=15, pady=(10, 15))

        # Preview of folder contents
        tk.Button(self.local_folder_frame, text="Preview Contents",
                 bg=DashboardStyles.ACCENT_WARNING, fg='white',
                 font=('Segoe UI', 10), padx=15, pady=8,
                 command=self.preview_local_clips).pack(pady=10)

    def create_api_visual_settings(self):
        """Create API-based visual generator settings"""
        self.api_visual_frame = tk.Frame(self.visual_settings_frame, bg=DashboardStyles.BG_CARD)

        tk.Label(self.api_visual_frame, text="API Visual Generator",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 10))

        tk.Label(self.api_visual_frame,
                text="Configure API keys for cloud-based image/video generation.\n"
                     "Support for Nano Banana, Sora, Kling, Hailuo, and Meta AI.",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 10)).pack(padx=15, pady=10)

        # API Key entry
        api_frame = tk.Frame(self.api_visual_frame, bg=DashboardStyles.BG_CARD)
        api_frame.pack(fill='x', padx=15, pady=5)

        tk.Label(api_frame, text="API Key:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(side='left')

        self.visual_api_key_var = tk.StringVar(value=self.settings.get('visual_api_key', ''))
        tk.Entry(api_frame, textvariable=self.visual_api_key_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), show='*', width=40).pack(side='left', padx=10)

        tk.Button(api_frame, text="Save",
                 bg=DashboardStyles.ACCENT_INFO, fg='white',
                 command=lambda: self.save_visual_api_key()).pack(side='left', padx=5)

        tk.Label(self.api_visual_frame,
                text="Note: Each API service requires its own key.\nConfigure based on your selected source above.",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9, 'italic')).pack(padx=15, pady=(20, 15))

    def on_visual_source_change(self):
        """Handle visual source selection change"""
        source = self.visual_source_var.get()

        # Hide all frames
        self.comfyui_frame.pack_forget()
        self.local_folder_frame.pack_forget()
        self.api_visual_frame.pack_forget()

        # Show appropriate frame
        if source == 'comfyui':
            self.comfyui_frame.pack(fill='both', expand=True)
        elif source == 'local':
            self.local_folder_frame.pack(fill='both', expand=True)
        else:
            self.api_visual_frame.pack(fill='both', expand=True)

    def test_comfyui_connection(self):
        """Test ComfyUI server connection"""
        url = self.comfyui_url_var.get()
        try:
            response = requests.get(f"{url}/system_stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                vram = stats.get('devices', [{}])[0].get('vram_free', 0) / (1024**3)
                messagebox.showinfo("Success",
                                   f"Connected to ComfyUI!\nFree VRAM: {vram:.1f} GB")
            else:
                messagebox.showerror("Error", f"Server returned: {response.status_code}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "Could not connect to ComfyUI server.\nMake sure it's running.")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def browse_comfyui_workflow(self):
        """Browse for ComfyUI workflow JSON"""
        file = filedialog.askopenfilename(
            title="Select ComfyUI Workflow",
            filetypes=[('JSON Files', '*.json'), ('All Files', '*.*')]
        )
        if file:
            self.comfyui_workflow_var.set(file)

    def save_comfyui_settings(self):
        """Save ComfyUI settings"""
        self.settings['comfyui_url'] = self.comfyui_url_var.get()
        self.settings['comfyui_workflow'] = self.comfyui_workflow_var.get()
        self.settings['comfyui_checkpoint'] = self.comfyui_checkpoint_var.get()
        self.settings['comfyui_width'] = self.comfyui_width_var.get()
        self.settings['comfyui_height'] = self.comfyui_height_var.get()
        self.settings['comfyui_steps'] = self.comfyui_steps_var.get()
        self.settings['comfyui_cfg'] = self.comfyui_cfg_var.get()
        self.settings['comfyui_output'] = self.comfyui_output_var.get()
        self.save_settings()
        messagebox.showinfo("Saved", "ComfyUI settings saved!")

    def preview_local_clips(self):
        """Preview contents of local clips folder"""
        folder = self.clips_folder_var.get()
        if not folder:
            messagebox.showerror("Error", "Please select a folder first")
            return

        try:
            from pathlib import Path
            folder_path = Path(folder)
            if not folder_path.exists():
                messagebox.showerror("Error", "Folder does not exist")
                return

            # Find all media files
            extensions = ['.mp4', '.mov', '.avi', '.jpg', '.jpeg', '.png', '.webp']
            files = []
            for ext in extensions:
                files.extend(folder_path.glob(f"*{ext}"))
                files.extend(folder_path.glob(f"*{ext.upper()}"))

            # Sort by name
            files = sorted(files, key=lambda x: x.name)

            if files:
                file_list = "\n".join([f"  {f.name}" for f in files[:20]])
                if len(files) > 20:
                    file_list += f"\n  ... and {len(files) - 20} more files"
                messagebox.showinfo("Folder Contents",
                                   f"Found {len(files)} media files:\n\n{file_list}")
            else:
                messagebox.showinfo("Empty", "No media files found in folder")

        except Exception as e:
            messagebox.showerror("Error", f"Error reading folder: {str(e)}")

    def save_visual_api_key(self):
        """Save visual API key"""
        self.settings['visual_api_key'] = self.visual_api_key_var.get()
        self.save_settings()
        messagebox.showinfo("Saved", "Visual API key saved!")

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
        # Create configuration dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Configure LLM API")
        dialog.geometry("500x400")
        dialog.configure(bg=DashboardStyles.BG_DARK)
        dialog.transient(self.window)
        dialog.grab_set()

        # Provider selection
        tk.Label(dialog, text="API Configuration",
                bg=DashboardStyles.BG_DARK, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 14, 'bold')).pack(pady=(20, 15))

        # OpenAI
        openai_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
        openai_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(openai_frame, text="OpenAI API Key:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

        openai_key_var = tk.StringVar(value=self.settings.get('openai_api_key', ''))
        tk.Entry(openai_frame, textvariable=openai_key_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), show='*', width=50).pack(padx=10, pady=(0, 10))

        # OpenRouter
        router_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
        router_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(router_frame, text="OpenRouter API Key:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

        router_key_var = tk.StringVar(value=self.settings.get('openrouter_api_key', ''))
        tk.Entry(router_frame, textvariable=router_key_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), show='*', width=50).pack(padx=10, pady=(0, 10))

        # Anthropic
        anthropic_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
        anthropic_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(anthropic_frame, text="Anthropic API Key:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

        anthropic_key_var = tk.StringVar(value=self.settings.get('anthropic_api_key', ''))
        tk.Entry(anthropic_frame, textvariable=anthropic_key_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), show='*', width=50).pack(padx=10, pady=(0, 10))

        # Local LLM URL
        local_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
        local_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(local_frame, text="Local LLM URL (e.g., http://localhost:11434):",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

        local_url_var = tk.StringVar(value=self.settings.get('local_llm_url', 'http://localhost:11434'))
        tk.Entry(local_frame, textvariable=local_url_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=50).pack(padx=10, pady=(0, 10))

        def save_api_config():
            self.settings['openai_api_key'] = openai_key_var.get()
            self.settings['openrouter_api_key'] = router_key_var.get()
            self.settings['anthropic_api_key'] = anthropic_key_var.get()
            self.settings['local_llm_url'] = local_url_var.get()
            self.save_settings()
            messagebox.showinfo("Saved", "API configuration saved!")
            dialog.destroy()

        tk.Button(dialog, text="Save Configuration",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=20, pady=10,
                 command=save_api_config).pack(pady=20)

    def call_llm_api(self, provider, system_prompt, user_prompt):
        """Call the selected LLM API"""
        try:
            if provider == 'openai':
                api_key = self.settings.get('openai_api_key', '')
                if not api_key:
                    return None, "OpenAI API key not configured"

                response = requests.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'gpt-4o-mini',
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ],
                        'max_tokens': 1500,
                        'temperature': 0.8
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content'], None
                else:
                    return None, f"OpenAI API error: {response.status_code} - {response.text}"

            elif provider == 'openrouter':
                api_key = self.settings.get('openrouter_api_key', '')
                if not api_key:
                    return None, "OpenRouter API key not configured"

                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'anthropic/claude-3-haiku',
                        'messages': [
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_prompt}
                        ],
                        'max_tokens': 1500,
                        'temperature': 0.8
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content'], None
                else:
                    return None, f"OpenRouter API error: {response.status_code} - {response.text}"

            elif provider == 'anthropic':
                api_key = self.settings.get('anthropic_api_key', '')
                if not api_key:
                    return None, "Anthropic API key not configured"

                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': api_key,
                        'Content-Type': 'application/json',
                        'anthropic-version': '2023-06-01'
                    },
                    json={
                        'model': 'claude-3-haiku-20240307',
                        'max_tokens': 1500,
                        'system': system_prompt,
                        'messages': [
                            {'role': 'user', 'content': user_prompt}
                        ]
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    return response.json()['content'][0]['text'], None
                else:
                    return None, f"Anthropic API error: {response.status_code} - {response.text}"

            elif provider == 'local':
                # Ollama-compatible API
                local_url = self.settings.get('local_llm_url', 'http://localhost:11434')

                response = requests.post(
                    f'{local_url}/api/generate',
                    json={
                        'model': 'llama3.2',
                        'prompt': f"{system_prompt}\n\n{user_prompt}",
                        'stream': False
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    return response.json().get('response', ''), None
                else:
                    return None, f"Local LLM error: {response.status_code} - {response.text}"

            else:
                return None, f"Unknown provider: {provider}"

        except requests.exceptions.Timeout:
            return None, "Request timed out"
        except requests.exceptions.ConnectionError:
            return None, "Connection error - check your network or server"
        except Exception as e:
            return None, f"Error: {str(e)}"

    def generate_scripts(self):
        """Generate scripts using AI"""
        num = self.num_scripts_var.get()
        template_key = self.content_template_var.get()
        provider = self.llm_provider_var.get()

        # Get template
        template = CONTENT_TEMPLATES.get(template_key, CONTENT_TEMPLATES['stoic'])

        self.script_preview.delete('1.0', tk.END)
        self.script_preview.insert('1.0', f"Generating {num} {template['name']} script(s) using {provider}...\n\n")
        self.window.update()

        # Generate in thread
        def generate_thread():
            import random

            for i in range(num):
                # Select random topic from template
                topic = random.choice(template['topics'])

                # Format prompts
                system_prompt = template['system_prompt']
                user_prompt = template['user_prompt'].format(topic=topic)

                # Add custom topic input for custom template
                if template_key == 'custom':
                    custom_topic = self.script_preview.get('1.0', tk.END).strip()
                    if custom_topic and not custom_topic.startswith('Generating'):
                        topic = custom_topic
                        user_prompt = template['user_prompt'].format(topic=topic)

                # Call API
                self.script_preview.insert(tk.END, f"\n--- Script {i+1}/{num} (Topic: {topic}) ---\n")
                self.window.update()

                result, error = self.call_llm_api(provider, system_prompt, user_prompt)

                if error:
                    self.script_preview.insert(tk.END, f"\n❌ Error: {error}\n")
                else:
                    self.script_preview.insert(tk.END, f"\n{result}\n")

                self.window.update()

            self.script_preview.insert(tk.END, "\n\n✅ Generation complete!")

        thread = threading.Thread(target=generate_thread, daemon=True)
        thread.start()

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
        # Create dialog for adding account
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Add {platform.title()} Account")
        dialog.geometry("450x400")
        dialog.configure(bg=DashboardStyles.BG_DARK)
        dialog.transient(self.window)
        dialog.grab_set()

        tk.Label(dialog, text=f"Add {platform.title()} Account",
                bg=DashboardStyles.BG_DARK, fg=DashboardStyles.TEXT_WHITE,
                font=('Segoe UI', 14, 'bold')).pack(pady=(20, 15))

        # Account name
        name_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
        name_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(name_frame, text="Account Name:",
                bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

        name_var = tk.StringVar()
        tk.Entry(name_frame, textvariable=name_var,
                bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                font=('Segoe UI', 10), width=40).pack(padx=10, pady=(0, 10))

        # Platform-specific fields
        if platform == 'youtube':
            # YouTube API credentials
            cred_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
            cred_frame.pack(fill='x', padx=20, pady=5)

            tk.Label(cred_frame, text="OAuth Client JSON:",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

            cred_var = tk.StringVar()
            cred_entry_frame = tk.Frame(cred_frame, bg=DashboardStyles.BG_CARD)
            cred_entry_frame.pack(fill='x', padx=10, pady=(0, 10))

            tk.Entry(cred_entry_frame, textvariable=cred_var,
                    bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10), width=30).pack(side='left')

            tk.Button(cred_entry_frame, text="Browse",
                     bg=DashboardStyles.ACCENT_INFO, fg='white',
                     command=lambda: cred_var.set(filedialog.askopenfilename(
                         filetypes=[('JSON Files', '*.json')]))).pack(side='left', padx=5)

            tk.Label(cred_frame, text="Get credentials from Google Cloud Console",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                    font=('Segoe UI', 8)).pack(anchor='w', padx=10)

        elif platform == 'tiktok':
            # TikTok session cookie
            cred_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
            cred_frame.pack(fill='x', padx=20, pady=5)

            tk.Label(cred_frame, text="Session Cookie (sessionid):",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

            cred_var = tk.StringVar()
            tk.Entry(cred_frame, textvariable=cred_var,
                    bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10), width=40, show='*').pack(padx=10, pady=(0, 10))

            tk.Label(cred_frame, text="Get from browser cookies after login",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                    font=('Segoe UI', 8)).pack(anchor='w', padx=10)

        elif platform == 'instagram':
            # Instagram credentials
            cred_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
            cred_frame.pack(fill='x', padx=20, pady=5)

            tk.Label(cred_frame, text="Username:",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

            username_var = tk.StringVar()
            tk.Entry(cred_frame, textvariable=username_var,
                    bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10), width=40).pack(padx=10, pady=(0, 5))

            tk.Label(cred_frame, text="Password:",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(5, 5))

            cred_var = tk.StringVar()
            tk.Entry(cred_frame, textvariable=cred_var,
                    bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10), width=40, show='*').pack(padx=10, pady=(0, 10))

        elif platform == 'facebook':
            # Facebook Page access token
            cred_frame = tk.Frame(dialog, bg=DashboardStyles.BG_CARD)
            cred_frame.pack(fill='x', padx=20, pady=5)

            tk.Label(cred_frame, text="Page Access Token:",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(10, 5))

            cred_var = tk.StringVar()
            tk.Entry(cred_frame, textvariable=cred_var,
                    bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10), width=40, show='*').pack(padx=10, pady=(0, 5))

            tk.Label(cred_frame, text="Page ID:",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10)).pack(anchor='w', padx=10, pady=(5, 5))

            page_id_var = tk.StringVar()
            tk.Entry(cred_frame, textvariable=page_id_var,
                    bg=DashboardStyles.BG_INPUT, fg=DashboardStyles.TEXT_LIGHT,
                    font=('Segoe UI', 10), width=40).pack(padx=10, pady=(0, 10))

            tk.Label(cred_frame, text="Get from Meta Developer Console",
                    bg=DashboardStyles.BG_CARD, fg=DashboardStyles.TEXT_MEDIUM,
                    font=('Segoe UI', 8)).pack(anchor='w', padx=10)
        else:
            cred_var = tk.StringVar()

        def save_account():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter an account name")
                return

            # Create account data
            account_data = {'name': name}

            if platform == 'youtube':
                account_data['credentials_file'] = cred_var.get()
            elif platform == 'tiktok':
                account_data['session_cookie'] = cred_var.get()
            elif platform == 'instagram':
                account_data['username'] = username_var.get()
                account_data['password'] = cred_var.get()
            elif platform == 'facebook':
                account_data['access_token'] = cred_var.get()
                account_data['page_id'] = page_id_var.get()

            # Add to accounts list
            if platform not in self.accounts:
                self.accounts[platform] = []
            self.accounts[platform].append(account_data)
            self.save_settings()

            messagebox.showinfo("Success", f"Account '{name}' added!")
            dialog.destroy()

            # Refresh accounts tab
            self.refresh_accounts_tab()

        tk.Button(dialog, text="Add Account",
                 bg=DashboardStyles.ACCENT_PRIMARY, fg='white',
                 font=('Segoe UI', 10, 'bold'), padx=20, pady=10,
                 command=save_account).pack(pady=20)

    def remove_account(self, platform, account):
        """Remove account"""
        if messagebox.askyesno("Remove Account", f"Remove {account['name']}?"):
            self.accounts[platform].remove(account)
            self.save_settings()
            self.refresh_accounts_tab()

    def refresh_accounts_tab(self):
        """Refresh the accounts tab to show updated accounts"""
        # Find and recreate accounts tab
        for i in range(self.notebook.index('end')):
            if self.notebook.tab(i, 'text') == '👥 Accounts':
                # Get the tab frame
                tab_frame = self.notebook.nametowidget(self.notebook.tabs()[i])
                # Clear and recreate
                for widget in tab_frame.winfo_children():
                    widget.destroy()

                # Recreate account lists
                platforms = [
                    ('youtube', '📺 YouTube Channels', 'red'),
                    ('tiktok', '🎵 TikTok Accounts', 'black'),
                    ('instagram', '📸 Instagram Accounts', 'purple'),
                    ('facebook', '📘 Facebook Pages', 'blue'),
                ]

                for platform, title, color in platforms:
                    frame = tk.Frame(tab_frame, bg=DashboardStyles.BG_CARD)
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
                break

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
