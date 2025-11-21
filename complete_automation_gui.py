"""
Video Automation Studio - Modern Professional Interface
Beautiful gradient-based design with premium styling
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

# Setup logging with UTF-8 encoding to handle Unicode filenames
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure StreamHandler to use UTF-8 encoding
import sys
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stderr:
        handler.stream = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

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
    """Modern Professional Dark Theme - Easy on Eyes"""
    # Background - Dark theme
    BG_DARK = '#0d1117'           # Deep dark (GitHub dark)
    BG_GRADIENT_START = '#1a1f2e' # Dark blue-gray
    BG_GRADIENT_END = '#2d1b3d'   # Dark purple
    BG_CARD = '#161b22'           # Dark card background
    BG_CARD_HOVER = '#1f2937'     # Subtle hover (slightly lighter)
    BG_INPUT = '#0d1117'          # Dark input background

    # Modern accent colors - Vibrant and professional
    ACCENT_PRIMARY = '#58a6ff'    # Bright blue
    ACCENT_SUCCESS = '#3fb950'    # Bright green
    ACCENT_DANGER = '#f85149'     # Bright red
    ACCENT_WARNING = '#d29922'    # Bright orange
    ACCENT_INFO = '#58a6ff'       # Bright blue

    # Text colors - Dark theme
    TEXT_DARK = '#ffffff'         # White text (reversed)
    TEXT_MEDIUM = '#8b949e'       # Medium gray
    TEXT_LIGHT = '#6e7681'        # Light gray
    TEXT_WHITE = '#ffffff'        # Pure white

    # Borders
    BORDER_LIGHT = '#30363d'      # Dark border
    BORDER_MEDIUM = '#21262d'     # Darker border


def get_windows_fonts():
    """Scan Windows fonts folder and return available font families including Urdu fonts"""
    try:
        font_files = {}

        # Check multiple font locations
        font_locations = [
            Path(r"C:\Windows\Fonts"),  # Windows system fonts
            Path.home() / "AppData/Local/Microsoft/Windows/Fonts",  # Windows user fonts
        ]

        # Scan all locations for TTF fonts
        for fonts_folder in font_locations:
            if fonts_folder.exists():
                for font_file in fonts_folder.glob("*.ttf"):
                    try:
                        font_name = font_file.stem
                        font_files[font_name] = str(font_file)
                    except Exception as e:
                        logger.debug(f"Could not load font {font_file}: {e}")
                        continue

        # Add Urdu/Arabic fonts explicitly (user-friendly names)
        urdu_fonts = {
            'Jameel Noori Nastaleeq': 'Jameel Noori Nastaleeq',
            'Jameel Noori Nastaleeq Kasheeda': 'Jameel Noori Nastaleeq Kasheeda',
            'Noto Nastaliq Urdu': 'Noto Nastaliq Urdu',
            'Noto Nastaliq Urdu Bold': 'Noto Nastaliq Urdu Bold',
            'Noto Naskh Arabic': 'Noto Naskh Arabic',
        }

        # Add Urdu fonts to the list
        for font_name in urdu_fonts:
            font_files[font_name] = font_name

        # Add common default fonts
        common_fonts = ['Arial', 'Arial Bold', 'Impact', 'Verdana', 'Times New Roman', 'Segoe UI']
        for font in common_fonts:
            if font not in font_files:
                font_files[font] = font

        return sorted(font_files.keys()) if font_files else ['Arial', 'Impact', 'Verdana']

    except Exception as e:
        logger.error(f"Error getting fonts: {e}")
        return ['Arial', 'Impact', 'Verdana', 'Jameel Noori Nastaleeq']


class ModernButton(tk.Button):
    """Custom modern button with hover effects"""
    def __init__(self, parent, **kwargs):
        # Extract custom parameters
        bg_color = kwargs.pop('bg_color', AppStyles.ACCENT_PRIMARY)
        hover_color = kwargs.pop('hover_color', AppStyles.ACCENT_INFO)

        # Set default button styling
        kwargs.setdefault('relief', 'flat')
        kwargs.setdefault('cursor', 'hand2')
        kwargs.setdefault('bg', bg_color)
        kwargs.setdefault('fg', AppStyles.TEXT_WHITE)
        kwargs.setdefault('font', ('Segoe UI', 10, 'bold'))
        kwargs.setdefault('padx', 25)
        kwargs.setdefault('pady', 12)
        kwargs.setdefault('borderwidth', 0)

        super().__init__(parent, **kwargs)

        self.default_bg = bg_color
        self.hover_bg = hover_color

        # Bind hover events
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        self['background'] = self.hover_bg

    def on_leave(self, e):
        self['background'] = self.default_bg


class VideoAutomationGUI:
    """Main modern GUI application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Video Automation Studio - Professional Edition")
        self.root.geometry("1280x900")  # Larger default size
        self.root.configure(bg=AppStyles.BG_CARD)
        self.root.resizable(True, True)
        self.root.minsize(1100, 800)  # Increased minimum size

        # Make window expand with content
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

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
            # Save caption layout and position if they exist
            if hasattr(self, 'caption_layout_var'):
                self.settings['caption_layout'] = self.caption_layout_var.get()
            if hasattr(self, 'caption_position_var'):
                self.settings['caption_position'] = self.caption_position_var.get()
            if hasattr(self, 'caption_preset_var'):
                self.settings['caption_preset'] = self.caption_preset_var.get()

            # Save emoji theme
            if hasattr(self, 'emoji_preset_var'):
                display_value = self.emoji_preset_var.get()
                if hasattr(self, 'emoji_preset_map') and display_value in self.emoji_preset_map:
                    self.settings['emoji_preset_category'] = self.emoji_preset_map[display_value]

            # Save caption font styles
            if hasattr(self, 'caption_font_var'):
                self.settings['caption_font_style'] = self.caption_font_var.get()
            if hasattr(self, 'caption_highlight_font_var'):
                self.settings['caption_highlight_font_style'] = self.caption_highlight_font_var.get()

            # Save audio paths
            if hasattr(self, 'bgm_file_var'):
                self.settings['bgm_file'] = self.bgm_file_var.get()
            if hasattr(self, 'vo_path_var'):
                self.settings['voiceover_folder'] = self.vo_path_var.get()
            if hasattr(self, 'voiceover_text_var'):
                self.settings['voiceover_text_file'] = self.voiceover_text_var.get()

            # Save TTS engine preferences (Cloud vs Local Kokoro)
            if hasattr(self, 'tts_engine_var'):
                self.settings['tts_engine'] = self.tts_engine_var.get()
            if hasattr(self, 'kokoro_voice_var'):
                self.settings['kokoro_voice'] = self.kokoro_voice_var.get()
            if hasattr(self, 'kokoro_quality_var'):
                self.settings['kokoro_quality'] = self.kokoro_quality_var.get()

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
        """Setup the main UI with modern design"""

        # ═══════════════════════════════════════════════════════════
        # MODERN GRADIENT HEADER
        # ═══════════════════════════════════════════════════════════
        header_frame = tk.Frame(self.root, bg=AppStyles.BG_GRADIENT_START, height=80)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)

        # Create gradient effect with multiple frames
        gradient_canvas = tk.Canvas(header_frame, height=80, bg=AppStyles.BG_GRADIENT_START,
                                    highlightthickness=0)
        gradient_canvas.pack(fill='both', expand=True)

        # Draw gradient
        for i in range(80):
            # Interpolate between gradient colors
            ratio = i / 80
            gradient_canvas.create_line(0, i, 1200, i,
                                       fill=self.interpolate_color(
                                           AppStyles.BG_GRADIENT_START,
                                           AppStyles.BG_GRADIENT_END, ratio))

        # Header content on top of gradient
        header_content = tk.Frame(gradient_canvas, bg=AppStyles.BG_GRADIENT_START, height=80)
        gradient_canvas.create_window(0, 0, window=header_content, anchor='nw', width=1200)

        # Left side - Logo and title
        left_header = tk.Frame(header_content, bg=AppStyles.BG_GRADIENT_START)
        left_header.pack(side='left', padx=30, pady=15)

        tk.Label(left_header, text="🎬 Video Automation Studio",
                bg=AppStyles.BG_GRADIENT_START, fg=AppStyles.TEXT_WHITE,
                font=('Segoe UI', 22, 'bold')).pack(anchor='w')

        tk.Label(left_header, text="Create stunning videos with AI-powered automation",
                bg=AppStyles.BG_GRADIENT_START, fg=AppStyles.TEXT_WHITE,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(3,0))

        # Right side - Status
        right_header = tk.Frame(header_content, bg=AppStyles.BG_GRADIENT_START)
        right_header.pack(side='right', padx=30, pady=15)

        status_badge = tk.Frame(right_header, bg=AppStyles.ACCENT_SUCCESS, padx=15, pady=8)
        status_badge.pack()

        self.status_label = tk.Label(status_badge, textvariable=self.status_var,
                                     bg=AppStyles.ACCENT_SUCCESS, fg=AppStyles.TEXT_WHITE,
                                     font=('Segoe UI', 10, 'bold'))
        self.status_label.pack()

        # ═══════════════════════════════════════════════════════════
        # MODERN TAB NOTEBOOK
        # ═══════════════════════════════════════════════════════════

        # Custom style for modern dark tabs
        style = ttk.Style()
        style.theme_create("modern_dark", parent="alt", settings={
            "TNotebook": {
                "configure": {
                    "tabmargins": [2, 5, 2, 0],
                    "background": AppStyles.BG_CARD
                }
            },
            "TNotebook.Tab": {
                "configure": {
                    "padding": [25, 12],
                    "background": AppStyles.BG_INPUT,
                    "foreground": AppStyles.TEXT_MEDIUM,
                    "borderwidth": 0,
                    "font": ('Segoe UI', 10, 'bold')
                },
                "map": {
                    "background": [
                        ("selected", AppStyles.BG_CARD_HOVER),
                        ("active", AppStyles.BG_CARD)
                    ],
                    "foreground": [
                        ("selected", AppStyles.ACCENT_PRIMARY),
                        ("active", AppStyles.TEXT_WHITE)
                    ],
                    "expand": [("selected", [1, 1, 1, 0])]
                }
            }
        })
        style.theme_use("modern_dark")

        # Tab container with shadow effect
        tab_container = tk.Frame(self.root, bg=AppStyles.BG_CARD)
        tab_container.pack(fill='both', expand=True, padx=0, pady=0)

        self.notebook = ttk.Notebook(tab_container)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(10, 0))

        # Create tabs
        self.create_quick_process_tab()
        self.create_text_settings_tab()
        self.create_effects_tab()
        self.create_audio_tab()
        self.create_captions_tab()
        self.create_transitions_tab()

        # ═══════════════════════════════════════════════════════════
        # MODERN PROGRESS BAR & ACTION BUTTONS
        # ═══════════════════════════════════════════════════════════
        bottom_frame = tk.Frame(self.root, bg=AppStyles.BG_CARD, height=120)
        bottom_frame.pack(fill='x', side='bottom', padx=20, pady=20)
        bottom_frame.pack_propagate(False)

        # Progress section with modern design
        progress_container = tk.Frame(bottom_frame, bg=AppStyles.BG_CARD)
        progress_container.pack(fill='x', pady=(0, 15))

        tk.Label(progress_container, text="Processing Progress",
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w')

        # Custom progress bar style for dark theme
        style.configure("Modern.Horizontal.TProgressbar",
                       troughcolor=AppStyles.BG_INPUT,
                       background=AppStyles.ACCENT_SUCCESS,
                       borderwidth=0,
                       thickness=10)

        self.progress_bar = ttk.Progressbar(progress_container,
                                           mode='determinate',
                                           variable=self.progress_var,
                                           style="Modern.Horizontal.TProgressbar")
        self.progress_bar.pack(fill='x', pady=8)

        self.progress_text = tk.Label(progress_container, text="Ready to process",
                                     bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                                     font=('Segoe UI', 9))
        self.progress_text.pack(anchor='w')

        # Modern action buttons
        button_frame = tk.Frame(bottom_frame, bg=AppStyles.BG_CARD)
        button_frame.pack()

        self.btn_process = ModernButton(button_frame, text="▶  Process Videos",
                                       bg_color=AppStyles.ACCENT_SUCCESS,
                                       hover_color='#059669',
                                       command=self.start_processing)
        self.btn_process.pack(side='left', padx=5)

        self.btn_stop = ModernButton(button_frame, text="■  Stop",
                                     bg_color=AppStyles.ACCENT_DANGER,
                                     hover_color='#dc2626',
                                     state='disabled',
                                     command=self.stop_processing)
        self.btn_stop.pack(side='left', padx=5)

        self.btn_save = ModernButton(button_frame, text="💾  Save Settings",
                                     bg_color=AppStyles.ACCENT_INFO,
                                     hover_color='#2563eb',
                                     command=self.save_settings)
        self.btn_save.pack(side='left', padx=5)

    def interpolate_color(self, color1, color2, ratio):
        """Interpolate between two hex colors"""
        c1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        c2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)

        return f'#{r:02x}{g:02x}{b:02x}'

    def create_quick_process_tab(self):
        """Create modern Quick Process tab with horizontal grid layout"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_CARD)
        self.notebook.add(tab, text='⚡ Quick Process')

        # Scrollable content
        canvas = tk.Canvas(tab, bg=AppStyles.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_CARD)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Create horizontal grid container (3 columns for main cards)
        grid_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configure grid columns
        for col in range(3):
            grid_container.columnconfigure(col, weight=1, uniform='main_col')

        # ROW 1: Input Source | Output Settings | Processing Options

        # Input Source Card
        input_card = self.create_grid_card(grid_container, "📁 Input Source", row=0, col=0)
        self.create_path_field(input_card, 'Video Folder:', self.video_folder_var, self.browse_video_folder)
        self.create_path_field(input_card, 'Quotes File:', self.quotes_file_var, self.browse_quotes_file)

        # Output Settings Card
        output_card = self.create_grid_card(grid_container, "📂 Output Settings", row=0, col=1)
        self.create_path_field(output_card, 'Output Folder:', self.output_folder_var, self.browse_output_folder)

        # Processing Options Card
        proc_card = self.create_grid_card(grid_container, "⚙️ Processing Options", row=0, col=2)

        options = [
            ('enable_captions', '📝 Captions'),
            ('use_tts_voiceover', '🔊 TTS Voice'),
            ('add_custom_bgm', '🎵 BGM'),
            ('video_zoom', '🔍 Zoom'),
            ('pulsing_cta', '💓 Pulsing'),
        ]

        for key, label in options:
            var = tk.BooleanVar(value=self.settings.get(key, False))

            chk_frame = tk.Frame(proc_card, bg=AppStyles.BG_CARD)
            chk_frame.pack(fill='x', padx=15, pady=5)

            chk = tk.Checkbutton(chk_frame, text=label,
                                variable=var, bg=AppStyles.BG_CARD,
                                fg=AppStyles.TEXT_DARK,
                                font=('Segoe UI', 9),
                                activebackground=AppStyles.BG_CARD,
                                selectcolor=AppStyles.BG_INPUT,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w')
            setattr(self, f'{key}_var', var)

        # ROW 2: Quick Stats (full width)
        stats_card = self.create_grid_card(grid_container, "📊 Quick Stats", row=1, col=0, colspan=3)

        stats_data = [
            ("Videos Ready", str(self.count_videos()), "🎬"),
            ("Quotes Available", str(self.count_quotes()), "💬"),
            ("Output Path", "✓" if self.output_folder_var.get() else "✗", "📂"),
        ]

        stats_row_frame = tk.Frame(stats_card, bg=AppStyles.BG_CARD)
        stats_row_frame.pack(fill='x', padx=20, pady=10)

        for label, value, icon in stats_data:
            stat_cell = tk.Frame(stats_row_frame, bg=AppStyles.BG_INPUT, padx=20, pady=10)
            stat_cell.pack(side='left', expand=True, fill='both', padx=5)

            tk.Label(stat_cell, text=f"{icon} {label}:",
                    bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                    font=('Segoe UI', 9)).pack(anchor='w')

            tk.Label(stat_cell, text=value,
                    bg=AppStyles.BG_INPUT, fg=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 11, 'bold')).pack(anchor='w')

    def create_text_settings_tab(self):
        """Create Text Settings tab with horizontal grid layout"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_CARD)
        self.notebook.add(tab, text='📝 Text Settings')

        canvas = tk.Canvas(tab, bg=AppStyles.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_CARD)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Create horizontal grid container (3 columns)
        grid_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configure grid columns
        for col in range(3):
            grid_container.columnconfigure(col, weight=1, uniform='text_col')

        # Title, Quote, CTA sections in horizontal grid
        text_sections = [
            ('title', '📌', 'Title Settings', 0),
            ('quote', '💬', 'Quote Settings', 1),
            ('cta', '🎯', 'Call-to-Action', 2)
        ]

        for prefix, icon, title, col in text_sections:
            card = self.create_grid_card(grid_container, f"{icon} {title}", row=0, col=col)
            self.create_text_controls(card, prefix)

    def create_effects_tab(self):
        """Create Visual Effects tab with horizontal grid layout"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_CARD)
        self.notebook.add(tab, text='✨ Visual Effects')

        canvas = tk.Canvas(tab, bg=AppStyles.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_CARD)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Combined effects list for horizontal grid
        all_effects = [
            # Text Effects
            ('text_fade_in', '💫 Fade In'),
            ('text_slide_up', '⬆️ Slide Up'),
            ('text_bounce', '🎾 Bounce'),
            ('text_kinetic', '⚡ Kinetic Typing'),
            ('text_glitch', '📺 Glitch Effect'),
            # Visual Effects
            ('text_glow', '✨ Text Glow'),
            ('vignette', '🌑 Vignette'),
            ('background_dim', '🌙 Background Dim'),
            ('film_grain', '🎞️ Film Grain'),
            ('neon_glow', '💡 Neon Glow'),
            ('drop_shadow', '👤 Drop Shadow'),
            # Particle Effects
            ('add_glitter', '✨ Glitter'),
            ('add_stars', '⭐ Stars'),
            ('add_hearts', '❤️ Hearts'),
            ('add_confetti', '🎉 Confetti'),
        ]

        # Create horizontal grid layout (4 columns)
        self.create_effect_grid(content, "🎨 Visual Effects & Enhancements", all_effects, columns=4)

    def create_audio_tab(self):
        """Create Audio Settings tab with horizontal grid layout"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_CARD)
        self.notebook.add(tab, text='🔊 Audio Settings')

        canvas = tk.Canvas(tab, bg=AppStyles.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_CARD)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Create horizontal grid container (2x2 grid)
        grid_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configure grid columns
        for col in range(2):
            grid_container.columnconfigure(col, weight=1, uniform='audio_col')

        # ROW 0: Original Audio | BGM Settings
        # Original Audio Settings
        original_card = self.create_grid_card(grid_container, "🎧 Original Audio", row=0, col=0)

        mute_var = tk.BooleanVar(value=self.settings.get('mute_original_audio', False))
        tk.Checkbutton(original_card, text='Mute Original Audio',
                      variable=mute_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('mute_original_audio', mute_var.get())).pack(anchor='w', padx=20, pady=10)

        self.create_slider_control(original_card, 'Volume:', 'original_audio_volume', 0.0, 1.0, 0.5, resolution=0.1)

        # BGM Settings
        bgm_card = self.create_grid_card(grid_container, "🎵 Background Music", row=0, col=1)

        bgm_var = tk.BooleanVar(value=self.settings.get('add_custom_bgm', False))
        tk.Checkbutton(bgm_card, text='Add Background Music',
                      variable=bgm_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('add_custom_bgm', bgm_var.get())).pack(anchor='w', padx=20, pady=10)

        # BGM File/Folder selection
        bgm_file_frame = tk.Frame(bgm_card, bg=AppStyles.BG_CARD)
        bgm_file_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(bgm_file_frame, text='BGM File or Folder:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        bgm_input_frame = tk.Frame(bgm_file_frame, bg=AppStyles.BG_CARD)
        bgm_input_frame.pack(fill='x')

        self.bgm_file_var = tk.StringVar(value=self.settings.get('bgm_file', ''))
        bgm_entry = tk.Entry(bgm_input_frame, textvariable=self.bgm_file_var,
                            bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                            font=('Segoe UI', 9), relief='flat', bd=2)
        bgm_entry.pack(side='left', fill='x', expand=True, ipady=6)

        ModernButton(bgm_input_frame, text='📄 File',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.browse_bgm_file).pack(side='left', padx=(5, 2))

        ModernButton(bgm_input_frame, text='📁 Folder',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.browse_bgm_folder).pack(side='left', padx=2)

        # Volume slider
        self.create_slider_control(bgm_card, 'Volume:', 'bgm_volume', 0.0, 1.0, 0.3, resolution=0.1)

        # ROW 1: Voiceover Settings | TTS Settings
        # Voiceover Settings
        vo_card = self.create_grid_card(grid_container, "🎙️ Voiceover", row=1, col=0)

        vo_var = tk.BooleanVar(value=self.settings.get('add_voiceover', False))
        tk.Checkbutton(vo_card, text='Enable Voiceover',
                      variable=vo_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('add_voiceover', vo_var.get())).pack(anchor='w', padx=20, pady=10)

        # Voiceover Folder
        vo_folder_frame = tk.Frame(vo_card, bg=AppStyles.BG_CARD)
        vo_folder_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(vo_folder_frame, text='Voiceover Folder (Files: 1.mp3, 2.mp3...):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        vo_input_frame = tk.Frame(vo_folder_frame, bg=AppStyles.BG_CARD)
        vo_input_frame.pack(fill='x')

        self.vo_path_var = tk.StringVar(value=self.settings.get('voiceover_folder', ''))
        vo_entry = tk.Entry(vo_input_frame, textvariable=self.vo_path_var,
                           bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                           font=('Segoe UI', 9), relief='flat', bd=2)
        vo_entry.pack(side='left', fill='x', expand=True, ipady=6)

        ModernButton(vo_input_frame, text='📁 Browse',
                    bg_color=AppStyles.ACCENT_SUCCESS,
                    font=('Segoe UI', 9, 'bold'),
                    padx=20, pady=6,
                    command=self.browse_voiceover_folder).pack(side='left', padx=(5, 0))

        # TTS Settings
        tts_card = self.create_grid_card(grid_container, "🗣️ TTS Settings", row=1, col=1)

        tts_var = tk.BooleanVar(value=self.settings.get('use_tts_voiceover', True))
        tk.Checkbutton(tts_card, text='Generate Voiceover from Text (TTS)',
                      variable=tts_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('use_tts_voiceover', tts_var.get())).pack(anchor='w', padx=20, pady=10)

        # Info
        info_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        info_frame.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(info_frame, text='ℹ️ Automatically converts quote text to speech using natural AI voices.',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9), justify='left').pack(anchor='w', padx=15, pady=5)

        # TTS Engine Selection
        engine_frame = tk.Frame(tts_card, bg=AppStyles.BG_INPUT, pady=15, padx=20)
        engine_frame.pack(fill='x', padx=15, pady=(5, 15))

        tk.Label(engine_frame, text='🎛️ TTS Engine:',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 10))

        self.tts_engine_var = tk.StringVar(value=self.settings.get('tts_engine', 'cloud'))

        # Cloud TTS option
        cloud_frame = tk.Frame(engine_frame, bg=AppStyles.BG_INPUT)
        cloud_frame.pack(fill='x', pady=5)

        tk.Radiobutton(cloud_frame, text='☁️ Cloud TTS (Edge-TTS)',
                      variable=self.tts_engine_var, value='cloud',
                      bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_INPUT,
                      selectcolor=AppStyles.BG_CARD,
                      font=('Segoe UI', 10, 'bold'),
                      command=self.on_tts_engine_change).pack(anchor='w')

        tk.Label(cloud_frame, text='   • 60+ premium voices (Microsoft Edge TTS)',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)
        tk.Label(cloud_frame, text='   • Requires internet connection',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)
        tk.Label(cloud_frame, text='   • Fast processing, high quality',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)

        # Local TTS option (Kokoro)
        local_frame = tk.Frame(engine_frame, bg=AppStyles.BG_INPUT)
        local_frame.pack(fill='x', pady=(10, 5))

        tk.Radiobutton(local_frame, text='💻 Local TTS (Kokoro - FREE & Offline)',
                      variable=self.tts_engine_var, value='local',
                      bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_INPUT,
                      selectcolor=AppStyles.BG_CARD,
                      font=('Segoe UI', 10, 'bold'),
                      command=self.on_tts_engine_change).pack(anchor='w')

        tk.Label(local_frame, text='   • 100% FREE - No subscriptions, no character limits',
                bg=AppStyles.BG_INPUT, fg=AppStyles.ACCENT_SUCCESS,
                font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=20)
        tk.Label(local_frame, text='   • Works completely offline (no internet needed)',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)
        tk.Label(local_frame, text='   • Studio-quality voices, faster than cloud',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)
        tk.Label(local_frame, text='   • Runs on modest hardware (8GB RAM recommended)',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)

        # Kokoro TTS Settings (shown when Local TTS is selected)
        self.kokoro_settings_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        self.kokoro_settings_frame.pack(fill='x', padx=20, pady=8)

        # Installation status
        kokoro_status_frame = tk.Frame(self.kokoro_settings_frame, bg=AppStyles.BG_INPUT, pady=10, padx=15)
        kokoro_status_frame.pack(fill='x', pady=(0, 10))

        self.kokoro_status_label = tk.Label(kokoro_status_frame, text='⚠️ Kokoro TTS: Not Installed',
                                            bg=AppStyles.BG_INPUT, fg=AppStyles.ACCENT_WARNING,
                                            font=('Segoe UI', 9, 'bold'))
        self.kokoro_status_label.pack(anchor='w')

        tk.Label(kokoro_status_frame, text='Installation Guide: pip install kokoro-onnx',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(3, 0))

        ModernButton(kokoro_status_frame, text='📖 Setup Instructions',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 8, 'bold'),
                    padx=15, pady=4,
                    command=self.show_kokoro_setup).pack(anchor='w', pady=(5, 0))

        # Kokoro Voice Selection
        kokoro_voice_frame = tk.Frame(self.kokoro_settings_frame, bg=AppStyles.BG_CARD)
        kokoro_voice_frame.pack(fill='x', pady=8)

        tk.Label(kokoro_voice_frame, text='Kokoro Voice:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.kokoro_voices = [
            'af - Male 1 (American, Deep)',
            'af_bella - Female 1 (American, Warm)',
            'af_sarah - Female 2 (American, Clear)',
            'am_adam - Male 2 (American, Professional)',
            'am_michael - Male 3 (American, Energetic)',
            'bf_emma - Female 3 (British, Elegant)',
            'bf_isabella - Female 4 (British, Sophisticated)',
            'bm_george - Male 4 (British, Distinguished)',
            'bm_lewis - Male 5 (British, Authoritative)'
        ]

        self.kokoro_voice_var = tk.StringVar(value=self.settings.get('kokoro_voice', self.kokoro_voices[0]))
        kokoro_voice_combo = ttk.Combobox(kokoro_voice_frame, textvariable=self.kokoro_voice_var,
                                          values=self.kokoro_voices, state='readonly',
                                          font=('Segoe UI', 9), width=40)
        kokoro_voice_combo.pack(fill='x', pady=5)
        kokoro_voice_combo.bind('<<ComboboxSelected>>', lambda e: self.update_setting('kokoro_voice', self.kokoro_voice_var.get()))

        # Quality Selection
        kokoro_quality_frame = tk.Frame(self.kokoro_settings_frame, bg=AppStyles.BG_CARD)
        kokoro_quality_frame.pack(fill='x', pady=8)

        tk.Label(kokoro_quality_frame, text='Audio Quality:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.kokoro_quality_var = tk.StringVar(value=self.settings.get('kokoro_quality', 'wav'))

        quality_opts = tk.Frame(kokoro_quality_frame, bg=AppStyles.BG_CARD)
        quality_opts.pack(fill='x')

        tk.Radiobutton(quality_opts, text='🎵 WAV (Studio Quality - Uncompressed)',
                      variable=self.kokoro_quality_var, value='wav',
                      bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      font=('Segoe UI', 9),
                      command=lambda: self.update_setting('kokoro_quality', 'wav')).pack(anchor='w', pady=3)

        tk.Radiobutton(quality_opts, text='🎧 MP3 (Compressed - Smaller file size)',
                      variable=self.kokoro_quality_var, value='mp3',
                      bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      font=('Segoe UI', 9),
                      command=lambda: self.update_setting('kokoro_quality', 'mp3')).pack(anchor='w', pady=3)

        # Cloud TTS Voice Selection (shown when Cloud TTS is selected)
        self.cloud_voice_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        self.cloud_voice_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(self.cloud_voice_frame, text='Cloud TTS Voice:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        # ALL voice keys (60+)
        self.tts_voice_keys = [
            # PREMIUM MOTIVATIONAL VOICES
            'steffan_multi', 'andrew_multi', 'brian_multi', 'ava_multi', 'emma_multi',
            'alloy', 'nova', 'shimmer', 'kai', 'luna', 'jenny_multi', 'ryan_multi',
            # US Female Deep
            'monica', 'nancy', 'ana', 'aria', 'jenny', 'michelle', 'amber', 'ashley', 'sara', 'emma',
            # US Male Deep
            'andrew', 'brian', 'tony', 'jason', 'brandon', 'jacob', 'christopher', 'guy', 'davis', 'eric', 'roger', 'steffan',
            # British
            'thomas', 'mia', 'ryan', 'sonia', 'libby', 'alfie',
            # Australian
            'annette', 'natasha', 'william',
            # Indian English
            'neerja', 'prabhat',
            # URDU VOICES
            'asad', 'uzma', 'salman', 'gul', 'asad_multi', 'uzma_multi', 'faiz', 'parveen'
        ]

        # Voice display names with FULL descriptions (Professional, Deep, Poetic, etc.)
        if TTSGenerator:
            # Use detailed descriptions from TTSGenerator.VOICE_NAMES
            voice_options = []
            for key in self.tts_voice_keys:
                display_name = TTSGenerator.VOICE_NAMES.get(key, key.replace('_', ' ').title())
                voice_options.append(display_name)
        else:
            # Fallback if TTSGenerator not available
            voice_options = [f"{key.replace('_', ' ').title()}" for key in self.tts_voice_keys]

        current_voice = self.settings.get('tts_voice', 'andrew_multi')
        try:
            current_index = self.tts_voice_keys.index(current_voice)
            current_display = voice_options[current_index]
        except (ValueError, IndexError):
            current_display = voice_options[0] if voice_options else "Andrew Multi"

        self.tts_voice_var = tk.StringVar(value=current_display)

        voice_combo = ttk.Combobox(self.cloud_voice_frame, textvariable=self.tts_voice_var,
                                   values=voice_options, state='readonly',
                                   font=('Segoe UI', 9), width=60)
        voice_combo.pack(fill='x', pady=5)
        voice_combo.bind('<<ComboboxSelected>>', self.on_tts_voice_change)

        # Speed slider
        self.create_slider_control(tts_card, 'Speech Speed (WPM):', 'tts_speed', 100, 250, 150)

        # ═══════════════════════════════════════════════════════════
        # VOICE PREVIEW SECTION (NEW!)
        # ═══════════════════════════════════════════════════════════
        preview_card = tk.Frame(tts_card, bg=AppStyles.BG_INPUT, pady=15, padx=20)
        preview_card.pack(fill='x', padx=15, pady=(15, 15))

        tk.Label(preview_card, text='🎧 Voice Preview',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 5))

        tk.Label(preview_card, text='Test how the selected voice sounds with custom text',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 10))

        # Preview text input
        tk.Label(preview_card, text='Test Text (Copy-Paste Enabled):',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(0, 5))

        default_preview_text = "Success comes from taking action every single day. Remember, you are capable of incredible things!"

        # Use Text widget for better copy-paste support
        self.preview_text_widget = tk.Text(preview_card, height=3, wrap='word',
                                           bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                                           font=('Segoe UI', 10), relief='flat', bd=2,
                                           insertbackground=AppStyles.TEXT_DARK)
        self.preview_text_widget.pack(fill='x', pady=(0, 10))
        self.preview_text_widget.insert('1.0', default_preview_text)

        # Preview buttons
        preview_btn_frame = tk.Frame(preview_card, bg=AppStyles.BG_INPUT)
        preview_btn_frame.pack(fill='x', pady=(0, 10))

        ModernButton(preview_btn_frame, text='▶ Play Voice Preview',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 10, 'bold'),
                    padx=25, pady=10,
                    command=self.play_voice_preview).pack(side='left', padx=(0, 10))

        ModernButton(preview_btn_frame, text='⏹ Stop',
                    bg_color=AppStyles.ACCENT_DANGER,
                    font=('Segoe UI', 10, 'bold'),
                    padx=20, pady=10,
                    command=self.stop_voice_preview).pack(side='left')

        # Preview status label
        self.preview_status_label = tk.Label(preview_card, text="",
                                            bg=AppStyles.BG_INPUT,
                                            fg=AppStyles.TEXT_MEDIUM,
                                            font=('Segoe UI', 9, 'italic'))
        self.preview_status_label.pack(anchor='w', pady=(5, 0))

        # Voiceover Text File
        vo_text_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        vo_text_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(vo_text_frame, text='Voiceover Text File (Optional - for longer narration):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 2))

        tk.Label(vo_text_frame, text='ℹ️ Use a separate file for voiceover text. If not selected, Quotes.txt will be used.',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic'), justify='left').pack(anchor='w', pady=(0, 5))

        vo_text_input = tk.Frame(vo_text_frame, bg=AppStyles.BG_CARD)
        vo_text_input.pack(fill='x')

        self.voiceover_text_var = tk.StringVar(value=self.settings.get('voiceover_text_file', ''))
        vo_text_entry = tk.Entry(vo_text_input, textvariable=self.voiceover_text_var,
                                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                font=('Segoe UI', 9), relief='flat', bd=2)
        vo_text_entry.pack(side='left', fill='x', expand=True, ipady=6)

        ModernButton(vo_text_input, text='📄 Browse',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.browse_voiceover_text).pack(side='left', padx=(5, 2))

        ModernButton(vo_text_input, text='✕ Clear',
                    bg_color=AppStyles.ACCENT_DANGER,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=lambda: self.voiceover_text_var.set('')).pack(side='left', padx=2)

        # Initialize frame visibility based on selected engine
        self.on_tts_engine_change()

    def create_captions_tab(self):
        """Create Captions tab with horizontal grid layout"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_CARD)
        self.notebook.add(tab, text='💬 Captions')

        canvas = tk.Canvas(tab, bg=AppStyles.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_CARD)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Create horizontal grid container (3 columns)
        grid_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configure grid columns
        for col in range(3):
            grid_container.columnconfigure(col, weight=1, uniform='caption_col')

        # ROW 0: Enable Captions | Preset | Emoji Theme
        # Enable Captions
        cap_card = self.create_grid_card(grid_container, "💬 Enable Captions", row=0, col=0)

        caption_var = tk.BooleanVar(value=self.settings.get('enable_captions', True))
        tk.Checkbutton(cap_card, text='Enable Word-by-Word Captions',
                      variable=caption_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('enable_captions', caption_var.get())).pack(anchor='w', padx=12, pady=6)

        info_frame = tk.Frame(cap_card, bg=AppStyles.BG_CARD)
        info_frame.pack(fill='x', padx=12, pady=(0, 6))
        tk.Label(info_frame, text='ℹ️ Synced with TTS like TikTok/YouTube',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8), justify='left').pack(anchor='w', padx=10, pady=3)

        # Caption Style Presets
        preset_card = self.create_grid_card(grid_container, "🎨 Presets", row=0, col=1)

        preset_frame = tk.Frame(preset_card, bg=AppStyles.BG_CARD)
        preset_frame.pack(fill='x', padx=12, pady=6)

        tk.Label(preset_frame, text='Style Preset:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 3))

        self.caption_preset_var = tk.StringVar(value=self.settings.get('caption_preset', 'Custom'))
        self.caption_presets = [
            "Custom",
            # VIRAL TRENDING STYLES
            "🚀 MrBeast Style (Yellow/Black Viral)",
            "💰 Alex Hormozi (Bold Red)",
            "👑 Andrew Tate (Aggressive Red/Black)",
            "🎯 Subway Surfers (Bright Colorful)",
            "💪 Fitness Motivation (Orange Energy)",
            "🧠 Psychology Facts (Purple Deep)",
            "💸 Money Mindset (Green Dollar)",
            "🎤 Podcast Clips (Navy Professional)",
            "😂 Meme Style (Comic Sans Fun)",
            "🌟 Instagram Viral (Gradient Pink)",
            "⚡ High Energy Shorts (Yellow Thunder)",
            "🔴 Breaking News Alert (Red Urgent)",
            "💎 Luxury Brand (Gold Elegant)",
            "🌊 Calm & Chill (Blue Peaceful)",
            "🎨 Artistic Creative (Multi-color)",
            # NEW CAPCUT TRENDING STYLES 2025
            "🎪 Carnival Pop (Rainbow Bounce)",
            "🌈 Pride Rainbow (Smooth Transition)",
            "⚡ Neon Thunder (Electric Glow Pulse)",
            "🎯 Target Lock (Red Laser Focus)",
            "💥 Comic Boom (Explosion Style)",
            "🌙 Midnight Dream (Dark Purple Stars)",
            "🔮 Crystal Glow (Translucent Effect)",
            "🎆 Firework Burst (Color Splash)",
            "🌺 Tropical Vibe (Beach Gradient)",
            "⚙️ Tech Glitch (Cyberpunk Style)",
            "🏔️ Ice Cold (Frozen Blue Frost)",
            "🔥 Fire Blaze (Orange Red Flame)",
            "🌸 Cherry Blossom (Soft Pink Japan)",
            "⭐ Star Power (Golden Shine)",
            "🎵 Music Beat (Sound Wave Pulse)",
            # URDU & ARABIC STYLES
            "📖 Urdu Poetry (شاعری - Nastaliq)",
            "🕌 Islamic Quotes (اسلامی - Calligraphy)",
            "🎭 Drama Serial (ڈرامہ - Pakistani Style)",
            # ORIGINAL STYLES
            "🔥 Bold Impact (TikTok Style)",
            "✨ Minimal Clean",
            "💎 Neon Glow",
            "🎬 Cinematic",
            "🎮 Gaming Style",
            "📰 News Anchor",
            "🌅 Vintage Film",
            "🎯 Corporate Pro",
            "🌈 Colorful Pop",
            "🖤 Dark Mode"
        ]

        preset_combo = ttk.Combobox(preset_frame, textvariable=self.caption_preset_var,
                                   values=self.caption_presets, state='readonly',
                                   font=('Segoe UI', 8), width=32)
        preset_combo.pack(fill='x', pady=3)
        preset_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_caption_preset())

        ModernButton(preset_frame, text='Apply Preset',
                    bg_color=AppStyles.ACCENT_WARNING,
                    font=('Segoe UI', 8, 'bold'),
                    padx=15, pady=4,
                    command=self.apply_caption_preset).pack(pady=3)

        # Emoji Theme
        emoji_card = self.create_grid_card(grid_container, "😊 Emoji", row=0, col=2)

        emoji_frame = tk.Frame(emoji_card, bg=AppStyles.BG_CARD)
        emoji_frame.pack(fill='x', padx=12, pady=6)

        tk.Label(emoji_frame, text='Emoji Theme:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 3))

        self.emoji_categories = [
            "🎯 General (Mixed)",
            "💪 Motivational & Inspirational",
            "❤️ Love & Relationships",
            "💔 Heartbreak & Sad",
            "🏆 Success & Achievement",
            "💪 Fitness & Health",
            "💼 Business & Money",
            "🍕 Food & Cooking",
            "✈️ Travel & Adventure",
            "💻 Technology & Gaming",
            "🎉 Party & Celebration",
            "🌿 Nature & Environment",
            "⚠️ Warning & Alert",
            "📚 Educational & Learning",
            "😂 Funny & Comedy",
            "🙏 Spiritual & Mindfulness",
            "👗 Fashion & Beauty",
            "🐶 Animals & Pets"
        ]

        self.emoji_preset_map = {
            "🎯 General (Mixed)": "general",
            "💪 Motivational & Inspirational": "motivational",
            "❤️ Love & Relationships": "love",
            "💔 Heartbreak & Sad": "heartbreak",
            "🏆 Success & Achievement": "success",
            "💪 Fitness & Health": "fitness",
            "💼 Business & Money": "business",
            "🍕 Food & Cooking": "food",
            "✈️ Travel & Adventure": "travel",
            "💻 Technology & Gaming": "tech",
            "🎉 Party & Celebration": "party",
            "🌿 Nature & Environment": "nature",
            "⚠️ Warning & Alert": "warning",
            "📚 Educational & Learning": "educational",
            "😂 Funny & Comedy": "funny",
            "🙏 Spiritual & Mindfulness": "spiritual",
            "👗 Fashion & Beauty": "fashion",
            "🐶 Animals & Pets": "animals"
        }

        saved_key = self.settings.get('emoji_preset_category', 'general')
        emoji_reverse_map = {v: k for k, v in self.emoji_preset_map.items()}
        current_emoji = emoji_reverse_map.get(saved_key, self.emoji_categories[0])

        self.emoji_preset_var = tk.StringVar(value=current_emoji)
        emoji_combo = ttk.Combobox(emoji_frame, textvariable=self.emoji_preset_var,
                                  values=self.emoji_categories, state='readonly',
                                  font=('Segoe UI', 9), width=35)
        emoji_combo.pack(fill='x', pady=5)

        emoji_info = tk.Frame(emoji_card, bg=AppStyles.BG_CARD)
        emoji_info.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(emoji_info, text='ℹ️ Emoji theme determines which emojis appear above captions.',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic'), justify='left').pack(anchor='w', padx=10, pady=5)

        # ROW 1: Global Settings | Regular Captions | CapCut Highlighted
        # Global Settings
        global_card = self.create_grid_card(grid_container, "🌍 Global Settings", row=1, col=0)

        # Caption Layout
        layout_frame = tk.Frame(global_card, bg=AppStyles.BG_CARD)
        layout_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(layout_frame, text='Caption Layout:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        self.caption_layout_var = tk.StringVar(value=self.settings.get('caption_layout', '2-line'))
        layout_opts = tk.Frame(layout_frame, bg=AppStyles.BG_CARD)
        layout_opts.pack(fill='x')

        tk.Radiobutton(layout_opts, text='1-Line (All words on ONE line)',
                      variable=self.caption_layout_var, value='1-line',
                      bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      font=('Segoe UI', 9)).pack(side='left', padx=10)

        tk.Radiobutton(layout_opts, text='2-Lines (Split across 2 lines)',
                      variable=self.caption_layout_var, value='2-line',
                      bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      font=('Segoe UI', 9)).pack(side='left', padx=10)

        # Font size
        self.create_slider_control(global_card, 'Caption Font Size:', 'caption_font_size', 30, 100, 60)

        # Position
        pos_frame = tk.Frame(global_card, bg=AppStyles.BG_CARD)
        pos_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(pos_frame, text='Caption Position:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        self.caption_position_var = tk.StringVar(value=self.settings.get('caption_position', 'bottom'))
        pos_opts = tk.Frame(pos_frame, bg=AppStyles.BG_CARD)
        pos_opts.pack(fill='x')

        for pos in ['top', 'center', 'bottom']:
            tk.Radiobutton(pos_opts, text=pos.capitalize(),
                          variable=self.caption_position_var, value=pos,
                          bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                          activebackground=AppStyles.BG_CARD,
                          selectcolor=AppStyles.BG_INPUT,
                          font=('Segoe UI', 9)).pack(side='left', padx=15)

        # Words per line
        self.create_slider_control(global_card, 'Words Per Caption:', 'caption_words_per_line', 1, 5, 3)

        # Regular Caption Settings
        regular_card = self.create_grid_card(grid_container, "📝 Regular Captions", row=1, col=1)

        # Font style
        font_frame = tk.Frame(regular_card, bg=AppStyles.BG_CARD)
        font_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(font_frame, text='Caption Font Style:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        available_fonts = get_windows_fonts()
        self.caption_font_var = tk.StringVar(value=self.settings.get('caption_font_style', 'arialbd.ttf'))
        font_combo = ttk.Combobox(font_frame, textvariable=self.caption_font_var,
                                 values=available_fonts, state='readonly',
                                 font=('Segoe UI', 9), width=30)
        font_combo.pack(fill='x', pady=5)

        # Text color
        self.create_color_picker(regular_card, 'Caption Text Color:', 'caption_text_color', '#FFFFFF')

        # Background
        bg_enabled_var = tk.BooleanVar(value=self.settings.get('caption_bg_enabled', True))
        tk.Checkbutton(regular_card, text='Enable Caption Background',
                      variable=bg_enabled_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('caption_bg_enabled', bg_enabled_var.get())).pack(anchor='w', padx=20, pady=5)

        self.create_color_picker(regular_card, 'Caption Background Color:', 'caption_bg_color', '#000000')
        self.create_slider_control(regular_card, 'Opacity:', 'caption_bg_opacity', 0, 255, 180)

        # CapCut-Style Highlighting
        capcut_card = self.create_grid_card(grid_container, "✨ CapCut Highlighting", row=1, col=2)

        highlight_var = tk.BooleanVar(value=self.settings.get('caption_highlight_enabled', False))
        tk.Checkbutton(capcut_card, text='✨ Enable Word-by-Word Highlighting (like TikTok/Instagram)',
                      variable=highlight_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('caption_highlight_enabled', highlight_var.get())).pack(anchor='w', padx=20, pady=10)

        # Highlight font
        hl_font_frame = tk.Frame(capcut_card, bg=AppStyles.BG_CARD)
        hl_font_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(hl_font_frame, text='Highlight Font Style:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        highlight_fonts = [
            'Segoe UI Bold', 'Arial Bold', 'Arial', 'Arial Black', 'Impact',
            'Montserrat Bold', 'Bebas Neue', 'Poppins Bold', 'Roboto Bold',
            'Times New Roman Bold', 'Times New Roman', 'Verdana Bold', 'Verdana',
            'Calibri Bold', 'Calibri', 'Comic Sans MS Bold', 'Comic Sans MS',
            'Georgia Bold', 'Georgia', 'Courier New Bold', 'Courier New',
            'Tahoma Bold', 'Tahoma', 'Trebuchet MS Bold', 'Trebuchet MS'
        ]
        self.caption_highlight_font_var = tk.StringVar(value=self.settings.get('caption_highlight_font_style', 'Segoe UI Bold'))
        hl_font_combo = ttk.Combobox(hl_font_frame, textvariable=self.caption_highlight_font_var,
                                    values=highlight_fonts, state='readonly',
                                    font=('Segoe UI', 9), width=30)
        hl_font_combo.pack(fill='x', pady=5)

        # Highlight font size
        self.create_slider_control(capcut_card, 'Highlight Font Size:', 'caption_highlight_font_size', 20, 80, 60)

        # Active/Inactive colors
        self.create_color_picker(capcut_card, 'Active Word:', 'caption_highlight_color', '#FFD700')
        self.create_color_picker(capcut_card, 'Inactive Words:', 'caption_inactive_color', '#FFFFFF')

        # ROW 2: Text Stroke (full width)
        # Stroke/Outline
        stroke_card = self.create_grid_card(grid_container, "🖊️ Text Stroke/Outline", row=2, col=0, colspan=3)

        stroke_var = tk.BooleanVar(value=self.settings.get('caption_stroke_enabled', False))
        tk.Checkbutton(stroke_card, text='Enable Text Stroke/Outline',
                      variable=stroke_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('caption_stroke_enabled', stroke_var.get())).pack(anchor='w', padx=20, pady=10)

        self.create_color_picker(stroke_card, 'Active Word Stroke Color:', 'caption_active_stroke_color', '#000000')
        self.create_color_picker(stroke_card, 'Inactive Words Stroke Color:', 'caption_inactive_stroke_color', '#000000')
        self.create_slider_control(stroke_card, 'Stroke Width:', 'caption_stroke_width', 1, 10, 2)

    def create_transitions_tab(self):
        """Create Transitions tab with horizontal grid layout"""
        tab = tk.Frame(self.notebook, bg=AppStyles.BG_CARD)
        self.notebook.add(tab, text='🎬 Transitions')

        canvas = tk.Canvas(tab, bg=AppStyles.BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=AppStyles.BG_CARD)

        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Combined transitions list for horizontal grid
        all_transitions = [
            ('transition_fade_in', '🌅 Fade In'),
            ('transition_fade_out', '🌅 Fade Out'),
            ('transition_zoom_in', '🔍 Zoom In'),
            ('transition_zoom_out', '🔍 Zoom Out'),
            ('lens_flare_enabled', '✨ Lens Flare'),
            ('light_leak_enabled', '💡 Light Leaks'),
            ('film_burn_enabled', '🔥 Film Burn'),
        ]

        # Create horizontal grid layout (4 columns)
        self.create_effect_grid(content, "🎬 Transitions & Cinematic Effects", all_transitions, columns=4)

    # Helper methods

    def create_modern_card(self, parent, title):
        """Create a modern card with shadow and rounded corners"""
        # Outer frame for shadow effect
        card_outer = tk.Frame(parent, bg=AppStyles.BORDER_LIGHT, pady=2, padx=2)
        card_outer.pack(fill='x', padx=15, pady=10)

        # Inner card
        card = tk.Frame(card_outer, bg=AppStyles.BG_CARD, relief='flat')
        card.pack(fill='both', expand=True)

        # Card header with gradient effect
        header = tk.Frame(card, bg=AppStyles.BG_INPUT, height=45)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=title,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=20, pady=10)

        return card

    def create_grid_card(self, parent, title, row, col, colspan=1):
        """Create a compact card in a grid layout"""
        # Outer frame for shadow effect
        card_outer = tk.Frame(parent, bg=AppStyles.BORDER_LIGHT, pady=1, padx=1)
        card_outer.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky='nsew')

        # Inner card
        card = tk.Frame(card_outer, bg=AppStyles.BG_CARD, relief='flat')
        card.pack(fill='both', expand=True)

        # Compact card header
        header = tk.Frame(card, bg=AppStyles.BG_INPUT, height=32)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text=title,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=12, pady=5)

        return card

    def create_path_field(self, parent, label_text, var, browse_cmd):
        """Create a path field with browse button"""
        field_container = tk.Frame(parent, bg=AppStyles.BG_CARD)
        field_container.pack(fill='x', padx=15, pady=8)

        tk.Label(field_container, text=label_text,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 5))

        path_row = tk.Frame(field_container, bg=AppStyles.BG_CARD)
        path_row.pack(fill='x')

        entry = tk.Entry(path_row, textvariable=var,
                        bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                        font=('Segoe UI', 8), relief='flat', width=20)
        entry.pack(side='left', fill='x', expand=True, padx=(0, 5))

        ModernButton(path_row, text='Browse',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 8, 'bold'),
                    padx=10, pady=4,
                    command=browse_cmd).pack(side='right')

    def create_modern_section(self, parent, title, fields):
        """Create a modern section with input fields"""
        card = self.create_modern_card(parent, title)

        for label_text, var, browse_cmd in fields:
            field_container = tk.Frame(card, bg=AppStyles.BG_CARD)
            field_container.pack(fill='x', padx=20, pady=12)

            tk.Label(field_container, text=label_text,
                    bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                    font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

            input_frame = tk.Frame(field_container, bg=AppStyles.BG_CARD)
            input_frame.pack(fill='x')

            entry = tk.Entry(input_frame, textvariable=var,
                           bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                           font=('Segoe UI', 9), relief='flat', bd=2)
            entry.pack(side='left', fill='x', expand=True, ipady=6)

            btn_text = 'Browse Folder' if 'Folder' in label_text else 'Browse File'
            ModernButton(input_frame, text=btn_text,
                        bg_color=AppStyles.ACCENT_INFO,
                        font=('Segoe UI', 9, 'bold'),
                        padx=20, pady=8,
                        command=browse_cmd).pack(side='left', padx=(5, 0))

        return card

    def create_effect_section(self, parent, title, effects):
        """Create effect section with checkboxes"""
        card = self.create_modern_card(parent, title)

        for key, label in effects:
            var = tk.BooleanVar(value=self.settings.get(key, False))

            chk_frame = tk.Frame(card, bg=AppStyles.BG_CARD)
            chk_frame.pack(fill='x', padx=20, pady=6)

            chk = tk.Checkbutton(chk_frame, text=label,
                                variable=var, bg=AppStyles.BG_CARD,
                                fg=AppStyles.TEXT_DARK,
                                font=('Segoe UI', 10),
                                activebackground=AppStyles.BG_CARD,
                                selectcolor=AppStyles.BG_INPUT,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w')

    def create_effect_grid(self, parent, title, effects, columns=4):
        """Create horizontal grid layout for effects (professional layout)"""
        card = self.create_modern_card(parent, title)

        # Create grid container
        grid_container = tk.Frame(card, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True, padx=20, pady=15)

        # Place effects in grid layout
        for idx, (key, label) in enumerate(effects):
            row = idx // columns
            col = idx % columns

            var = tk.BooleanVar(value=self.settings.get(key, False))

            # Create effect cell with border and padding
            effect_cell = tk.Frame(grid_container, bg=AppStyles.BG_INPUT,
                                   highlightbackground=AppStyles.BORDER_LIGHT,
                                   highlightthickness=1,
                                   padx=15, pady=12)
            effect_cell.grid(row=row, column=col, padx=8, pady=8, sticky='ew')

            chk = tk.Checkbutton(effect_cell, text=label,
                                variable=var, bg=AppStyles.BG_INPUT,
                                fg=AppStyles.TEXT_DARK,
                                font=('Segoe UI', 10, 'bold'),
                                activebackground=AppStyles.BG_INPUT,
                                selectcolor=AppStyles.BG_CARD,
                                command=lambda k=key, v=var: self.update_setting(k, v.get()))
            chk.pack(anchor='w')

        # Configure grid columns to expand equally
        for col in range(columns):
            grid_container.columnconfigure(col, weight=1, uniform='effect_col')

    def create_slider_control(self, parent, label, key, from_, to, default, resolution=1):
        """Create a modern slider control"""
        slider_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        slider_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(slider_frame, text=label,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        var = tk.DoubleVar(value=self.settings.get(key, default))

        value_label = tk.Label(slider_frame, text=str(var.get()),
                              bg=AppStyles.BG_CARD, fg=AppStyles.ACCENT_PRIMARY,
                              font=('Segoe UI', 9, 'bold'), width=6)
        value_label.pack(side='right')

        scale = tk.Scale(slider_frame, from_=from_, to=to, resolution=resolution,
                        orient='horizontal', variable=var,
                        bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                        highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                        showvalue=False,
                        command=lambda v, k=key, vl=value_label: self.on_slider_change(k, v, vl))
        scale.pack(side='left', fill='x', expand=True, padx=10)

    def on_slider_change(self, key, value, value_label):
        """Handle slider value change"""
        val = float(value)
        value_label.config(text=f"{val:.2f}" if val < 10 else str(int(val)))
        self.update_setting(key, val if val < 10 else int(val))

    def create_text_controls(self, parent, prefix):
        """Create text controls for title/quote/cta"""
        # Enable checkbox
        enabled_var = tk.BooleanVar(value=self.settings.get(f'{prefix}_enabled', True))
        tk.Checkbutton(parent, text=f'Enable {prefix.title()}',
                      variable=enabled_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting(f'{prefix}_enabled', enabled_var.get())).pack(anchor='w', padx=20, pady=10)

        # Font Size slider
        self.create_slider_control(parent, 'Font Size:', f'{prefix}_font_size', 10, 100, 30)

        # Text Color picker
        color_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        color_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(color_frame, text='Text Color:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        color_var = tk.StringVar(value=self.settings.get(f'{prefix}_text_color', '#FFFFFF'))

        color_preview = tk.Frame(color_frame, bg=color_var.get(), width=40, height=25,
                                relief='solid', borderwidth=1)
        color_preview.pack(side='right', padx=5)

        tk.Entry(color_frame, textvariable=color_var, width=10,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat').pack(side='right', padx=5)

        ModernButton(color_frame, text='Pick Color',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=lambda p=prefix, v=color_var, cp=color_preview: self.pick_color(p, v, cp)).pack(side='right', padx=5)

    def update_setting(self, key, value):
        """Update a setting value"""
        self.settings[key] = value
        logger.debug(f"Setting updated: {key} = {value}")

    def pick_color(self, prefix, var, preview_frame):
        """Open color picker"""
        color = colorchooser.askcolor(title=f"Choose {prefix} color")
        if color[1]:
            var.set(color[1])
            preview_frame.config(bg=color[1])
            self.update_setting(f'{prefix}_text_color', color[1])

    def create_color_picker(self, parent, label_text, setting_key, default_color):
        """Create a modern color picker control"""
        color_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        color_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(color_frame, text=label_text,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        input_frame = tk.Frame(color_frame, bg=AppStyles.BG_CARD)
        input_frame.pack(fill='x')

        color_var = tk.StringVar(value=self.settings.get(setting_key, default_color))

        # Color preview
        color_preview = tk.Frame(input_frame, bg=color_var.get(), width=40, height=25,
                                relief='solid', borderwidth=1)
        color_preview.pack(side='left', padx=(0, 10))

        # Entry
        tk.Entry(input_frame, textvariable=color_var, width=10,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat').pack(side='left', padx=5)

        # Pick button
        ModernButton(input_frame, text='Choose Color',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=lambda: self.pick_setting_color(setting_key, color_var, color_preview)).pack(side='left', padx=5)

    def pick_setting_color(self, setting_key, var, preview_frame):
        """Open color picker for a setting"""
        color = colorchooser.askcolor(title=f"Choose color for {setting_key}")
        if color[1]:
            var.set(color[1])
            preview_frame.config(bg=color[1])
            self.update_setting(setting_key, color[1])

    def apply_caption_preset(self):
        """Apply selected caption preset"""
        preset = self.caption_preset_var.get()
        logger.info(f"Applying caption preset: {preset}")

        # Preset configurations (simplified versions - user can customize further)
        preset_configs = {
            "🚀 MrBeast Style (Yellow/Black Viral)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FFD700',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000000',
                'caption_bg_opacity': 220,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 3
            },
            "💰 Alex Hormozi (Bold Red)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF0000',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000000',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 4
            },
            "👑 Andrew Tate (Aggressive Red/Black)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#DC143C',
                'caption_inactive_color': '#808080',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000000',
                'caption_bg_opacity': 230,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 4
            },
            "🎯 Subway Surfers (Bright Colorful)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#00FF00',
                'caption_inactive_color': '#FFFF00',
                'caption_bg_enabled': True,
                'caption_bg_color': '#FF00FF',
                'caption_bg_opacity': 180,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#0000FF',
                'caption_stroke_width': 2
            },
            "💪 Fitness Motivation (Orange Energy)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF8800',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000000',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 3
            },
            "🧠 Psychology Facts (Purple Deep)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#9370DB',
                'caption_inactive_color': '#E6E6FA',
                'caption_bg_enabled': True,
                'caption_bg_color': '#1a1a2e',
                'caption_bg_opacity': 210,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 2
            },
            # NEW CAPCUT TRENDING STYLES 2025
            "🎪 Carnival Pop (Rainbow Bounce)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF1493',
                'caption_inactive_color': '#FFD700',
                'caption_bg_enabled': True,
                'caption_bg_color': '#FF69B4',
                'caption_bg_opacity': 180,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFD700',
                'caption_stroke_width': 3
            },
            "🌈 Pride Rainbow (Smooth Transition)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF0080',
                'caption_inactive_color': '#00D4FF',
                'caption_bg_enabled': False,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFD700',
                'caption_stroke_width': 4
            },
            "⚡ Neon Thunder (Electric Glow Pulse)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#00FFFF',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000033',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FF00FF',
                'caption_stroke_width': 3
            },
            "🎯 Target Lock (Red Laser Focus)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF0000',
                'caption_inactive_color': '#666666',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000000',
                'caption_bg_opacity': 240,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFFF00',
                'caption_stroke_width': 2
            },
            "💥 Comic Boom (Explosion Style)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FFFF00',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#FF4500',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 5
            },
            "🌙 Midnight Dream (Dark Purple Stars)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#9370DB',
                'caption_inactive_color': '#C8A2C8',
                'caption_bg_enabled': True,
                'caption_bg_color': '#191970',
                'caption_bg_opacity': 220,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFD700',
                'caption_stroke_width': 2
            },
            "🔮 Crystal Glow (Translucent Effect)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#E0FFFF',
                'caption_inactive_color': '#B0E0E6',
                'caption_bg_enabled': True,
                'caption_bg_color': '#483D8B',
                'caption_bg_opacity': 150,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFFFFF',
                'caption_stroke_width': 2
            },
            "🎆 Firework Burst (Color Splash)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FFD700',
                'caption_inactive_color': '#FF69B4',
                'caption_bg_enabled': False,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FF4500',
                'caption_stroke_width': 4
            },
            "🌺 Tropical Vibe (Beach Gradient)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF6347',
                'caption_inactive_color': '#20B2AA',
                'caption_bg_enabled': True,
                'caption_bg_color': '#FFE4B5',
                'caption_bg_opacity': 180,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FF1493',
                'caption_stroke_width': 2
            },
            "⚙️ Tech Glitch (Cyberpunk Style)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#00FFFF',
                'caption_inactive_color': '#FF00FF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000000',
                'caption_bg_opacity': 230,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#00FF00',
                'caption_stroke_width': 2
            },
            "🏔️ Ice Cold (Frozen Blue Frost)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#00CED1',
                'caption_inactive_color': '#E0FFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#000080',
                'caption_bg_opacity': 190,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFFFFF',
                'caption_stroke_width': 3
            },
            "🔥 Fire Blaze (Orange Red Flame)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF4500',
                'caption_inactive_color': '#FFD700',
                'caption_bg_enabled': True,
                'caption_bg_color': '#8B0000',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#000000',
                'caption_stroke_width': 3
            },
            "🌸 Cherry Blossom (Soft Pink Japan)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FFB7C5',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#FFC0CB',
                'caption_bg_opacity': 170,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FF1493',
                'caption_stroke_width': 2
            },
            "⭐ Star Power (Golden Shine)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FFD700',
                'caption_inactive_color': '#FFA500',
                'caption_bg_enabled': True,
                'caption_bg_color': '#4B0082',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFFFFF',
                'caption_stroke_width': 3
            },
            "🎵 Music Beat (Sound Wave Pulse)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#00FF00',
                'caption_inactive_color': '#ADFF2F',
                'caption_bg_enabled': True,
                'caption_bg_color': '#1C1C1C',
                'caption_bg_opacity': 210,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#00FFFF',
                'caption_stroke_width': 2
            },
            # URDU & ARABIC STYLES
            "📖 Urdu Poetry (شاعری - Nastaliq)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#8B4513',
                'caption_inactive_color': '#F5DEB3',
                'caption_bg_enabled': True,
                'caption_bg_color': '#2F4F4F',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFD700',
                'caption_stroke_width': 2,
                'caption_font_style': 'Jameel Noori Nastaleeq',  # Urdu font
                'text_direction': 'rtl'  # Right-to-left
            },
            "🕌 Islamic Quotes (اسلامی - Calligraphy)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#228B22',
                'caption_inactive_color': '#F0E68C',
                'caption_bg_enabled': True,
                'caption_bg_color': '#006400',
                'caption_bg_opacity': 210,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFD700',
                'caption_stroke_width': 3,
                'caption_font_style': 'Jameel Noori Nastaleeq',
                'text_direction': 'rtl'
            },
            "🎭 Drama Serial (ڈرامہ - Pakistani Style)": {
                'caption_highlight_enabled': True,
                'caption_highlight_color': '#FF1493',
                'caption_inactive_color': '#FFFFFF',
                'caption_bg_enabled': True,
                'caption_bg_color': '#800020',
                'caption_bg_opacity': 200,
                'caption_stroke_enabled': True,
                'caption_active_stroke_color': '#FFD700',
                'caption_stroke_width': 2,
                'caption_font_style': 'Jameel Noori Nastaleeq',
                'text_direction': 'rtl'
            }
        }

        if preset in preset_configs:
            config = preset_configs[preset]
            for key, value in config.items():
                self.update_setting(key, value)
            messagebox.showinfo("Preset Applied", f"Applied preset: {preset}\n\nYou can further customize the settings below.")
            logger.info(f"Preset {preset} applied successfully")
        elif preset != "Custom":
            # For presets without full config, just notify
            messagebox.showinfo("Preset Selected", f"Selected: {preset}\n\nConfigure the caption settings below to match this style.")
            logger.info(f"Preset {preset} selected (no auto-config available)")

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

    def browse_bgm_file(self):
        """Browse for BGM file"""
        file = filedialog.askopenfilename(title="Select Background Music",
                                         filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.m4a *.aac"), ("All Files", "*.*")])
        if file:
            self.bgm_file_var.set(file)
            self.update_setting('bgm_file', file)
            logger.info(f"BGM file selected: {file}")

    def browse_bgm_folder(self):
        """Browse for BGM folder"""
        folder = filedialog.askdirectory(title="Select BGM Folder")
        if folder:
            self.bgm_file_var.set(folder)
            self.update_setting('bgm_file', folder)
            logger.info(f"BGM folder selected: {folder}")

    def browse_voiceover_folder(self):
        """Browse for voiceover folder"""
        folder = filedialog.askdirectory(title="Select Voiceover Folder")
        if folder:
            self.vo_path_var.set(folder)
            self.update_setting('voiceover_folder', folder)
            logger.info(f"Voiceover folder selected: {folder}")

    def browse_voiceover_text(self):
        """Browse for voiceover text file"""
        file = filedialog.askopenfilename(title="Select Voiceover Text File",
                                         filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file:
            self.voiceover_text_var.set(file)
            self.update_setting('voiceover_text_file', file)
            logger.info(f"Voiceover text file selected: {file}")

    def play_voice_preview(self):
        """Generate and play voice preview"""
        import tempfile
        import subprocess
        import platform

        # Get selected voice key
        display_name = self.tts_voice_var.get()
        voice_key = 'aria'  # Default

        if TTSGenerator:
            voice_options = [TTSGenerator.VOICE_NAMES.get(k, k) for k in self.tts_voice_keys]
            try:
                voice_index = voice_options.index(display_name)
                voice_key = self.tts_voice_keys[voice_index]
            except (ValueError, IndexError):
                voice_key = 'aria'

        # Get test text from Text widget
        test_text = self.preview_text_widget.get('1.0', 'end-1c').strip()
        if not test_text:
            self.preview_status_label.config(text="⚠ Please enter test text")
            return

        # Get speed
        speed = self.settings.get('tts_speed', 150)

        # Update status
        self.preview_status_label.config(text="🔄 Generating preview audio...")
        self.root.update()

        # Generate audio in background thread
        def generate_and_play():
            try:
                # Check if edge-tts is available
                try:
                    import edge_tts
                    import asyncio
                except ImportError:
                    self.preview_status_label.config(text="❌ edge-tts not installed. Run: pip install edge-tts")
                    return

                # Get voice mapping
                if TTSGenerator:
                    voice_id = TTSGenerator.VOICES.get(voice_key, 'en-US-AriaNeural')
                else:
                    voice_id = 'en-US-AriaNeural'

                # Create temp file
                temp_dir = tempfile.gettempdir()
                preview_file = Path(temp_dir) / f"tts_preview_{voice_key}.mp3"

                # Generate audio using edge-tts
                async def generate_audio():
                    # Calculate rate from speed (150 WPM = +0%)
                    rate_percent = int((speed - 150) / 150 * 100)
                    rate = f"{rate_percent:+d}%"

                    communicate = edge_tts.Communicate(test_text, voice_id, rate=rate)
                    await communicate.save(str(preview_file))

                # Run async generation
                asyncio.run(generate_audio())

                # Update status
                voice_display = TTSGenerator.VOICE_NAMES.get(voice_key, voice_key) if TTSGenerator else voice_key
                self.preview_status_label.config(text=f"▶ Playing: {voice_display}")

                # Play audio based on platform
                system = platform.system()
                if system == 'Windows':
                    subprocess.run(['start', '', str(preview_file)], shell=True, check=False)
                elif system == 'Darwin':  # macOS
                    subprocess.run(['afplay', str(preview_file)], check=False)
                else:  # Linux
                    subprocess.run(['xdg-open', str(preview_file)], check=False)

                # Update status after delay
                self.root.after(2000, lambda: self.preview_status_label.config(
                    text=f"✅ Preview played. Audio saved to: {preview_file}"))

            except Exception as e:
                self.preview_status_label.config(text=f"❌ Error: {str(e)}")
                logger.error(f"Voice preview error: {e}")

        # Run in background thread
        thread = threading.Thread(target=generate_and_play, daemon=True)
        thread.start()

    def stop_voice_preview(self):
        """Stop any playing preview audio"""
        import subprocess
        import platform

        try:
            # On Windows, kill media player processes
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/F', '/IM', 'wmplayer.exe'],
                             capture_output=True, check=False)
                subprocess.run(['taskkill', '/F', '/IM', 'Microsoft.Media.Player.exe'],
                             capture_output=True, check=False)

            self.preview_status_label.config(text="⏹ Playback stopped")
        except Exception as e:
            self.preview_status_label.config(text=f"⚠ Stop failed: {str(e)}")
            logger.error(f"Stop preview error: {e}")

    def on_tts_voice_change(self, event=None):
        """Handle TTS voice selection change"""
        display_name = self.tts_voice_var.get()
        voice_options = [f"{key.replace('_', ' ').title()}" for key in self.tts_voice_keys]
        try:
            voice_index = voice_options.index(display_name)
            voice_key = self.tts_voice_keys[voice_index]
            self.update_setting('tts_voice', voice_key)
            logger.info(f"TTS voice changed to: {voice_key}")
        except (ValueError, IndexError):
            logger.warning(f"Could not find voice key for: {display_name}")

    def on_tts_engine_change(self):
        """Handle TTS engine selection change (Cloud vs Local)"""
        engine = self.tts_engine_var.get()
        self.update_setting('tts_engine', engine)
        logger.info(f"TTS engine changed to: {engine}")

        # Toggle visibility of Cloud vs Kokoro settings
        if engine == 'cloud':
            self.cloud_voice_frame.pack(fill='x', padx=20, pady=8)
            self.kokoro_settings_frame.pack_forget()
        else:  # local (Kokoro)
            self.cloud_voice_frame.pack_forget()
            self.kokoro_settings_frame.pack(fill='x', padx=20, pady=8)
            # Check Kokoro installation
            self.check_kokoro_installation()

    def check_kokoro_installation(self):
        """Check if Kokoro TTS is installed"""
        try:
            import importlib.util
            spec = importlib.util.find_spec("kokoro_onnx")
            if spec is not None:
                self.kokoro_status_label.config(
                    text='✅ Kokoro TTS: Installed & Ready',
                    fg=AppStyles.ACCENT_SUCCESS
                )
                logger.info("Kokoro TTS is installed")
                return True
            else:
                self.kokoro_status_label.config(
                    text='⚠️ Kokoro TTS: Not Installed',
                    fg=AppStyles.ACCENT_WARNING
                )
                logger.warning("Kokoro TTS is not installed")
                return False
        except Exception as e:
            self.kokoro_status_label.config(
                text='❌ Kokoro TTS: Error Checking Installation',
                fg=AppStyles.ACCENT_DANGER
            )
            logger.error(f"Error checking Kokoro installation: {e}")
            return False

    def show_kokoro_setup(self):
        """Show Kokoro TTS setup instructions"""
        setup_text = """
🎙️ KOKORO TTS - FREE LOCAL TEXT-TO-SPEECH SETUP GUIDE

📦 INSTALLATION:

1. Install Kokoro TTS package:
   pip install kokoro-onnx

2. Download voice models (first use):
   The models will auto-download on first use (~100-200MB each)

   Available voices:
   - af (Male 1 - American, Deep)
   - af_bella (Female 1 - American, Warm)
   - af_sarah (Female 2 - American, Clear)
   - am_adam (Male 2 - American, Professional)
   - am_michael (Male 3 - American, Energetic)
   - bf_emma (Female 3 - British, Elegant)
   - bf_isabella (Female 4 - British, Sophisticated)
   - bm_george (Male 4 - British, Distinguished)
   - bm_lewis (Male 5 - British, Authoritative)

✨ BENEFITS:
• 100% FREE - No subscriptions, no API costs, no character limits
• Works OFFLINE - No internet connection required after installation
• Studio Quality - WAV output with professional sound
• FAST - Faster than cloud TTS services
• Privacy - All processing happens on YOUR computer
• Unlimited - Generate as many voiceovers as you want

💻 SYSTEM REQUIREMENTS:
• 8GB RAM recommended (4GB minimum)
• Works on Windows, Mac, Linux
• Python 3.8+ required
• ~500MB disk space for models

🚀 FIRST TIME USE:
1. Select "Local TTS (Kokoro)" option
2. Choose your preferred voice
3. Select quality (WAV for best, MP3 for smaller files)
4. Click "Process Videos" - models will auto-download
5. Enjoy FREE unlimited voiceovers!

📚 More Info: https://github.com/thewh1teagle/kokoro-onnx

Need help? Check the logs or open an issue on GitHub!
"""

        # Create a popup window with scrollable text
        popup = tk.Toplevel(self.root)
        popup.title("Kokoro TTS Setup Guide")
        popup.geometry("700x600")
        popup.configure(bg=AppStyles.BG_CARD)

        # Header
        header = tk.Frame(popup, bg=AppStyles.BG_GRADIENT_START, height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text="🎙️ Kokoro TTS - Setup Guide",
                bg=AppStyles.BG_GRADIENT_START, fg=AppStyles.TEXT_WHITE,
                font=('Segoe UI', 16, 'bold')).pack(pady=15)

        # Scrollable text area
        text_frame = tk.Frame(popup, bg=AppStyles.BG_CARD)
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)

        text_widget = scrolledtext.ScrolledText(text_frame,
                                               wrap=tk.WORD,
                                               bg=AppStyles.BG_INPUT,
                                               fg=AppStyles.TEXT_DARK,
                                               font=('Consolas', 9),
                                               padx=15, pady=15)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', setup_text)
        text_widget.config(state='disabled')

        # Close button
        ModernButton(popup, text='Close',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    command=popup.destroy).pack(pady=10)

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
        self.status_label.config(bg=AppStyles.ACCENT_WARNING)

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
        self.status_label.config(bg=AppStyles.ACCENT_SUCCESS)
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
