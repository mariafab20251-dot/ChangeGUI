"""
Video Automation Studio - Tab-Based Interface
Clean, professional dashboard with organized tab navigation
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog, scrolledtext
import json
from pathlib import Path
import threading
import sys
import os
from PIL import Image, ImageDraw, ImageFont, ImageTk
import numpy as np
import queue
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config import config
except ImportError:
    config = None
    logger.warning("Could not import config - using default paths")

# Import the video automation processor
try:
    from youtube_video_automation_enhanced import VideoQuoteAutomation, TTSGenerator
except ImportError:
    VideoQuoteAutomation = None
    TTSGenerator = None
    logger.error("Could not import VideoQuoteAutomation - processing will not be available")


class AppStyles:
    """Clean, professional styling"""
    # Colors
    BG_PRIMARY = '#f5f7fa'
    BG_SECONDARY = '#ffffff'
    BG_HEADER = '#2c3e50'
    BG_TAB = '#ecf0f1'

    # Accent colors
    ACCENT_BLUE = '#3498db'
    ACCENT_GREEN = '#27ae60'
    ACCENT_RED = '#e74c3c'
    ACCENT_ORANGE = '#f39c12'

    # Text colors
    TEXT_PRIMARY = '#2c3e50'
    TEXT_SECONDARY = '#7f8c8d'
    TEXT_LIGHT = '#ffffff'

    # Border
    BORDER = '#bdc3c7'
    BORDER_LIGHT = '#d5dbdb'


def get_windows_fonts():
    """Scan Windows fonts folder and return available font families"""
    try:
        if config:
            fonts_folder = config.SYSTEM_FONTS_FOLDER
        else:
            fonts_folder = Path(r"C:\Windows\Fonts")

        font_files = {}

        if not fonts_folder.exists():
            logger.warning(f"Fonts folder not found: {fonts_folder}")
            return ['Arial', 'Arial Bold', 'Impact', 'Verdana']

        # Scan for TTF fonts
        for font_file in fonts_folder.glob("*.ttf"):
            try:
                font_name = font_file.stem
                font_files[font_name] = str(font_file)
            except Exception as e:
                logger.debug(f"Could not load font {font_file}: {e}")
                continue

        return sorted(font_files.keys()) if font_files else ['Arial', 'Impact', 'Verdana']

    except Exception as e:
        logger.error(f"Error getting Windows fonts: {e}")
        return ['Arial', 'Impact', 'Verdana']


class VideoAutomationGUI:
    """Main tab-based GUI application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Video Automation Studio - Professional Edition")
        self.root.geometry("1000x750")
        self.root.configure(bg=AppStyles.BG_PRIMARY)
        self.root.resizable(True, True)
        self.root.minsize(900, 650)

        # Load settings
        self.settings = self.load_settings()
        self.paths = self.load_paths()
        self.processing = False
        self.process_thread = None

        # Variables for paths
        self.video_folder_var = tk.StringVar(value=self.paths.get('video_folder', ''))
        self.quotes_file_var = tk.StringVar(value=self.paths.get('quotes_file', ''))
        self.output_folder_var = tk.StringVar(value=self.paths.get('output_folder', ''))

        # Progress tracking
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Ready")

        self.setup_ui()
        logger.info("Application started successfully")

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            settings_file = Path('overlay_settings.json')
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("Settings file not found, using defaults")
                return {}
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {}

    def load_paths(self):
        """Load processing paths from JSON file"""
        try:
            paths_file = Path('processing_paths.json')
            if paths_file.exists():
                with open(paths_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading paths: {e}")
            return {}

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open('overlay_settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            logger.info("Settings saved successfully")
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def save_paths(self):
        """Save processing paths to JSON file"""
        try:
            paths = {
                'video_folder': self.video_folder_var.get(),
                'quotes_file': self.quotes_file_var.get(),
                'output_folder': self.output_folder_var.get()
            }
            with open('processing_paths.json', 'w', encoding='utf-8') as f:
                json.dump(paths, f, indent=2)
            logger.info("Paths saved successfully")
        except Exception as e:
            logger.error(f"Error saving paths: {e}")

    def setup_ui(self):
        """Setup the main UI"""

        # ═══════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════
        header_frame = tk.Frame(self.root, bg=AppStyles.BG_HEADER, height=70)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)

        # App title
        title_frame = tk.Frame(header_frame, bg=AppStyles.BG_HEADER)
        title_frame.pack(side='left', padx=30, pady=15)

        tk.Label(title_frame, text="🎬 Video Automation Studio",
                bg=AppStyles.BG_HEADER, fg=AppStyles.TEXT_LIGHT,
                font=('Segoe UI', 18, 'bold')).pack(anchor='w')

        tk.Label(title_frame, text="Professional Edition",
                bg=AppStyles.BG_HEADER, fg=AppStyles.TEXT_SECONDARY,
                font=('Segoe UI', 9)).pack(anchor='w')

        # Status indicator
        status_frame = tk.Frame(header_frame, bg=AppStyles.BG_HEADER)
        status_frame.pack(side='right', padx=30)

        self.status_label = tk.Label(status_frame, textvariable=self.status_var,
                                     bg=AppStyles.BG_HEADER, fg=AppStyles.ACCENT_GREEN,
                                     font=('Segoe UI', 10, 'bold'))
        self.status_label.pack()

        # ═══════════════════════════════════════════════════════════
        # TAB NOTEBOOK
        # ═══════════════════════════════════════════════════════════
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=AppStyles.BG_PRIMARY, borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 10))
        style.map('TNotebook.Tab', background=[('selected', AppStyles.BG_SECONDARY)])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=0, pady=0)

        # Create tabs
        self.create_quick_process_tab()
        self.create_text_settings_tab()
        self.create_effects_tab()
        self.create_audio_tab()
        self.create_captions_tab()
        self.create_transitions_tab()

        # ═══════════════════════════════════════════════════════════
        # PROGRESS BAR & ACTION BUTTONS
        # ═══════════════════════════════════════════════════════════
        bottom_frame = tk.Frame(self.root, bg=AppStyles.BG_SECONDARY, height=100)
        bottom_frame.pack(fill='x', side='bottom')
        bottom_frame.pack_propagate(False)

        # Progress section
        progress_frame = tk.Frame(bottom_frame, bg=AppStyles.BG_SECONDARY)
        progress_frame.pack(fill='x', padx=30, pady=10)

        tk.Label(progress_frame, text="Progress",
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 9, 'bold')).pack(anchor='w')

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate',
                                           variable=self.progress_var)
        self.progress_bar.pack(fill='x', pady=5)

        self.progress_text = tk.Label(progress_frame, text="Ready",
                                     bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_SECONDARY,
                                     font=('Segoe UI', 9))
        self.progress_text.pack(anchor='w')

        # Action buttons
        button_frame = tk.Frame(bottom_frame, bg=AppStyles.BG_SECONDARY)
        button_frame.pack(pady=5)

        self.btn_process = tk.Button(button_frame, text="▶ Process Now",
                                     bg=AppStyles.ACCENT_GREEN, fg='white',
                                     font=('Segoe UI', 11, 'bold'),
                                     relief='flat', padx=30, pady=10,
                                     cursor='hand2',
                                     command=self.start_processing)
        self.btn_process.pack(side='left', padx=5)

        self.btn_stop = tk.Button(button_frame, text="■ Stop",
                                 bg=AppStyles.ACCENT_RED, fg='white',
                                 font=('Segoe UI', 11, 'bold'),
                                 relief='flat', padx=30, pady=10,
                                 cursor='hand2', state='disabled',
                                 command=self.stop_processing)
        self.btn_stop.pack(side='left', padx=5)

        self.btn_save = tk.Button(button_frame, text="💾 Save Settings",
                                 bg=AppStyles.ACCENT_BLUE, fg='white',
                                 font=('Segoe UI', 11, 'bold'),
                                 relief='flat', padx=30, pady=10,
                                 cursor='hand2',
                                 command=self.save_settings)
        self.btn_save.pack(side='left', padx=5)

    def create_quick_process_tab(self):
        """Create Quick Process tab"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_PRIMARY)
        self.notebook.add(tab, text='Quick Process')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_PRIMARY)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Input Source Section
        self.create_section(content, "📁 Input Source", [
            ('Video Folder:', self.video_folder_var, self.browse_video_folder),
            ('Quotes File:', self.quotes_file_var, self.browse_quotes_file),
        ])

        # Output Settings Section
        self.create_section(content, "📂 Output Settings", [
            ('Output Folder:', self.output_folder_var, self.browse_output_folder),
        ])

        # Processing Options Section
        proc_frame = self.create_section_frame(content, "⚙️ Processing Options")

        options = [
            ('enable_captions', '📝 Generate Captions'),
            ('use_tts_voiceover', '🔊 Generate TTS Voiceover'),
            ('add_custom_bgm', '🎵 Add Background Music'),
            ('video_zoom', '🔍 Apply Video Zoom Effect'),
            ('pulsing_cta', '💓 Pulsing Call-to-Action'),
        ]

        for key, label in options:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(proc_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)
            setattr(self, f'{key}_var', var)

        # Quick Stats Section
        stats_frame = self.create_section_frame(content, "📊 Quick Stats")

        stats_text = f"""Videos Ready: {self.count_videos()}
Quotes Available: {self.count_quotes()}
Output Path Set: {'✓' if self.output_folder_var.get() else '✗'}
Settings Loaded: ✓"""

        tk.Label(stats_frame, text=stats_text,
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10), justify='left').pack(anchor='w', padx=20, pady=10)

    def create_text_settings_tab(self):
        """Create Text Settings tab"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_PRIMARY)
        self.notebook.add(tab, text='Text Settings')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_PRIMARY)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Title Settings
        title_frame = self.create_section_frame(content, "📌 Title Settings")
        self.create_text_controls(title_frame, 'title')

        # Quote Settings
        quote_frame = self.create_section_frame(content, "💬 Quote Settings")
        self.create_text_controls(quote_frame, 'quote')

        # CTA Settings
        cta_frame = self.create_section_frame(content, "🎯 Call-to-Action Settings")
        self.create_text_controls(cta_frame, 'cta')

    def create_effects_tab(self):
        """Create Visual Effects tab"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_PRIMARY)
        self.notebook.add(tab, text='Visual Effects')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_PRIMARY)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Text Effects
        text_fx_frame = self.create_section_frame(content, "✍️ Text Effects")

        text_effects = [
            ('text_fade_in', '💫 Fade In'),
            ('text_slide_up', '⬆️ Slide Up'),
            ('text_bounce', '🎾 Bounce'),
            ('text_kinetic', '⚡ Kinetic Typing'),
            ('text_glitch', '📺 Glitch Effect'),
        ]

        for key, label in text_effects:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(text_fx_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)

        # Visual Effects
        visual_fx_frame = self.create_section_frame(content, "🌟 Visual Effects")

        visual_effects = [
            ('text_glow', '✨ Text Glow'),
            ('vignette', '🌑 Vignette'),
            ('background_dim', '🌙 Background Dim'),
            ('film_grain', '🎞️ Film Grain'),
            ('neon_glow', '💡 Neon Glow'),
            ('drop_shadow', '👤 Drop Shadow'),
        ]

        for key, label in visual_effects:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(visual_fx_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)

        # Particle Effects
        particle_fx_frame = self.create_section_frame(content, "🎊 Particle Effects")

        particle_effects = [
            ('add_glitter', '✨ Glitter'),
            ('add_stars', '⭐ Stars'),
            ('add_hearts', '❤️ Hearts'),
            ('add_confetti', '🎉 Confetti'),
        ]

        for key, label in particle_effects:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(particle_fx_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)

    def create_audio_tab(self):
        """Create Audio Settings tab"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_PRIMARY)
        self.notebook.add(tab, text='Audio Settings')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_PRIMARY)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # TTS Settings
        tts_frame = self.create_section_frame(content, "🗣️ Text-to-Speech Settings")

        # TTS Enable
        tts_var = tk.BooleanVar(value=self.settings.get('use_tts_voiceover', True))
        tk.Checkbutton(tts_frame, text='Enable TTS Voiceover',
                      variable=tts_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10, 'bold'), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting('use_tts_voiceover', tts_var.get())).pack(anchor='w', padx=20, pady=10)

        # TTS Voice selection
        voice_frame = tk.Frame(tts_frame, bg=AppStyles.BG_SECONDARY)
        voice_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(voice_frame, text='Voice:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        voices = ['andrew_multi', 'aria_multi', 'emily_multi', 'ryan_multi']
        voice_combo = ttk.Combobox(voice_frame, values=voices, state='readonly', width=20)
        voice_combo.set(self.settings.get('tts_voice', 'andrew_multi'))
        voice_combo.pack(side='left', padx=10)
        voice_combo.bind('<<ComboboxSelected>>',
                        lambda e: self.update_setting('tts_voice', voice_combo.get()))

        # TTS Speed
        speed_frame = tk.Frame(tts_frame, bg=AppStyles.BG_SECONDARY)
        speed_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(speed_frame, text='Speed:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        speed_var = tk.IntVar(value=self.settings.get('tts_speed', 144))
        speed_scale = tk.Scale(speed_frame, from_=50, to=200, orient='horizontal',
                              variable=speed_var, bg=AppStyles.BG_SECONDARY,
                              command=lambda v: self.update_setting('tts_speed', int(float(v))))
        speed_scale.pack(side='left', fill='x', expand=True, padx=10)

        # BGM Settings
        bgm_frame = self.create_section_frame(content, "🎵 Background Music Settings")

        bgm_var = tk.BooleanVar(value=self.settings.get('add_custom_bgm', False))
        tk.Checkbutton(bgm_frame, text='Add Background Music',
                      variable=bgm_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10, 'bold'), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting('add_custom_bgm', bgm_var.get())).pack(anchor='w', padx=20, pady=10)

        # BGM File
        bgm_file_frame = tk.Frame(bgm_frame, bg=AppStyles.BG_SECONDARY)
        bgm_file_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(bgm_file_frame, text='BGM File:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        bgm_file_var = tk.StringVar(value=self.settings.get('bgm_file', ''))
        tk.Entry(bgm_file_frame, textvariable=bgm_file_var, width=40).pack(side='left', padx=10)
        tk.Button(bgm_file_frame, text='Browse', command=lambda: self.browse_bgm_file(bgm_file_var)).pack(side='left')

        # BGM Volume
        volume_frame = tk.Frame(bgm_frame, bg=AppStyles.BG_SECONDARY)
        volume_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(volume_frame, text='BGM Volume:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        bgm_volume_var = tk.DoubleVar(value=self.settings.get('bgm_volume', 0.3))
        volume_scale = tk.Scale(volume_frame, from_=0.0, to=1.0, resolution=0.1,
                               orient='horizontal', variable=bgm_volume_var,
                               bg=AppStyles.BG_SECONDARY,
                               command=lambda v: self.update_setting('bgm_volume', float(v)))
        volume_scale.pack(side='left', fill='x', expand=True, padx=10)

        # Audio Mixing
        mix_frame = self.create_section_frame(content, "🎚️ Audio Mixing")

        mute_var = tk.BooleanVar(value=self.settings.get('mute_original_audio', False))
        tk.Checkbutton(mix_frame, text='Mute Original Audio',
                      variable=mute_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting('mute_original_audio', mute_var.get())).pack(anchor='w', padx=20, pady=5)

    def create_captions_tab(self):
        """Create Captions tab"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_PRIMARY)
        self.notebook.add(tab, text='Captions')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_PRIMARY)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Caption Enable
        cap_frame = self.create_section_frame(content, "💬 Caption Settings")

        caption_var = tk.BooleanVar(value=self.settings.get('enable_captions', False))
        tk.Checkbutton(cap_frame, text='Enable Captions',
                      variable=caption_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10, 'bold'), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting('enable_captions', caption_var.get())).pack(anchor='w', padx=20, pady=10)

        # Caption Style
        style_frame = self.create_section_frame(content, "🎨 Caption Style")

        # Font size
        size_frame = tk.Frame(style_frame, bg=AppStyles.BG_SECONDARY)
        size_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(size_frame, text='Font Size:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        cap_size_var = tk.IntVar(value=self.settings.get('caption_font_size', 55))
        tk.Scale(size_frame, from_=20, to=100, orient='horizontal',
                variable=cap_size_var, bg=AppStyles.BG_SECONDARY,
                command=lambda v: self.update_setting('caption_font_size', int(float(v)))).pack(side='left', fill='x', expand=True, padx=10)

        # Caption Highlighting
        highlight_frame = self.create_section_frame(content, "🖍️ Word Highlighting")

        highlight_var = tk.BooleanVar(value=self.settings.get('caption_highlight_enabled', True))
        tk.Checkbutton(highlight_frame, text='Enable Word Highlighting',
                      variable=highlight_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting('caption_highlight_enabled', highlight_var.get())).pack(anchor='w', padx=20, pady=5)

        # Emoji in Captions
        emoji_var = tk.BooleanVar(value=self.settings.get('emoji_in_captions', True))
        tk.Checkbutton(highlight_frame, text='Include Emojis in Captions',
                      variable=emoji_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting('emoji_in_captions', emoji_var.get())).pack(anchor='w', padx=20, pady=5)

    def create_transitions_tab(self):
        """Create Transitions tab"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_PRIMARY)
        self.notebook.add(tab, text='Transitions')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_PRIMARY)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Fade Transitions
        fade_frame = self.create_section_frame(content, "🌅 Fade Transitions")

        transitions = [
            ('transition_fade_in', 'Fade In'),
            ('transition_fade_out', 'Fade Out'),
        ]

        for key, label in transitions:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(fade_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)

        # Zoom Transitions
        zoom_frame = self.create_section_frame(content, "🔍 Zoom Transitions")

        zoom_transitions = [
            ('transition_zoom_in', 'Zoom In'),
            ('transition_zoom_out', 'Zoom Out'),
        ]

        for key, label in zoom_transitions:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(zoom_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)

        # Cinematic Effects
        cinema_frame = self.create_section_frame(content, "🎬 Cinematic Effects")

        cinema_effects = [
            ('lens_flare_enabled', '✨ Lens Flare'),
            ('light_leak_enabled', '💡 Light Leaks'),
            ('film_burn_enabled', '🔥 Film Burn'),
        ]

        for key, label in cinema_effects:
            var = tk.BooleanVar(value=self.settings.get(key, False))
            chk = tk.Checkbutton(cinema_frame, text=label,
                                variable=var, bg=AppStyles.BG_SECONDARY,
                                font=('Segoe UI', 10), activebackground=AppStyles.BG_SECONDARY,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w', padx=20, pady=5)

    # Helper methods

    def create_section_frame(self, parent, title):
        """Create a section frame with title"""
        section = tk.Frame(parent, bg=AppStyles.BG_SECONDARY, relief='solid', borderwidth=1)
        section.pack(fill='x', padx=20, pady=10)

        # Section header
        header = tk.Frame(section, bg=AppStyles.BG_TAB, height=35)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=title,
                bg=AppStyles.BG_TAB, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=15, pady=5)

        return section

    def create_section(self, parent, title, fields):
        """Create a section with input fields"""
        frame = self.create_section_frame(parent, title)

        for label_text, var, browse_cmd in fields:
            field_frame = tk.Frame(frame, bg=AppStyles.BG_SECONDARY)
            field_frame.pack(fill='x', padx=20, pady=10)

            tk.Label(field_frame, text=label_text,
                    bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                    font=('Segoe UI', 10)).pack(anchor='w')

            entry_frame = tk.Frame(field_frame, bg=AppStyles.BG_SECONDARY)
            entry_frame.pack(fill='x', pady=5)

            entry = tk.Entry(entry_frame, textvariable=var, font=('Segoe UI', 9))
            entry.pack(side='left', fill='x', expand=True)

            btn = tk.Button(entry_frame, text='Browse Folder' if 'Folder' in label_text else 'Browse File',
                           bg=AppStyles.ACCENT_BLUE, fg='white',
                           font=('Segoe UI', 9), relief='flat', padx=15, pady=5,
                           command=browse_cmd)
            btn.pack(side='left', padx=5)

        return frame

    def create_text_controls(self, parent, prefix):
        """Create text controls for title/quote/cta"""
        # Enable checkbox
        enabled_var = tk.BooleanVar(value=self.settings.get(f'{prefix}_enabled', True))
        tk.Checkbutton(parent, text=f'Enable {prefix.title()}',
                      variable=enabled_var, bg=AppStyles.BG_SECONDARY,
                      font=('Segoe UI', 10, 'bold'), activebackground=AppStyles.BG_SECONDARY,
                      command=lambda: self.update_setting(f'{prefix}_enabled', enabled_var.get())).pack(anchor='w', padx=20, pady=10)

        # Font Size
        size_frame = tk.Frame(parent, bg=AppStyles.BG_SECONDARY)
        size_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(size_frame, text='Font Size:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        size_var = tk.IntVar(value=self.settings.get(f'{prefix}_font_size', 30))
        tk.Scale(size_frame, from_=10, to=100, orient='horizontal',
                variable=size_var, bg=AppStyles.BG_SECONDARY,
                command=lambda v, p=prefix: self.update_setting(f'{p}_font_size', int(float(v)))).pack(side='left', fill='x', expand=True, padx=10)

        # Text Color
        color_frame = tk.Frame(parent, bg=AppStyles.BG_SECONDARY)
        color_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(color_frame, text='Text Color:',
                bg=AppStyles.BG_SECONDARY, fg=AppStyles.TEXT_PRIMARY,
                font=('Segoe UI', 10)).pack(side='left')

        color_var = tk.StringVar(value=self.settings.get(f'{prefix}_text_color', '#FFFFFF'))
        tk.Entry(color_frame, textvariable=color_var, width=10).pack(side='left', padx=10)
        tk.Button(color_frame, text='Pick Color',
                 command=lambda p=prefix, v=color_var: self.pick_color(p, v)).pack(side='left')

    def update_setting(self, key, value):
        """Update a setting value"""
        self.settings[key] = value
        logger.debug(f"Setting updated: {key} = {value}")

    def pick_color(self, prefix, var):
        """Open color picker"""
        color = colorchooser.askcolor(title=f"Choose {prefix} color")
        if color[1]:
            var.set(color[1])
            self.update_setting(f'{prefix}_text_color', color[1])

    def browse_video_folder(self):
        """Browse for video folder"""
        folder = filedialog.askdirectory(title="Select Video Folder")
        if folder:
            self.video_folder_var.set(folder)
            self.save_paths()
            logger.info(f"Video folder selected: {folder}")

    def browse_quotes_file(self):
        """Browse for quotes file"""
        file = filedialog.askopenfilename(title="Select Quotes File",
                                         filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file:
            self.quotes_file_var.set(file)
            self.save_paths()
            logger.info(f"Quotes file selected: {file}")

    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)
            self.save_paths()
            logger.info(f"Output folder selected: {folder}")

    def browse_bgm_file(self, var):
        """Browse for BGM file"""
        file = filedialog.askopenfilename(title="Select Background Music",
                                         filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")])
        if file:
            var.set(file)
            self.update_setting('bgm_file', file)
            logger.info(f"BGM file selected: {file}")

    def count_videos(self):
        """Count videos in video folder"""
        try:
            folder = Path(self.video_folder_var.get())
            if folder.exists():
                return len(list(folder.glob('*.mp4'))) + len(list(folder.glob('*.avi'))) + len(list(folder.glob('*.mov')))
            return 0
        except:
            return 0

    def count_quotes(self):
        """Count quotes in quotes file"""
        try:
            file = Path(self.quotes_file_var.get())
            if file.exists():
                with open(file, 'r', encoding='utf-8') as f:
                    return len([line for line in f if line.strip()])
            return 0
        except:
            return 0

    def start_processing(self):
        """Start video processing"""
        # Validate inputs
        if not self.video_folder_var.get():
            messagebox.showerror("Error", "Please select a video folder")
            return

        if not self.quotes_file_var.get():
            messagebox.showerror("Error", "Please select a quotes file")
            return

        if not self.output_folder_var.get():
            messagebox.showerror("Error", "Please select an output folder")
            return

        # Save settings before processing
        self.save_settings()
        self.save_paths()

        # Start processing in thread
        self.processing = True
        self.btn_process.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.status_var.set("Processing...")
        self.status_label.config(fg=AppStyles.ACCENT_ORANGE)

        self.process_thread = threading.Thread(target=self.process_videos, daemon=True)
        self.process_thread.start()

        logger.info("Processing started")

    def stop_processing(self):
        """Stop video processing"""
        self.processing = False
        self.btn_stop.config(state='disabled')
        self.status_var.set("Stopping...")
        logger.info("Processing stop requested")

    def process_videos(self):
        """Process videos in background thread"""
        try:
            if VideoQuoteAutomation is None:
                raise Exception("VideoQuoteAutomation module not available")

            automation = VideoQuoteAutomation(
                video_folder=self.video_folder_var.get(),
                quotes_file=self.quotes_file_var.get(),
                output_folder=self.output_folder_var.get()
            )

            # Get list of videos
            videos = automation.get_video_files()
            total = len(videos)

            if total == 0:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "No videos found in the selected folder"))
                self.finish_processing()
                return

            # Process each video
            for i, video in enumerate(videos):
                if not self.processing:
                    break

                try:
                    # Update progress
                    progress = (i / total) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda i=i, t=total: self.progress_text.config(
                        text=f"Processing video {i+1} of {total}..."))

                    # Process video
                    automation.process_single_video(video)
                    logger.info(f"Completed: {video}")

                except Exception as e:
                    logger.error(f"Error processing {video}: {e}")
                    continue

            # Complete
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.progress_text.config(text="Complete!"))
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Processed {total} videos successfully!"))

        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed: {str(e)}"))

        finally:
            self.finish_processing()

    def finish_processing(self):
        """Clean up after processing"""
        self.processing = False
        self.btn_process.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.status_var.set("Ready")
        self.status_label.config(fg=AppStyles.ACCENT_GREEN)
        logger.info("Processing finished")


def main():
    """Main entry point"""
    try:
        root = tk.Tk()
        app = VideoAutomationGUI(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Application failed to start: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start:\n{str(e)}")


if __name__ == "__main__":
    main()
