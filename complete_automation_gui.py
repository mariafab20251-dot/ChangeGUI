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

# Import NeuTTS helper for voice cloning
try:
    from neutts_helper import NeuTTSHelper, AsyncNeuTTSHelper
except ImportError:
    NeuTTSHelper = None
    AsyncNeuTTSHelper = None
    logger.warning("Could not import NeuTTSHelper - voice cloning will not be available")

# Import Automation Dashboard
try:
    from automation_dashboard import AutomationDashboard
except ImportError:
    AutomationDashboard = None
    logger.warning("Could not import AutomationDashboard - AI automation features will not be available")


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

        # Enable copy-paste keyboard shortcuts for all text widgets
        self.setup_copy_paste_bindings()

        self.setup_ui()
        logger.info("Application started successfully")

    def setup_copy_paste_bindings(self):
        """Setup global copy-paste keyboard shortcuts for all text widgets"""
        # Bind Ctrl+A to select all for Text widgets
        def select_all(event):
            widget = event.widget
            if isinstance(widget, tk.Text):
                widget.tag_add('sel', '1.0', 'end')
                return 'break'
            elif isinstance(widget, tk.Entry):
                widget.select_range(0, tk.END)
                return 'break'
            return None

        # Bind Ctrl+C for copy
        def copy_text(event):
            widget = event.widget
            try:
                if isinstance(widget, tk.Text):
                    if widget.tag_ranges('sel'):
                        text = widget.get('sel.first', 'sel.last')
                        self.root.clipboard_clear()
                        self.root.clipboard_append(text)
                elif isinstance(widget, tk.Entry):
                    if widget.selection_present():
                        text = widget.selection_get()
                        self.root.clipboard_clear()
                        self.root.clipboard_append(text)
            except:
                pass
            return 'break'

        # Bind Ctrl+V for paste
        def paste_text(event):
            widget = event.widget
            try:
                text = self.root.clipboard_get()
                if isinstance(widget, tk.Text):
                    if widget.tag_ranges('sel'):
                        widget.delete('sel.first', 'sel.last')
                    widget.insert('insert', text)
                elif isinstance(widget, tk.Entry):
                    if widget.selection_present():
                        widget.delete('sel.first', 'sel.last')
                    widget.insert('insert', text)
            except:
                pass
            return 'break'

        # Bind Ctrl+X for cut
        def cut_text(event):
            widget = event.widget
            try:
                if isinstance(widget, tk.Text):
                    if widget.tag_ranges('sel'):
                        text = widget.get('sel.first', 'sel.last')
                        self.root.clipboard_clear()
                        self.root.clipboard_append(text)
                        widget.delete('sel.first', 'sel.last')
                elif isinstance(widget, tk.Entry):
                    if widget.selection_present():
                        text = widget.selection_get()
                        self.root.clipboard_clear()
                        self.root.clipboard_append(text)
                        widget.delete('sel.first', 'sel.last')
            except:
                pass
            return 'break'

        # Apply bindings globally
        self.root.bind_class('Text', '<Control-a>', select_all)
        self.root.bind_class('Text', '<Control-A>', select_all)
        self.root.bind_class('Text', '<Control-c>', copy_text)
        self.root.bind_class('Text', '<Control-C>', copy_text)
        self.root.bind_class('Text', '<Control-v>', paste_text)
        self.root.bind_class('Text', '<Control-V>', paste_text)
        self.root.bind_class('Text', '<Control-x>', cut_text)
        self.root.bind_class('Text', '<Control-X>', cut_text)

        # Entry widgets usually work by default, but add explicit bindings
        self.root.bind_class('Entry', '<Control-a>', select_all)
        self.root.bind_class('Entry', '<Control-A>', select_all)

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
            if hasattr(self, 'caption_animation_var'):
                self.settings['caption_word_animation'] = self.caption_animation_var.get()
            if hasattr(self, 'gradient_type_var'):
                self.settings['gradient_type'] = self.gradient_type_var.get()

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

    def open_automation_dashboard(self):
        """Open the AI Automation Dashboard window"""
        if AutomationDashboard:
            try:
                dashboard = AutomationDashboard(parent=self.root)
                logger.info("Opened AI Automation Dashboard")
            except Exception as e:
                logger.error(f"Error opening dashboard: {e}")
                messagebox.showerror("Error", f"Failed to open AI Automation Dashboard: {str(e)}")
        else:
            messagebox.showwarning("Not Available",
                                   "AI Automation Dashboard is not available.\n"
                                   "Please check that automation_dashboard.py is present.")

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

        # Right side - Automation Button and Status
        right_header = tk.Frame(header_content, bg=AppStyles.BG_GRADIENT_START)
        right_header.pack(side='right', padx=30, pady=15)

        # AI Automation Dashboard Button
        if AutomationDashboard:
            automation_btn = tk.Button(right_header, text="🤖 AI Automation",
                                       bg=AppStyles.ACCENT_PRIMARY, fg=AppStyles.TEXT_WHITE,
                                       font=('Segoe UI', 10, 'bold'),
                                       relief='flat', cursor='hand2',
                                       padx=15, pady=8,
                                       command=self.open_automation_dashboard)
            automation_btn.pack(side='left', padx=(0, 15))

            # Hover effects
            automation_btn.bind('<Enter>', lambda e: automation_btn.config(bg=AppStyles.ACCENT_INFO))
            automation_btn.bind('<Leave>', lambda e: automation_btn.config(bg=AppStyles.ACCENT_PRIMARY))

        status_badge = tk.Frame(right_header, bg=AppStyles.ACCENT_SUCCESS, padx=15, pady=8)
        status_badge.pack(side='left')

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

        # Enable mouse wheel scrolling
        self.setup_mousewheel_scroll(canvas, content)

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

        # ROW 3: Template Manager (full width)
        template_card = self.create_grid_card(grid_container, "💾 Templates (Save/Load Effect Combinations)", row=2, col=0, colspan=3)

        template_frame = tk.Frame(template_card, bg=AppStyles.BG_CARD)
        template_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(template_frame, text='ℹ️ Save your favorite effect combinations as templates for quick reuse',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(0, 10))

        # Template selection and buttons
        template_controls = tk.Frame(template_frame, bg=AppStyles.BG_CARD)
        template_controls.pack(fill='x', pady=(0, 10))

        tk.Label(template_controls, text='Template:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 10))

        self.template_var = tk.StringVar(value="")
        self.template_dropdown = ttk.Combobox(template_controls, textvariable=self.template_var,
                                             state='readonly', width=25)
        self.template_dropdown.pack(side='left', padx=(0, 10))

        ModernButton(template_controls, text='📥 Load',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.load_template).pack(side='left', padx=2)

        ModernButton(template_controls, text='💾 Save As...',
                    bg_color=AppStyles.ACCENT_SUCCESS,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.save_template).pack(side='left', padx=2)

        ModernButton(template_controls, text='🗑️ Delete',
                    bg_color=AppStyles.ACCENT_DANGER,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.delete_template).pack(side='left', padx=2)

        # Refresh template list on startup
        self.refresh_template_list()

        # ROW 4: Platform Presets (full width)
        platform_card = self.create_grid_card(grid_container, "📱 Platform Presets", row=3, col=0, colspan=3)

        preset_frame = tk.Frame(platform_card, bg=AppStyles.BG_CARD)
        preset_frame.pack(fill='x', padx=20, pady=10)

        # Enable checkbox
        platform_var = tk.BooleanVar(value=self.settings.get('enable_platform_preset', False))
        tk.Checkbutton(preset_frame, text='Enable Platform Formatting',
                      variable=platform_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('enable_platform_preset', platform_var.get())).pack(anchor='w', pady=(0, 10))

        # Platform selection buttons (horizontal)
        platforms_row = tk.Frame(preset_frame, bg=AppStyles.BG_CARD)
        platforms_row.pack(fill='x', pady=(0, 10))

        tk.Label(platforms_row, text='Select Platform:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 15))

        platforms = [
            ('📱 Instagram Reels', 'instagram_reels', '9:16 (1080x1920)'),
            ('🎵 TikTok', 'tiktok', '9:16 (1080x1920)'),
            ('▶️ YouTube Shorts', 'youtube_shorts', '9:16 (1080x1920)'),
            ('🎬 YouTube', 'youtube', '16:9 (1920x1080)'),
            ('👥 Facebook', 'facebook', '1:1 (1080x1080)'),
        ]

        self.platform_preset_var = tk.StringVar(value=self.settings.get('platform_preset', 'none'))

        for label, value, dimensions in platforms:
            btn_frame = tk.Frame(platforms_row, bg=AppStyles.BG_INPUT if self.platform_preset_var.get() == value else AppStyles.BG_CARD,
                                padx=10, pady=6, relief='raised', bd=1)
            btn_frame.pack(side='left', padx=5)

            def select_platform(v=value, d=dimensions, frame=btn_frame):
                self.platform_preset_var.set(v)
                self.update_setting('platform_preset', v)
                # Update visual selection
                for child in platforms_row.winfo_children():
                    if isinstance(child, tk.Frame) and child != platforms_row.winfo_children()[0]:
                        child.config(bg=AppStyles.BG_CARD)
                frame.config(bg=AppStyles.BG_INPUT)

            btn_frame.bind('<Button-1>', lambda e, v=value, d=dimensions, frame=btn_frame: select_platform(v, d, frame))

            label_widget = tk.Label(btn_frame, text=f"{label}\n{dimensions}",
                                   bg=btn_frame['bg'], fg=AppStyles.TEXT_DARK,
                                   font=('Segoe UI', 9), cursor='hand2')
            label_widget.pack()
            label_widget.bind('<Button-1>', lambda e, v=value, d=dimensions, frame=btn_frame: select_platform(v, d, frame))

        # Crop mode selection
        crop_frame = tk.Frame(preset_frame, bg=AppStyles.BG_CARD)
        crop_frame.pack(fill='x', pady=(5, 0))

        tk.Label(crop_frame, text='Crop Mode:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 10))

        self.crop_mode_var = tk.StringVar(value=self.settings.get('crop_mode', 'center'))
        crop_dropdown = ttk.Combobox(crop_frame, textvariable=self.crop_mode_var,
                                     values=['center', 'top', 'bottom', 'smart'],
                                     state='readonly', width=15)
        crop_dropdown.pack(side='left')
        crop_dropdown.bind('<<ComboboxSelected>>',
                          lambda e: self.update_setting('crop_mode', self.crop_mode_var.get()))

        tk.Label(crop_frame, text='(Center: Crop from center | Top/Bottom: Keep that edge | Smart: Auto-detect faces)',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(side='left', padx=(10, 0))

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

        # Enable mouse wheel scrolling
        self.setup_mousewheel_scroll(canvas, content)

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

        # Enable mouse wheel scrolling
        self.setup_mousewheel_scroll(canvas, content)

        # Combined effects list for horizontal grid
        all_effects = [
            # Text Effects
            ('text_fade_in', '💫 Fade In'),
            ('text_slide_up', '⬆️ Slide Up'),
            ('text_bounce', '🎾 Bounce'),
            ('text_kinetic', '⚡ Kinetic Typing'),
            ('text_glitch', '📺 Glitch Effect'),
            # Visual Effects
            ('chromatic_aberration', '🌈 RGB Glitch'),
            ('text_glow', '✨ Text Glow'),
            ('vignette', '🌑 Vignette'),
            ('background_dim', '🌙 Background Dim'),
            ('film_grain', '🎞️ Film Grain'),
            ('gradient_overlay', '🌅 Gradient Overlay'),
            ('neon_glow', '💡 Neon Glow'),
            ('drop_shadow', '👤 Drop Shadow'),
            # Particle Effects
            ('add_glitter', '✨ Glitter'),
            ('add_stars', '⭐ Stars'),
            ('add_hearts', '❤️ Hearts'),
            ('add_confetti', '🎉 Confetti'),
        ]

        # ═══════════════════════════════════════════════════════════
        # 4-COLUMN GRID LAYOUT
        # ═══════════════════════════════════════════════════════════
        grid_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Configure 4 columns
        for col in range(4):
            grid_container.columnconfigure(col, weight=1, uniform='col')

        # Column 0: Checkboxes
        checkbox_card = self.create_grid_card(grid_container, "🎨 Visual Effects & Enhancements", row=0, col=0, rowspan=10)
        self.create_effect_grid(checkbox_card, "", all_effects, columns=1)

        # Column 1: RGB Glitch, Gradient, Particles
        chroma_card = self.create_grid_card(grid_container, "🌈 RGB Glitch", row=0, col=1)

        tk.Label(chroma_card, text='Trendy RGB split effect',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', padx=15, pady=(5, 10))

        dir_frame = tk.Frame(chroma_card, bg=AppStyles.BG_CARD)
        dir_frame.pack(fill='x', padx=15, pady=(0, 5))

        tk.Label(dir_frame, text='Direction:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9)).pack(side='left', padx=(0, 5))

        self.chromatic_direction_var = tk.StringVar(value=self.settings.get('chromatic_direction', 'horizontal'))
        chroma_dir_dropdown = ttk.Combobox(dir_frame, textvariable=self.chromatic_direction_var,
                                          values=['horizontal', 'vertical', 'both'],
                                          state='readonly', width=12)
        chroma_dir_dropdown.pack(side='left')
        chroma_dir_dropdown.bind('<<ComboboxSelected>>',
                                lambda e: self.update_setting('chromatic_direction', self.chromatic_direction_var.get()))

        self.create_slider_control(chroma_card, 'Intensity:', 'chromatic_intensity', 1, 20, 5, value_format=lambda v: f"{int(v)}px")

        # Gradient Overlay Settings (Row 1)
        gradient_card = self.create_grid_card(grid_container, "🌅 Gradient Overlay", row=1, col=1)

        tk.Label(gradient_card, text='Cinematic gradient effects',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', padx=15, pady=(5, 10))

        type_frame = tk.Frame(gradient_card, bg=AppStyles.BG_CARD)
        type_frame.pack(fill='x', padx=15, pady=(0, 5))

        tk.Label(type_frame, text='Direction:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9)).pack(side='left', padx=(0, 5))

        self.gradient_type_var = tk.StringVar(value=self.settings.get('gradient_type', 'top_to_bottom'))
        gradient_dropdown = ttk.Combobox(type_frame, textvariable=self.gradient_type_var,
                                        values=['top_to_bottom', 'bottom_to_top', 'left_to_right', 'right_to_left', 'radial'],
                                        state='readonly', width=14)
        gradient_dropdown.pack(side='left')
        gradient_dropdown.bind('<<ComboboxSelected>>',
                              lambda e: self.update_setting('gradient_type', self.gradient_type_var.get()))

        self.create_slider_control(gradient_card, 'Intensity:', 'gradient_intensity', 0.1, 0.8, 0.3, resolution=0.1)

        # Particle Effects Settings (Row 2)
        particle_card = self.create_grid_card(grid_container, "✨ Particle Effects", row=2, col=1)

        tk.Label(particle_card, text='Magical floating particles',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', padx=15, pady=(5, 10))

        self.create_slider_control(particle_card, 'Glitter:', 'glitter_intensity', 0.1, 1.0, 0.5, resolution=0.1)

        # Text Glow Settings (Row 3)
        glow_card = self.create_grid_card(grid_container, "✨ Text Glow & Neon", row=0, col=2)

        self.create_slider_control(glow_card, 'Glow:', 'glow_intensity', 1, 20, 8)
        self.create_color_picker(glow_card, 'Glow Color:', 'glow_color', '#ffffff')
        self.create_color_picker(glow_card, 'Neon Color:', 'neon_color', '#00ff88')

        # Text Entrance Animations (Row 4)
        entrance_card = self.create_grid_card(grid_container, "💫 Text Animations", row=1, col=2)

        self.create_slider_control(entrance_card, 'Fade:', 'text_fade_duration', 0.1, 2.0, 0.4, resolution=0.1, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(entrance_card, 'Slide:', 'text_slide_distance', 20, 200, 50, value_format=lambda v: f"{int(v)}px")
        self.create_slider_control(entrance_card, 'Bounce:', 'text_bounce_intensity', 1.0, 1.5, 1.15, resolution=0.05)

        # CTA Overlay (Row 5)
        cta_card = self.create_grid_card(grid_container, "💬 CTA Overlay", row=2, col=2)

        cta_var = tk.BooleanVar(value=self.settings.get('cta_overlay_enabled', False))
        tk.Checkbutton(cta_card, text='Enable CTA',
                      variable=cta_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('cta_overlay_enabled', cta_var.get())).pack(anchor='w', padx=15, pady=5)

        text_frame = tk.Frame(cta_card, bg=AppStyles.BG_CARD)
        text_frame.pack(fill='x', padx=15, pady=3)
        tk.Label(text_frame, text='Text:', bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 9)).pack(side='left')
        self.cta_text_var = tk.StringVar(value=self.settings.get('cta_overlay_text', 'Follow for more! 👉'))
        cta_entry = tk.Entry(text_frame, textvariable=self.cta_text_var, bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 8), width=15)
        cta_entry.pack(side='left', padx=5)
        cta_entry.bind('<FocusOut>', lambda e: self.update_setting('cta_overlay_text', self.cta_text_var.get()))

        pos_frame = tk.Frame(cta_card, bg=AppStyles.BG_CARD)
        pos_frame.pack(fill='x', padx=15, pady=3)
        tk.Label(pos_frame, text='Pos:', bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 9)).pack(side='left')
        self.cta_position_var = tk.StringVar(value=self.settings.get('cta_overlay_position', 'bottom-center'))
        cta_pos = ttk.Combobox(pos_frame, textvariable=self.cta_position_var,
                              values=['top-left', 'top-center', 'top-right', 'bottom-left', 'bottom-center', 'bottom-right'],
                              state='readonly', width=12)
        cta_pos.pack(side='left', padx=5)
        cta_pos.bind('<<ComboboxSelected>>', lambda e: self.update_setting('cta_overlay_position', self.cta_position_var.get()))

        anim_frame = tk.Frame(cta_card, bg=AppStyles.BG_CARD)
        anim_frame.pack(fill='x', padx=15, pady=3)
        tk.Label(anim_frame, text='Anim:', bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 9)).pack(side='left')
        self.cta_animation_var = tk.StringVar(value=self.settings.get('cta_overlay_animation', 'bounce'))
        cta_anim = ttk.Combobox(anim_frame, textvariable=self.cta_animation_var,
                               values=['none', 'bounce', 'pulse', 'slide-in', 'fade-in'],
                               state='readonly', width=10)
        cta_anim.pack(side='left', padx=5)
        cta_anim.bind('<<ComboboxSelected>>', lambda e: self.update_setting('cta_overlay_animation', self.cta_animation_var.get()))

        self.create_slider_control(cta_card, 'Start:', 'cta_overlay_start_time', 0, 10, 3.0, resolution=0.5, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(cta_card, 'Duration:', 'cta_overlay_duration', 1, 10, 3.0, resolution=0.5, value_format=lambda v: f"{v:.1f}s")

        # Progress Bar (Row 6)
        progress_card = self.create_grid_card(grid_container, "📊 Progress Bar", row=0, col=3)

        progress_var = tk.BooleanVar(value=self.settings.get('progress_bar', False))
        tk.Checkbutton(progress_card, text='Enable',
                      variable=progress_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('progress_bar', progress_var.get())).pack(anchor='w', padx=15, pady=5)

        pos_frame = tk.Frame(progress_card, bg=AppStyles.BG_CARD)
        pos_frame.pack(fill='x', padx=15, pady=3)
        tk.Label(pos_frame, text='Position:', bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 9)).pack(side='left')
        self.progress_position_var = tk.StringVar(value=self.settings.get('progress_bar_position', 'bottom'))
        progress_pos = ttk.Combobox(pos_frame, textvariable=self.progress_position_var, values=['top', 'bottom'], state='readonly', width=8)
        progress_pos.pack(side='left', padx=5)
        progress_pos.bind('<<ComboboxSelected>>', lambda e: self.update_setting('progress_bar_position', self.progress_position_var.get()))

        self.create_color_picker(progress_card, 'Color:', 'progress_color', '#00ff40')
        self.create_slider_control(progress_card, 'Height:', 'progress_bar_height', 2, 15, 5, value_format=lambda v: f"{int(v)}px")

        # Watermark (Row 7)
        watermark_card = self.create_grid_card(grid_container, "🏷️ Watermark", row=1, col=3)

        watermark_var = tk.BooleanVar(value=self.settings.get('watermark_enabled', False))
        tk.Checkbutton(watermark_card, text='Enable',
                      variable=watermark_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('watermark_enabled', watermark_var.get())).pack(anchor='w', padx=15, pady=5)

        file_frame = tk.Frame(watermark_card, bg=AppStyles.BG_CARD)
        file_frame.pack(fill='x', padx=15, pady=3)
        self.watermark_path_var = tk.StringVar(value=self.settings.get('watermark_image_path', ''))
        watermark_entry = tk.Entry(file_frame, textvariable=self.watermark_path_var,
                                   bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                   font=('Segoe UI', 8), width=12)
        watermark_entry.pack(side='left')
        ModernButton(file_frame, text='📁',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 8, 'bold'),
                    padx=8, pady=3,
                    command=self.browse_watermark).pack(side='left', padx=3)

        pos_frame = tk.Frame(watermark_card, bg=AppStyles.BG_CARD)
        pos_frame.pack(fill='x', padx=15, pady=3)
        tk.Label(pos_frame, text='Pos:', bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 9)).pack(side='left')
        self.watermark_position_var = tk.StringVar(value=self.settings.get('watermark_position', 'bottom-right'))
        watermark_pos = ttk.Combobox(pos_frame, textvariable=self.watermark_position_var,
                                    values=['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'],
                                    state='readonly', width=10)
        watermark_pos.pack(side='left', padx=5)
        watermark_pos.bind('<<ComboboxSelected>>', lambda e: self.update_setting('watermark_position', self.watermark_position_var.get()))

        self.create_slider_control(watermark_card, 'Opacity:', 'watermark_opacity', 0, 100, 70)
        self.create_slider_control(watermark_card, 'Size:', 'watermark_scale', 0.05, 0.5, 0.15, resolution=0.01, value_format=lambda v: f"{int(v*100)}%")

        # Region Blur Settings (Row 8)
        blur_card = self.create_grid_card(grid_container, "🌫️ Region Blur", row=2, col=3)

        blur_var = tk.BooleanVar(value=self.settings.get('region_blur_enabled', False))
        tk.Checkbutton(blur_card, text='Enable',
                      variable=blur_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('region_blur_enabled', blur_var.get())).pack(anchor='w', padx=15, pady=5)

        region_frame = tk.Frame(blur_card, bg=AppStyles.BG_CARD)
        region_frame.pack(fill='x', padx=15, pady=3)
        tk.Label(region_frame, text='Region:', bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 9)).pack(side='left')
        self.blur_region_var = tk.StringVar(value=self.settings.get('blur_region', 'bottom'))
        blur_region = ttk.Combobox(region_frame, textvariable=self.blur_region_var,
                                   values=['top', 'bottom', 'left', 'right', 'center', 'top_bottom', 'left_right'],
                                   state='readonly', width=10)
        blur_region.pack(side='left', padx=5)
        blur_region.bind('<<ComboboxSelected>>', lambda e: self.update_setting('blur_region', self.blur_region_var.get()))

        self.create_slider_control(blur_card, 'Size:', 'blur_region_size', 10, 50, 30, value_format=lambda v: f"{int(v)}%")
        self.create_slider_control(blur_card, 'Intensity:', 'blur_intensity', 1, 100, 15, value_format=lambda v: f"{int(v)}")

        tint_var = tk.BooleanVar(value=self.settings.get('blur_color_tint_enabled', False))
        tk.Checkbutton(blur_card, text='Color Tint',
                      variable=tint_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('blur_color_tint_enabled', tint_var.get())).pack(anchor='w', padx=15, pady=3)

        tint_color_frame = tk.Frame(blur_card, bg=AppStyles.BG_CARD)
        tint_color_frame.pack(fill='x', padx=15, pady=3)

        self.blur_tint_color_var = tk.StringVar(value=self.settings.get('blur_tint_color', '#000000'))
        tint_preview = tk.Frame(tint_color_frame, bg=self.blur_tint_color_var.get(), width=20, height=15, relief='solid', borderwidth=1)
        tint_preview.pack(side='left', padx=(0, 3))
        tk.Entry(tint_color_frame, textvariable=self.blur_tint_color_var, width=7, bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK, font=('Segoe UI', 8)).pack(side='left')

        def pick_tint_color():
            color = colorchooser.askcolor(title="Choose Blur Tint Color")
            if color[1]:
                self.blur_tint_color_var.set(color[1])
                tint_preview.config(bg=color[1])
                self.update_setting('blur_tint_color', color[1])

        ModernButton(tint_color_frame, text='🎨', bg_color=AppStyles.ACCENT_INFO, font=('Segoe UI', 8), padx=6, pady=2, command=pick_tint_color).pack(side='left', padx=3)

        self.create_slider_control(blur_card, 'Tint:', 'blur_tint_opacity', 0, 100, 50, value_format=lambda v: f"{int(v)}%")

        feather_var = tk.BooleanVar(value=self.settings.get('blur_feather_edge', True))
        tk.Checkbutton(blur_card, text='Feather Edge',
                      variable=feather_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 8),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('blur_feather_edge', feather_var.get())).pack(anchor='w', padx=15, pady=3)

        # Blur Text Overlay (Row 9) - Full text controls like Quote Settings
        blur_text_card = self.create_grid_card(grid_container, "📝 Blur Text Overlay", row=3, col=3)

        # Text content input (add before other controls) - Multi-line Text widget
        content_frame = tk.Frame(blur_text_card, bg=AppStyles.BG_CARD)
        content_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(content_frame, text='Text Content (Multi-line supported):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        # Use Text widget for multi-line support
        blur_text_content = tk.Text(content_frame, height=4, wrap='word',
                                    bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                    font=('Segoe UI', 10), relief='flat', bd=2,
                                    insertbackground=AppStyles.TEXT_DARK)
        blur_text_content.pack(fill='x', pady=(0, 5))

        # Insert existing content
        current_content = self.settings.get('blur_text_content', 'Your Text Here')
        blur_text_content.insert('1.0', current_content)

        # Save on focus out
        def save_blur_text_content(event=None):
            content = blur_text_content.get('1.0', 'end-1c')
            self.update_setting('blur_text_content', content)

        blur_text_content.bind('<FocusOut>', save_blur_text_content)

        # Store reference for later access
        self.blur_text_content_widget = blur_text_content

        # Use the same comprehensive text controls as Quote Settings
        self.create_text_controls(blur_text_card, 'blur_text')

    def browse_watermark(self):
        """Browse for watermark image file"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select Watermark Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.watermark_path_var.set(filename)
            self.update_setting('watermark_image_path', filename)

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

        # Enable mouse wheel scrolling
        self.setup_mousewheel_scroll(canvas, content)

        # ═══════════════════════════════════════════════════════════
        # 4-COLUMN GRID LAYOUT: Left = Audio Sources, Right = TTS Settings
        # ═══════════════════════════════════════════════════════════
        main_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Left column for audio sources (Original, BGM, Voiceover)
        col1_frame = tk.Frame(main_container, bg=AppStyles.BG_CARD)
        col1_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Right column for TTS settings
        col3_frame = tk.Frame(main_container, bg=AppStyles.BG_CARD)
        col3_frame.pack(side='left', fill='both', expand=True)

        # LEFT COLUMN - Audio Sources
        grid_container = tk.Frame(col1_frame, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True)
        grid_container.columnconfigure(0, weight=1)

        # Original Audio Settings (Row 0)
        original_card = self.create_grid_card(grid_container, "🎧 Original Audio", row=0, col=0)

        mute_var = tk.BooleanVar(value=self.settings.get('mute_original_audio', False))
        tk.Checkbutton(original_card, text='Mute Original Audio',
                      variable=mute_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('mute_original_audio', mute_var.get())).pack(anchor='w', padx=20, pady=10)

        self.create_slider_control(original_card, 'Volume:', 'original_audio_volume', 0.0, 1.0, 0.5, resolution=0.1)

        # BGM Settings (Row 1)
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

        # Voiceover Settings (Row 2)
        vo_card = self.create_grid_card(grid_container, "🎙️ Voiceover", row=0, col=2)

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

        # RIGHT COLUMN - TTS Settings
        grid_container = tk.Frame(col3_frame, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True)
        grid_container.columnconfigure(0, weight=1)

        # TTS Settings (Row 0)
        tts_card = self.create_grid_card(grid_container, "🗣️ TTS Settings", row=0, col=3)

        tts_var = tk.BooleanVar(value=self.settings.get('use_tts_voiceover', True))
        tk.Checkbutton(tts_card, text='Generate Voiceover from Text (TTS)',
                      variable=tts_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('use_tts_voiceover', tts_var.get())).pack(anchor='w', padx=20, pady=10)

        # Use Original Audio option (skip TTS but still apply effects)
        use_original_audio_var = tk.BooleanVar(value=self.settings.get('use_original_audio', False))
        tk.Checkbutton(tts_card, text='Use Original Audio (Skip TTS, Apply Effects Only)',
                      variable=use_original_audio_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('use_original_audio', use_original_audio_var.get())).pack(anchor='w', padx=20, pady=10)

        # Info
        info_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        info_frame.pack(fill='x', padx=20, pady=(0, 10))
        tk.Label(info_frame, text='ℹ️ TTS: Converts quote text to speech using AI voices.\n   Use Original Audio: Keeps video audio, applies voice/pitch effects.',
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

        # NeuTTS option (Voice Cloning)
        neutts_frame = tk.Frame(engine_frame, bg=AppStyles.BG_INPUT)
        neutts_frame.pack(fill='x', pady=(10, 5))

        tk.Radiobutton(neutts_frame, text='🎙️ NeuTTS (Voice Cloning)',
                      variable=self.tts_engine_var, value='neutts',
                      bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                      activebackground=AppStyles.BG_INPUT,
                      selectcolor=AppStyles.BG_CARD,
                      font=('Segoe UI', 10, 'bold'),
                      command=self.on_tts_engine_change).pack(anchor='w')

        tk.Label(neutts_frame, text='   • Clone any voice from audio sample',
                bg=AppStyles.BG_INPUT, fg=AppStyles.ACCENT_PRIMARY,
                font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=20)
        tk.Label(neutts_frame, text='   • Create custom voices from 10-30 seconds of audio',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(anchor='w', padx=20)
        tk.Label(neutts_frame, text='   • Requires NeuTTS server running locally',
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
            # American Female voices
            'af_alloy - Female (American, Versatile)',
            'af_aoede - Female (American, Melodic)',
            'af_bella - Female (American, Warm)',
            'af_jessica - Female (American, Conversational)',
            'af_kore - Female (American, Expressive)',
            'af_nicole - Female (American, Soft)',
            'af_nova - Female (American, Friendly)',
            'af_river - Female (American, Smooth)',
            'af_sarah - Female (American, Clear)',
            'af_sky - Female (American, Youthful)',
            # American Male voices
            'am_adam - Male (American, Professional)',
            'am_echo - Male (American, Resonant)',
            'am_eric - Male (American, Casual)',
            'am_fenrir - Male (American, Deep)',
            'am_liam - Male (American, Warm)',
            'am_michael - Male (American, Energetic)',
            'am_onyx - Male (American, Rich)',
            'am_puck - Male (American, Playful)',
            # British Female voices
            'bf_alice - Female (British, Gentle)',
            'bf_emma - Female (British, Elegant)',
            'bf_isabella - Female (British, Sophisticated)',
            'bf_lily - Female (British, Sweet)',
            # British Male voices
            'bm_daniel - Male (British, Refined)',
            'bm_fable - Male (British, Storyteller)',
            'bm_george - Male (British, Distinguished)',
            'bm_lewis - Male (British, Authoritative)',
            # Hindi voices
            'hf_alpha - Female (Hindi)',
            'hf_beta - Female (Hindi)',
            'hm_omega - Male (Hindi)',
            'hm_psi - Male (Hindi)',
            # Japanese voices
            'jf_alpha - Female (Japanese)',
            'jf_gongitsune - Female (Japanese, Storyteller)',
            'jf_nezumi - Female (Japanese)',
            'jf_tebukuro - Female (Japanese)',
            'jm_kumo - Male (Japanese)',
            # Spanish voices
            'ef_dora - Female (Spanish)',
            'em_alex - Male (Spanish)',
            'em_santa - Male (Spanish)',
            # French voice
            'ff_siwis - Female (French)',
            # Italian voices
            'if_sara - Female (Italian)',
            'im_nicola - Male (Italian)',
            # Brazilian Portuguese voices
            'pf_dora - Female (Brazilian Portuguese)',
            'pm_alex - Male (Brazilian Portuguese)',
            'pm_santa - Male (Brazilian Portuguese)'
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

        # Kokoro Speed Control
        kokoro_speed_frame = tk.Frame(self.kokoro_settings_frame, bg=AppStyles.BG_CARD)
        kokoro_speed_frame.pack(fill='x', pady=8)

        tk.Label(kokoro_speed_frame, text='Speech Speed:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        speed_slider_frame = tk.Frame(kokoro_speed_frame, bg=AppStyles.BG_CARD)
        speed_slider_frame.pack(fill='x')

        tk.Label(speed_slider_frame, text='Slow',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        self.kokoro_speed_var = tk.DoubleVar(value=self.settings.get('kokoro_speed', 1.0))
        kokoro_speed_slider = tk.Scale(speed_slider_frame, from_=0.5, to=2.0,
                                       resolution=0.1, orient='horizontal',
                                       variable=self.kokoro_speed_var,
                                       bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                                       highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                                       command=lambda v: self.update_setting('kokoro_speed', float(v)))
        kokoro_speed_slider.pack(side='left', fill='x', expand=True, padx=5)

        tk.Label(speed_slider_frame, text='Fast',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        tk.Label(kokoro_speed_frame, text='1.0 = Normal speed, 0.8 = Slower, 1.2 = Faster',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(5, 0))

        # Kokoro Pitch Control
        kokoro_pitch_frame = tk.Frame(self.kokoro_settings_frame, bg=AppStyles.BG_CARD)
        kokoro_pitch_frame.pack(fill='x', pady=8)

        tk.Label(kokoro_pitch_frame, text='Kokoro Pitch (semitones):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        kokoro_pitch_slider_frame = tk.Frame(kokoro_pitch_frame, bg=AppStyles.BG_CARD)
        kokoro_pitch_slider_frame.pack(fill='x')

        tk.Label(kokoro_pitch_slider_frame, text='Lower',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        self.kokoro_pitch_var = tk.IntVar(value=self.settings.get('kokoro_pitch', 0))
        kokoro_pitch_slider = tk.Scale(kokoro_pitch_slider_frame, from_=-12, to=12,
                                       resolution=1, orient='horizontal',
                                       variable=self.kokoro_pitch_var,
                                       bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                                       highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                                       command=lambda v: self.update_setting('kokoro_pitch', int(v)))
        kokoro_pitch_slider.pack(side='left', fill='x', expand=True, padx=5)

        tk.Label(kokoro_pitch_slider_frame, text='Higher',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        tk.Label(kokoro_pitch_frame, text='ℹ️ -12 = 1 octave lower, +12 = 1 octave higher',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(5, 0))

        # Model Path (optional - for custom installations)
        model_path_frame = tk.Frame(self.kokoro_settings_frame, bg=AppStyles.BG_CARD)
        model_path_frame.pack(fill='x', pady=8)

        tk.Label(model_path_frame, text='Model Path (Optional):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        tk.Label(model_path_frame, text='Leave empty to auto-detect. Set path if models are in custom location.',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(0, 5))

        model_path_row = tk.Frame(model_path_frame, bg=AppStyles.BG_CARD)
        model_path_row.pack(fill='x')

        self.kokoro_model_path_var = tk.StringVar(value=self.settings.get('kokoro_model_path', ''))
        model_path_entry = tk.Entry(model_path_row, textvariable=self.kokoro_model_path_var,
                                    bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                    font=('Segoe UI', 9), relief='flat')
        model_path_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        model_path_entry.bind('<FocusOut>', lambda e: self.update_setting('kokoro_model_path', self.kokoro_model_path_var.get()))

        def browse_kokoro_models():
            from tkinter import filedialog
            folder = filedialog.askdirectory(title="Select Kokoro Models Folder")
            if folder:
                self.kokoro_model_path_var.set(folder)
                self.update_setting('kokoro_model_path', folder)

        ModernButton(model_path_row, text='Browse',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 8, 'bold'),
                    padx=10, pady=4,
                    command=browse_kokoro_models).pack(side='right')

        # Cloud TTS Voice Selection (shown when Cloud TTS is selected)
        self.cloud_voice_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        self.cloud_voice_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(self.cloud_voice_frame, text='Cloud TTS Voice:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        # ALL voice keys (60+)
        self.tts_voice_keys = [
            # PREMIUM MOTIVATIONAL VOICES (Multilingual - Support Urdu + English)
            'steffan_multi', 'andrew_multi', 'brian_multi', 'ava_multi', 'emma_multi',
            'alloy', 'nova', 'shimmer', 'kai', 'luna', 'jenny_multi', 'ryan_multi',
            # US Female Deep
            'monica', 'nancy', 'ana', 'aria', 'michelle', 'amber', 'ashley', 'sara',
            # US Male Deep
            'tony', 'jason', 'brandon', 'jacob', 'christopher', 'guy', 'davis', 'eric', 'roger',
            # British
            'thomas', 'mia', 'sonia', 'libby', 'alfie',
            # Australian
            'annette', 'natasha', 'william',
            # Indian English
            'neerja', 'prabhat',
            # URDU VOICES (اردو)
            'asad_multi', 'uzma_multi', 'asad', 'uzma', 'salman', 'gul', 'faiz', 'parveen'
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

        # NeuTTS Settings (shown when NeuTTS is selected)
        self.neutts_settings_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        self.neutts_settings_frame.pack(fill='x', padx=20, pady=8)

        # Server Status
        neutts_status_frame = tk.Frame(self.neutts_settings_frame, bg=AppStyles.BG_INPUT, pady=10, padx=15)
        neutts_status_frame.pack(fill='x', pady=(0, 10))

        self.neutts_status_label = tk.Label(neutts_status_frame, text='⚠️ NeuTTS Server: Not Connected',
                                            bg=AppStyles.BG_INPUT, fg=AppStyles.ACCENT_WARNING,
                                            font=('Segoe UI', 9, 'bold'))
        self.neutts_status_label.pack(anchor='w')

        # Server URL
        url_frame = tk.Frame(self.neutts_settings_frame, bg=AppStyles.BG_CARD)
        url_frame.pack(fill='x', pady=8)

        tk.Label(url_frame, text='Server URL:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.neutts_url_var = tk.StringVar(value=self.settings.get('neutts_server_url', 'http://localhost:7860'))
        neutts_url_entry = tk.Entry(url_frame, textvariable=self.neutts_url_var,
                                    bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                    font=('Segoe UI', 9), relief='flat')
        neutts_url_entry.pack(fill='x', pady=(0, 5))
        neutts_url_entry.bind('<FocusOut>', lambda e: self.update_setting('neutts_server_url', self.neutts_url_var.get()))

        ModernButton(url_frame, text='🔄 Check Connection',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.check_neutts_connection).pack(anchor='w')

        # Voice Cloning Section
        clone_frame = tk.Frame(self.neutts_settings_frame, bg=AppStyles.BG_CARD)
        clone_frame.pack(fill='x', pady=8)

        tk.Label(clone_frame, text='🎙️ Clone New Voice:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        # Voice name
        name_row = tk.Frame(clone_frame, bg=AppStyles.BG_CARD)
        name_row.pack(fill='x', pady=2)
        tk.Label(name_row, text='Voice Name:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(side='left')
        self.neutts_voice_name_var = tk.StringVar()
        tk.Entry(name_row, textvariable=self.neutts_voice_name_var,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat', width=30).pack(side='left', padx=(5, 0))

        # Audio file
        audio_row = tk.Frame(clone_frame, bg=AppStyles.BG_CARD)
        audio_row.pack(fill='x', pady=2)
        tk.Label(audio_row, text='Audio Sample:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(side='left')
        self.neutts_audio_var = tk.StringVar()
        tk.Entry(audio_row, textvariable=self.neutts_audio_var,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat', width=25).pack(side='left', padx=(5, 5), fill='x', expand=True)
        ModernButton(audio_row, text='Browse',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 8, 'bold'),
                    padx=8, pady=3,
                    command=self.browse_neutts_audio).pack(side='left')

        # Reference text
        ref_row = tk.Frame(clone_frame, bg=AppStyles.BG_CARD)
        ref_row.pack(fill='x', pady=2)
        tk.Label(ref_row, text='Reference Text (what is said in audio):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w')
        self.neutts_ref_text = tk.Text(clone_frame, height=3, wrap='word',
                                       bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                       font=('Segoe UI', 9), relief='flat')
        self.neutts_ref_text.pack(fill='x', pady=2)

        ModernButton(clone_frame, text='🎤 Clone Voice',
                    bg_color=AppStyles.ACCENT_SUCCESS,
                    font=('Segoe UI', 10, 'bold'),
                    padx=20, pady=8,
                    command=self.clone_neutts_voice).pack(anchor='w', pady=(5, 0))

        # Cloned Voice Selection
        voice_select_frame = tk.Frame(self.neutts_settings_frame, bg=AppStyles.BG_CARD)
        voice_select_frame.pack(fill='x', pady=8)

        tk.Label(voice_select_frame, text='Select Cloned Voice:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        self.neutts_voice_var = tk.StringVar(value=self.settings.get('neutts_voice', ''))
        self.neutts_voice_combo = ttk.Combobox(voice_select_frame, textvariable=self.neutts_voice_var,
                                               values=[], state='readonly',
                                               font=('Segoe UI', 9), width=40)
        self.neutts_voice_combo.pack(fill='x', pady=5)
        self.neutts_voice_combo.bind('<<ComboboxSelected>>',
                                     lambda e: self.update_setting('neutts_voice', self.neutts_voice_var.get()))

        ModernButton(voice_select_frame, text='🔄 Refresh Voices',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 8, 'bold'),
                    padx=10, pady=4,
                    command=self.refresh_neutts_voices).pack(anchor='w')

        # NeuTTS Speed Control
        neutts_speed_frame = tk.Frame(self.neutts_settings_frame, bg=AppStyles.BG_CARD)
        neutts_speed_frame.pack(fill='x', pady=8)

        tk.Label(neutts_speed_frame, text='NeuTTS Speed:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        speed_slider_frame = tk.Frame(neutts_speed_frame, bg=AppStyles.BG_CARD)
        speed_slider_frame.pack(fill='x')

        self.neutts_speed_var = tk.DoubleVar(value=self.settings.get('neutts_speed', 1.0))
        neutts_speed_slider = tk.Scale(speed_slider_frame, from_=0.5, to=2.0,
                                       resolution=0.1, orient='horizontal',
                                       variable=self.neutts_speed_var,
                                       bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                                       highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                                       command=lambda v: self.update_setting('neutts_speed', float(v)))
        neutts_speed_slider.pack(side='left', fill='x', expand=True)

        tk.Label(speed_slider_frame, text='0.5=Slow  1.0=Normal  2.0=Fast',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left', padx=(10, 0))

        # NeuTTS Pitch Control
        neutts_pitch_frame = tk.Frame(self.neutts_settings_frame, bg=AppStyles.BG_CARD)
        neutts_pitch_frame.pack(fill='x', pady=8)

        tk.Label(neutts_pitch_frame, text='NeuTTS Pitch (semitones):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        neutts_pitch_slider_frame = tk.Frame(neutts_pitch_frame, bg=AppStyles.BG_CARD)
        neutts_pitch_slider_frame.pack(fill='x')

        tk.Label(neutts_pitch_slider_frame, text='Lower',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        self.neutts_pitch_var = tk.IntVar(value=self.settings.get('neutts_pitch', 0))
        neutts_pitch_slider = tk.Scale(neutts_pitch_slider_frame, from_=-12, to=12,
                                       resolution=1, orient='horizontal',
                                       variable=self.neutts_pitch_var,
                                       bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                                       highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                                       command=lambda v: self.update_setting('neutts_pitch', int(v)))
        neutts_pitch_slider.pack(side='left', fill='x', expand=True, padx=5)

        tk.Label(neutts_pitch_slider_frame, text='Higher',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        tk.Label(neutts_pitch_frame, text='ℹ️ -12 = 1 octave lower, +12 = 1 octave higher',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(5, 0))

        # Speed slider
        self.create_slider_control(tts_card, 'Speech Speed (WPM):', 'tts_speed', 100, 250, 150)

        # Pitch control for Cloud TTS
        pitch_frame = tk.Frame(tts_card, bg=AppStyles.BG_CARD)
        pitch_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(pitch_frame, text='🎵 Voice Pitch (Hz):',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        pitch_slider_frame = tk.Frame(pitch_frame, bg=AppStyles.BG_CARD)
        pitch_slider_frame.pack(fill='x')

        tk.Label(pitch_slider_frame, text='Lower',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        self.tts_pitch_var = tk.IntVar(value=self.settings.get('tts_pitch', 0))
        tts_pitch_slider = tk.Scale(pitch_slider_frame, from_=-50, to=50,
                                    resolution=5, orient='horizontal',
                                    variable=self.tts_pitch_var,
                                    bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                                    highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                                    command=lambda v: self.update_setting('tts_pitch', int(v)))
        tts_pitch_slider.pack(side='left', fill='x', expand=True, padx=5)

        tk.Label(pitch_slider_frame, text='Higher',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8)).pack(side='left')

        tk.Label(pitch_frame, text='ℹ️ Adjust voice pitch: -50Hz (deeper) to +50Hz (higher). 0 = default.',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(5, 0))

        # ═══════════════════════════════════════════════════════════
        # VOICE EFFECTS SECTION
        # ═══════════════════════════════════════════════════════════
        effects_card = tk.Frame(tts_card, bg=AppStyles.BG_INPUT, pady=15, padx=20)
        effects_card.pack(fill='x', padx=15, pady=(15, 10))

        tk.Label(effects_card, text='🎭 Voice Effects',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(0, 5))

        tk.Label(effects_card, text='Apply audio effects to transform the voice',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 10))

        # Voice effect selection
        self.voice_effect_var = tk.StringVar(value=self.settings.get('voice_effect', 'none'))

        effects_list = [
            ('none', '🚫 None (Original Voice)'),
            ('deep', '🔊 Deep Voice (-12 semitones)'),
            ('high', '🎵 High Voice (+12 semitones)'),
            ('robot', '🤖 Robot Voice'),
            ('echo', '🔈 Echo/Reverb'),
            ('whisper', '🤫 Whisper Effect'),
            ('radio', '📻 Radio/Telephone'),
            ('chipmunk', '🐿️ Chipmunk (+18 semitones)')
        ]

        for value, text in effects_list:
            tk.Radiobutton(effects_card, text=text,
                          variable=self.voice_effect_var, value=value,
                          bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                          font=('Segoe UI', 9),
                          activebackground=AppStyles.BG_INPUT,
                          selectcolor=AppStyles.BG_CARD,
                          command=lambda: self.update_setting('voice_effect', self.voice_effect_var.get())).pack(anchor='w', pady=2)

        tk.Label(effects_card, text='ℹ️ Effects are applied using FFmpeg audio filters during processing',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(10, 0))

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

        # Audio Enhancement (Row 1 in right column)
        audio_enhance_card = self.create_grid_card(grid_container, "🎚️ Audio Enhancement", row=1, col=3)

        # Audio Normalization
        norm_var = tk.BooleanVar(value=self.settings.get('audio_normalize', False))
        tk.Checkbutton(audio_enhance_card, text='Audio Normalization (Consistent Volume)',
                      variable=norm_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('audio_normalize', norm_var.get())).pack(anchor='w', padx=20, pady=10)

        tk.Label(audio_enhance_card, text='ℹ️ Normalizes audio to consistent volume levels across all videos',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', padx=20, pady=(0, 10))

        self.create_slider_control(audio_enhance_card, 'Target Audio Level (dB):', 'audio_target_level', -30, -10, -20, value_format=lambda v: f"{int(v)} dB")

        # Audio Ducking
        duck_var = tk.BooleanVar(value=self.settings.get('audio_auto_ducking', False))
        tk.Checkbutton(audio_enhance_card, text='Auto BGM Ducking (Lower BGM when voice speaks)',
                      variable=duck_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 10, 'bold'),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=lambda: self.update_setting('audio_auto_ducking', duck_var.get())).pack(anchor='w', padx=20, pady=10)

        tk.Label(audio_enhance_card, text='ℹ️ Automatically reduces background music volume when voiceover is playing',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', padx=20, pady=(0, 10))

        self.create_slider_control(audio_enhance_card, 'Ducking Amount:', 'audio_ducking_amount', 0.1, 0.8, 0.3, resolution=0.1, value_format=lambda v: f"{int(v*100)}%")

        # ═══════════════════════════════════════════════════════════
        # STANDALONE VOICEOVER GENERATION
        # ═══════════════════════════════════════════════════════════
        standalone_card = tk.Frame(content, bg=AppStyles.BG_INPUT, pady=15, padx=20)
        standalone_card.pack(fill='x', padx=15, pady=(15, 15))

        tk.Label(standalone_card, text='🎤 Standalone Voiceover Generator',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 5))

        tk.Label(standalone_card, text='Generate voiceovers from text files without video processing',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 15))

        # Input File Selection
        input_frame = tk.Frame(standalone_card, bg=AppStyles.BG_INPUT)
        input_frame.pack(fill='x', pady=(0, 10))

        tk.Label(input_frame, text='Input Text File:',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        file_input_row = tk.Frame(input_frame, bg=AppStyles.BG_INPUT)
        file_input_row.pack(fill='x')

        self.standalone_file_var = tk.StringVar()
        tk.Entry(file_input_row, textvariable=self.standalone_file_var,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat', bd=2).pack(side='left', fill='x', expand=True, ipady=6)

        ModernButton(file_input_row, text='📄 Browse File',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.browse_standalone_file).pack(side='left', padx=(5, 0))

        # Input Folder Selection
        folder_frame = tk.Frame(standalone_card, bg=AppStyles.BG_INPUT)
        folder_frame.pack(fill='x', pady=(0, 10))

        tk.Label(folder_frame, text='Or Input Folder (processes all .txt files):',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        folder_input_row = tk.Frame(folder_frame, bg=AppStyles.BG_INPUT)
        folder_input_row.pack(fill='x')

        self.standalone_folder_var = tk.StringVar()
        tk.Entry(folder_input_row, textvariable=self.standalone_folder_var,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat', bd=2).pack(side='left', fill='x', expand=True, ipady=6)

        ModernButton(folder_input_row, text='📁 Browse Folder',
                    bg_color=AppStyles.ACCENT_PRIMARY,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.browse_standalone_folder).pack(side='left', padx=(5, 0))

        # Output Folder Selection
        output_frame = tk.Frame(standalone_card, bg=AppStyles.BG_INPUT)
        output_frame.pack(fill='x', pady=(0, 10))

        tk.Label(output_frame, text='Output Folder for Audio Files:',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))

        output_input_row = tk.Frame(output_frame, bg=AppStyles.BG_INPUT)
        output_input_row.pack(fill='x')

        self.standalone_output_var = tk.StringVar()
        tk.Entry(output_input_row, textvariable=self.standalone_output_var,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat', bd=2).pack(side='left', fill='x', expand=True, ipady=6)

        ModernButton(output_input_row, text='📁 Browse',
                    bg_color=AppStyles.ACCENT_SUCCESS,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=self.browse_standalone_output).pack(side='left', padx=(5, 0))

        # Info label
        tk.Label(standalone_card, text='ℹ️ Uses current TTS settings (engine, voice, speed, pitch, effects)',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(anchor='w', pady=(5, 10))

        # Generate Button and Progress
        btn_frame = tk.Frame(standalone_card, bg=AppStyles.BG_INPUT)
        btn_frame.pack(fill='x', pady=(0, 10))

        ModernButton(btn_frame, text='🎙️ Generate Voiceovers',
                    bg_color=AppStyles.ACCENT_SUCCESS,
                    font=('Segoe UI', 11, 'bold'),
                    padx=30, pady=12,
                    command=self.generate_standalone_voiceovers).pack(side='left')

        ModernButton(btn_frame, text='⏹ Stop',
                    bg_color=AppStyles.ACCENT_DANGER,
                    font=('Segoe UI', 11, 'bold'),
                    padx=20, pady=12,
                    command=self.stop_standalone_generation).pack(side='left', padx=(10, 0))

        # Progress label
        self.standalone_progress_label = tk.Label(standalone_card, text="",
                                                 bg=AppStyles.BG_INPUT,
                                                 fg=AppStyles.TEXT_MEDIUM,
                                                 font=('Segoe UI', 9))
        self.standalone_progress_label.pack(anchor='w', pady=(5, 0))

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

        # Enable mouse wheel scrolling
        self.setup_mousewheel_scroll(canvas, content)

        # ═══════════════════════════════════════════════════════════
        # LIVE PREVIEW - Shows how captions will look with current settings
        # ═══════════════════════════════════════════════════════════
        preview_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        preview_container.pack(fill='x', padx=15, pady=(10, 15))

        preview_card = tk.Frame(preview_container, bg=AppStyles.BG_INPUT, relief='solid', borderwidth=2)
        preview_card.pack(fill='x', padx=5, pady=5)

        tk.Label(preview_card, text='🎬 Live Caption Preview',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(10, 5))

        tk.Label(preview_card, text='See how your captions will appear on the video with all settings applied',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 9)).pack(anchor='w', padx=15, pady=(0, 10))

        # Preview canvas
        self.caption_preview_canvas = tk.Canvas(preview_card, width=700, height=120,
                                               bg='#1a1a1a', highlightthickness=0)
        self.caption_preview_canvas.pack(padx=15, pady=(0, 15))

        # Initialize with sample text
        self.update_caption_preview()

        # ═══════════════════════════════════════════════════════════
        # 4-COLUMN GRID LAYOUT: Left = Settings, Right = Styling
        # ═══════════════════════════════════════════════════════════
        main_container = tk.Frame(content, bg=AppStyles.BG_CARD)
        main_container.pack(fill='both', expand=True, padx=15, pady=10)

        # Left column for basic settings
        col_frame = tk.Frame(main_container, bg=AppStyles.BG_CARD)
        col_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Right column for styling
        col2_frame = tk.Frame(main_container, bg=AppStyles.BG_CARD)
        col2_frame.pack(side='left', fill='both', expand=True)

        # LEFT COLUMN - Basic Settings
        grid_container = tk.Frame(col_frame, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True)
        grid_container.columnconfigure(0, weight=1)

        # Enable Captions (Row 0)
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

        # Caption Style Presets (Row 1)
        preset_card = self.create_grid_card(grid_container, "🎨 Presets", row=1, col=0)

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

        # Emoji Theme (Row 2)
        emoji_card = self.create_grid_card(grid_container, "😊 Emoji", row=0, col=1)

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

        # Global Settings (Row 3)
        global_card = self.create_grid_card(grid_container, "🌍 Global Settings", row=1, col=1)

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

        # RIGHT COLUMN - Styling
        grid_container = tk.Frame(col2_frame, bg=AppStyles.BG_CARD)
        grid_container.pack(fill='both', expand=True)
        grid_container.columnconfigure(0, weight=1)

        # Regular Caption Settings (Row 0)
        regular_card = self.create_grid_card(grid_container, "📝 Regular Captions", row=0, col=2)

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
        capcut_card = self.create_grid_card(grid_container, "✨ CapCut Highlighting", row=0, col=3)

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

        # Animation style
        anim_frame = tk.Frame(capcut_card, bg=AppStyles.BG_CARD)
        anim_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(anim_frame, text='Word Animation Style:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(anchor='w', pady=(0, 5))

        animation_styles = ['none', 'pop', 'bounce', 'fade', 'slide']
        self.caption_animation_var = tk.StringVar(value=self.settings.get('caption_word_animation', 'none'))
        anim_combo = ttk.Combobox(anim_frame, textvariable=self.caption_animation_var,
                                 values=animation_styles, state='readonly',
                                 font=('Segoe UI', 9), width=30)
        anim_combo.pack(fill='x', pady=5)
        anim_combo.bind('<<ComboboxSelected>>',
                       lambda e: self.update_setting('caption_word_animation', self.caption_animation_var.get()))

        # Animation intensity
        self.create_slider_control(capcut_card, 'Animation Intensity:', 'caption_animation_intensity', 1.0, 2.0, 1.2, resolution=0.1)

        # ROW 2: Text Stroke (full width)
        # Stroke/Outline
        stroke_card = self.create_grid_card(grid_container, "🖊️ Text Stroke/Outline", row=1, col=3)

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

        # Enable mouse wheel scrolling
        self.setup_mousewheel_scroll(canvas, content)

        # Combined transitions list for horizontal grid
        all_transitions = [
            ('transition_fade_in', '🌅 Fade In'),
            ('transition_fade_out', '🌇 Fade Out'),
            ('transition_zoom_in', '🔍 Zoom In'),
            ('transition_zoom_out', '🔎 Zoom Out'),
            ('transition_blur_in', '💨 Blur In'),
            ('transition_blur_out', '🌫️ Blur Out'),
            ('transition_slide_in', '⬅️ Slide In'),
            ('transition_slide_out', '➡️ Slide Out'),
            ('transition_wipe_in', '📱 Wipe In'),
            ('transition_wipe_out', '📲 Wipe Out'),
            ('transition_glitch_start', '📺 Glitch Start'),
            ('transition_glitch_end', '⚡ Glitch End'),
            ('transition_cinematic_bars', '🎞️ Cinematic Bars'),
            ('lens_flare_enabled', '✨ Lens Flare'),
            ('light_leak_enabled', '💡 Light Leaks'),
            ('film_burn_enabled', '🔥 Film Burn'),
        ]

        # Create horizontal grid layout (4 columns)
        self.create_effect_grid(content, "🎬 Transitions & Cinematic Effects", all_transitions, columns=4)

        # Transition Settings (Advanced Controls)
        settings_card = tk.Frame(content, bg=AppStyles.BG_INPUT, pady=15, padx=20)
        settings_card.pack(fill='x', padx=15, pady=(15, 0))

        tk.Label(settings_card, text='⚙️ Transition Settings',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 10))

        # Slide/Swipe Direction
        dir_frame = tk.Frame(settings_card, bg=AppStyles.BG_INPUT)
        dir_frame.pack(fill='x', pady=(0, 10))

        tk.Label(dir_frame, text='Slide/Swipe Direction:',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 10))

        self.slide_direction_var = tk.StringVar(value=self.settings.get('transition_slide_direction', 'left'))
        slide_dir_dropdown = ttk.Combobox(dir_frame, textvariable=self.slide_direction_var,
                                         values=['left', 'right', 'up', 'down'],
                                         state='readonly', width=15)
        slide_dir_dropdown.pack(side='left')
        slide_dir_dropdown.bind('<<ComboboxSelected>>',
                               lambda e: self.update_setting('transition_slide_direction', self.slide_direction_var.get()))

        tk.Label(dir_frame, text='(Direction video slides from/to)',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(side='left', padx=(10, 0))

        # Wipe Direction
        wipe_frame = tk.Frame(settings_card, bg=AppStyles.BG_INPUT)
        wipe_frame.pack(fill='x', pady=(0, 10))

        tk.Label(wipe_frame, text='Wipe Direction:',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left', padx=(0, 10))

        self.wipe_direction_var = tk.StringVar(value=self.settings.get('transition_wipe_direction', 'right'))
        wipe_dir_dropdown = ttk.Combobox(wipe_frame, textvariable=self.wipe_direction_var,
                                        values=['left', 'right', 'up', 'down'],
                                        state='readonly', width=15)
        wipe_dir_dropdown.pack(side='left')
        wipe_dir_dropdown.bind('<<ComboboxSelected>>',
                              lambda e: self.update_setting('transition_wipe_direction', self.wipe_direction_var.get()))

        # Duration Sliders
        self.create_slider_control(settings_card, 'Fade Duration:', 'transition_fade_in_duration', 0.1, 2.0, 0.5, resolution=0.1, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(settings_card, 'Zoom Duration:', 'transition_zoom_in_duration', 0.5, 3.0, 1.0, resolution=0.1, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(settings_card, 'Blur Duration:', 'transition_blur_duration', 0.1, 2.0, 0.5, resolution=0.1, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(settings_card, 'Slide Duration:', 'transition_slide_duration', 0.3, 2.0, 0.8, resolution=0.1, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(settings_card, 'Zoom Scale:', 'transition_zoom_scale', 1.1, 2.0, 1.3, resolution=0.1, value_format=lambda v: f"{v:.1f}x")
        self.create_slider_control(settings_card, 'Blur Amount:', 'transition_blur_amount', 5, 30, 15, value_format=lambda v: f"{int(v)}px")
        self.create_slider_control(settings_card, 'Glitch Intensity:', 'transition_glitch_intensity', 0.1, 1.0, 0.5, resolution=0.1, value_format=lambda v: f"{int(v*100)}%")

        # Cinematic Effects Settings (Lens Flare, Light Leaks, Film Burn repeats)
        cinematic_card = tk.Frame(content, bg=AppStyles.BG_INPUT, pady=15, padx=20)
        cinematic_card.pack(fill='x', padx=15, pady=(15, 0))

        tk.Label(cinematic_card, text='✨ Cinematic Effects Settings',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(0, 10))

        # Lens Flare Repeat Control
        flare_repeat_frame = tk.Frame(cinematic_card, bg=AppStyles.BG_INPUT)
        flare_repeat_frame.pack(fill='x', pady=(0, 10))

        self.lens_flare_repeat_var = tk.BooleanVar(value=self.settings.get('lens_flare_repeat_enabled', False))
        flare_repeat_cb = tk.Checkbutton(flare_repeat_frame, text='🔄 Repeat Lens Flare',
                                         variable=self.lens_flare_repeat_var,
                                         bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                         selectcolor=AppStyles.BG_CARD,
                                         activebackground=AppStyles.BG_INPUT,
                                         font=('Segoe UI', 10),
                                         command=lambda: self.update_setting('lens_flare_repeat_enabled', self.lens_flare_repeat_var.get()))
        flare_repeat_cb.pack(side='left')

        tk.Label(flare_repeat_frame, text='(Shows lens flare multiple times during video)',
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'italic')).pack(side='left', padx=(10, 0))

        self.create_slider_control(cinematic_card, 'Lens Flare Interval:', 'lens_flare_repeat_interval', 2.0, 15.0, 5.0, resolution=0.5, value_format=lambda v: f"{v:.1f}s")
        self.create_slider_control(cinematic_card, 'Lens Flare Intensity:', 'lens_flare_intensity', 0.1, 1.0, 0.5, resolution=0.1, value_format=lambda v: f"{int(v*100)}%")

        # Light Leak Repeat Control
        leak_repeat_frame = tk.Frame(cinematic_card, bg=AppStyles.BG_INPUT)
        leak_repeat_frame.pack(fill='x', pady=(10, 10))

        self.light_leak_repeat_var = tk.BooleanVar(value=self.settings.get('light_leak_repeat_enabled', False))
        leak_repeat_cb = tk.Checkbutton(leak_repeat_frame, text='🔄 Repeat Light Leaks',
                                        variable=self.light_leak_repeat_var,
                                        bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                        selectcolor=AppStyles.BG_CARD,
                                        activebackground=AppStyles.BG_INPUT,
                                        font=('Segoe UI', 10),
                                        command=lambda: self.update_setting('light_leak_repeat_enabled', self.light_leak_repeat_var.get()))
        leak_repeat_cb.pack(side='left')

        self.create_slider_control(cinematic_card, 'Light Leak Interval:', 'light_leak_repeat_interval', 3.0, 20.0, 8.0, resolution=1.0, value_format=lambda v: f"{v:.0f}s")

        # Film Burn Repeat Control
        burn_repeat_frame = tk.Frame(cinematic_card, bg=AppStyles.BG_INPUT)
        burn_repeat_frame.pack(fill='x', pady=(10, 10))

        self.film_burn_repeat_var = tk.BooleanVar(value=self.settings.get('film_burn_repeat_enabled', False))
        burn_repeat_cb = tk.Checkbutton(burn_repeat_frame, text='🔄 Repeat Film Burn',
                                        variable=self.film_burn_repeat_var,
                                        bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                        selectcolor=AppStyles.BG_CARD,
                                        activebackground=AppStyles.BG_INPUT,
                                        font=('Segoe UI', 10),
                                        command=lambda: self.update_setting('film_burn_repeat_enabled', self.film_burn_repeat_var.get()))
        burn_repeat_cb.pack(side='left')

        self.create_slider_control(cinematic_card, 'Film Burn Interval:', 'film_burn_repeat_interval', 5.0, 30.0, 10.0, resolution=1.0, value_format=lambda v: f"{v:.0f}s")

    # Helper methods

    def setup_mousewheel_scroll(self, canvas, content):
        """Setup mouse wheel scrolling for a canvas (Windows compatible)"""
        def _on_mousewheel(event):
            # Windows mouse wheel
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")

        # Bind mouse wheel when mouse enters canvas/content
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)
        content.bind('<Enter>', _bind_mousewheel)
        content.bind('<Leave>', _unbind_mousewheel)

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

    def create_grid_card(self, parent, title, row, col, colspan=1, rowspan=1):
        """Create a compact card in a grid layout"""
        # Outer frame for shadow effect
        card_outer = tk.Frame(parent, bg=AppStyles.BORDER_LIGHT, pady=1, padx=1)
        card_outer.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, padx=5, pady=5, sticky='nsew')

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

    def create_slider_control(self, parent, label, key, from_, to, default, resolution=1, value_format=None):
        """Create a modern slider control"""
        slider_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        slider_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(slider_frame, text=label,
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        var = tk.DoubleVar(value=self.settings.get(key, default))

        # Format initial value
        if value_format:
            display_value = value_format(var.get())
        else:
            display_value = str(var.get())

        value_label = tk.Label(slider_frame, text=display_value,
                              bg=AppStyles.BG_CARD, fg=AppStyles.ACCENT_PRIMARY,
                              font=('Segoe UI', 9, 'bold'), width=8)
        value_label.pack(side='right')

        scale = tk.Scale(slider_frame, from_=from_, to=to, resolution=resolution,
                        orient='horizontal', variable=var,
                        bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                        highlightthickness=0, troughcolor=AppStyles.BG_INPUT,
                        showvalue=False,
                        command=lambda v, k=key, vl=value_label, fmt=value_format: self.on_slider_change(k, v, vl, fmt))
        scale.pack(side='left', fill='x', expand=True, padx=10)

    def on_slider_change(self, key, value, value_label, value_format=None):
        """Handle slider value change"""
        val = float(value)

        # Format display value
        if value_format:
            display_value = value_format(val)
        else:
            display_value = f"{val:.2f}" if val < 10 else str(int(val))

        value_label.config(text=display_value)
        self.update_setting(key, val if val < 10 else int(val))

        # Trigger preview update for text settings
        for prefix in ['title', 'quote', 'cta']:
            if key.startswith(f'{prefix}_'):
                self.update_text_preview(prefix)
                break

    def create_text_controls(self, parent, prefix):
        """Create text controls for title/quote/cta"""

        # Live Preview Panel at the top
        preview_container = tk.Frame(parent, bg=AppStyles.BG_CARD)
        preview_container.pack(fill='x', padx=20, pady=(10, 5))

        tk.Label(preview_container, text='📺 Live Preview:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_MEDIUM,
                font=('Segoe UI', 8, 'bold')).pack(anchor='w')

        preview_frame = tk.Frame(preview_container, bg='#1a1a2e', relief='sunken', bd=2)
        preview_frame.pack(fill='x', pady=(2, 0))

        # Preview canvas
        preview_canvas = tk.Canvas(preview_frame, height=50, bg='#1a1a2e', highlightthickness=0)
        preview_canvas.pack(fill='x', padx=5, pady=5)

        # Sample text for preview
        sample_texts = {'title': 'Sample Title', 'quote': '"Sample Quote"', 'cta': 'Follow Now!'}
        sample_text = sample_texts.get(prefix, 'Sample Text')

        # Create preview text item
        preview_text_id = preview_canvas.create_text(
            120, 25,
            text=sample_text,
            fill=self.settings.get(f'{prefix}_text_color', '#FFFFFF'),
            font=(self.settings.get(f'{prefix}_font_family', 'Arial'),
                  min(int(self.settings.get(f'{prefix}_font_size', 30)) // 2, 18),
                  'bold' if self.settings.get(f'{prefix}_font_bold', True) else 'normal')
        )

        # Store preview references for updates
        setattr(self, f'{prefix}_preview_canvas', preview_canvas)
        setattr(self, f'{prefix}_preview_text_id', preview_text_id)
        setattr(self, f'{prefix}_sample_text', sample_text)

        # Update preview when canvas is resized
        def on_canvas_resize(event):
            preview_canvas.coords(preview_text_id, event.width // 2, 25)
        preview_canvas.bind('<Configure>', on_canvas_resize)

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

        # Font Family selection with system fonts
        font_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        font_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(font_frame, text='Font Family:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        # Load system fonts from Windows fonts folder
        font_families = self.get_system_fonts(prefix)
        font_var = tk.StringVar(value=self.settings.get(f'{prefix}_font_family', 'Arial'))
        font_combo = ttk.Combobox(font_frame, textvariable=font_var, values=font_families,
                                  width=35, height=15)
        font_combo.pack(side='right', padx=5)

        def on_font_change(event, p=prefix, v=font_var):
            self.update_setting(f'{p}_font_family', v.get())
            self.update_text_preview(p)

        font_combo.bind('<<ComboboxSelected>>', on_font_change)

        # Store reference to combo for refresh
        setattr(self, f'{prefix}_font_combo', font_combo)

        # Custom fonts folder option
        custom_font_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        custom_font_frame.pack(fill='x', padx=20, pady=4)

        tk.Label(custom_font_frame, text='Custom Fonts:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9)).pack(side='left')

        custom_font_var = tk.StringVar(value=self.settings.get(f'{prefix}_custom_fonts_folder', ''))
        custom_font_entry = tk.Entry(custom_font_frame, textvariable=custom_font_var,
                                     bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                                     font=('Segoe UI', 8), relief='flat', width=15)
        custom_font_entry.pack(side='left', padx=5)

        def browse_custom_fonts():
            folder = filedialog.askdirectory(title=f"Select Custom Fonts Folder for {prefix.title()}")
            if folder:
                custom_font_var.set(folder)
                self.update_setting(f'{prefix}_custom_fonts_folder', folder)
                # Refresh font list
                new_fonts = self.get_system_fonts(prefix)
                font_combo['values'] = new_fonts
                logger.info(f"Custom fonts folder for {prefix}: {folder}")

        ModernButton(custom_font_frame, text='📁',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 8, 'bold'),
                    padx=8, pady=4,
                    command=browse_custom_fonts).pack(side='left', padx=2)

        def clear_custom_fonts():
            custom_font_var.set('')
            self.update_setting(f'{prefix}_custom_fonts_folder', '')
            # Refresh with system fonts only
            new_fonts = self.get_system_fonts(prefix)
            font_combo['values'] = new_fonts

        ModernButton(custom_font_frame, text='✕',
                    bg_color=AppStyles.ACCENT_DANGER,
                    font=('Segoe UI', 8, 'bold'),
                    padx=6, pady=4,
                    command=clear_custom_fonts).pack(side='left', padx=2)

        # Font Style (Bold, Italic)
        style_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        style_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(style_frame, text='Font Style:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        bold_var = tk.BooleanVar(value=self.settings.get(f'{prefix}_font_bold', True))

        def on_bold_change(p=prefix, v=bold_var):
            self.update_setting(f'{p}_font_bold', v.get())
            self.update_text_preview(p)

        tk.Checkbutton(style_frame, text='Bold',
                      variable=bold_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=on_bold_change).pack(side='left', padx=10)

        italic_var = tk.BooleanVar(value=self.settings.get(f'{prefix}_font_italic', False))

        def on_italic_change(p=prefix, v=italic_var):
            self.update_setting(f'{p}_font_italic', v.get())
            self.update_text_preview(p)

        tk.Checkbutton(style_frame, text='Italic',
                      variable=italic_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=on_italic_change).pack(side='left', padx=10)

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

        # Background Color picker
        bg_color_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        bg_color_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(bg_color_frame, text='Background:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        bg_color_var = tk.StringVar(value=self.settings.get(f'{prefix}_bg_color', '#000000'))

        bg_preview = tk.Frame(bg_color_frame, bg=bg_color_var.get(), width=40, height=25,
                             relief='solid', borderwidth=1)
        bg_preview.pack(side='right', padx=5)

        tk.Entry(bg_color_frame, textvariable=bg_color_var, width=10,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat').pack(side='right', padx=5)

        ModernButton(bg_color_frame, text='Pick Color',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=lambda p=prefix, v=bg_color_var, cp=bg_preview: self.pick_bg_color(p, v, cp)).pack(side='right', padx=5)

        # Background Opacity
        self.create_slider_control(parent, 'BG Opacity:', f'{prefix}_bg_opacity', 0, 100, 80, value_format=lambda v: f"{int(v)}%")

        # Text Position
        pos_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        pos_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(pos_frame, text='Position:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        positions = ['top', 'center', 'bottom']
        pos_var = tk.StringVar(value=self.settings.get(f'{prefix}_position', 'center'))
        pos_combo = ttk.Combobox(pos_frame, textvariable=pos_var, values=positions,
                                 state='readonly', width=10)
        pos_combo.pack(side='right', padx=5)
        pos_combo.bind('<<ComboboxSelected>>',
                      lambda e, p=prefix, v=pos_var: self.update_setting(f'{p}_position', v.get()))

        # Outline/Stroke
        outline_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        outline_frame.pack(fill='x', padx=20, pady=8)

        outline_var = tk.BooleanVar(value=self.settings.get(f'{prefix}_outline', True))

        def on_outline_change(p=prefix, v=outline_var):
            self.update_setting(f'{p}_outline', v.get())
            self.update_text_preview(p)

        tk.Checkbutton(outline_frame, text='Text Outline',
                      variable=outline_var, bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                      font=('Segoe UI', 9),
                      activebackground=AppStyles.BG_CARD,
                      selectcolor=AppStyles.BG_INPUT,
                      command=on_outline_change).pack(side='left')

        # Outline Color picker
        outline_color_frame = tk.Frame(parent, bg=AppStyles.BG_CARD)
        outline_color_frame.pack(fill='x', padx=20, pady=8)

        tk.Label(outline_color_frame, text='Outline Color:',
                bg=AppStyles.BG_CARD, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 10)).pack(side='left')

        outline_color_var = tk.StringVar(value=self.settings.get(f'{prefix}_outline_color', '#000000'))

        outline_preview = tk.Frame(outline_color_frame, bg=outline_color_var.get(), width=40, height=25,
                                  relief='solid', borderwidth=1)
        outline_preview.pack(side='right', padx=5)

        tk.Entry(outline_color_frame, textvariable=outline_color_var, width=10,
                bg=AppStyles.BG_INPUT, fg=AppStyles.TEXT_DARK,
                font=('Segoe UI', 9), relief='flat').pack(side='right', padx=5)

        def pick_outline_color():
            color = colorchooser.askcolor(title=f"Choose {prefix} outline color")
            if color[1]:
                outline_color_var.set(color[1])
                outline_preview.config(bg=color[1])
                self.update_setting(f'{prefix}_outline_color', color[1])
                self.update_text_preview(prefix)

        ModernButton(outline_color_frame, text='Pick Color',
                    bg_color=AppStyles.ACCENT_INFO,
                    font=('Segoe UI', 9, 'bold'),
                    padx=15, pady=6,
                    command=pick_outline_color).pack(side='right', padx=5)

        # Outline thickness
        self.create_slider_control(parent, 'Outline Size:', f'{prefix}_outline_size', 0, 10, 2)

    def get_system_fonts(self, prefix=None):
        """Get list of fonts from Windows fonts folder and custom folder"""
        from tkinter import font as tkFont
        fonts = set()

        # Get all system fonts that Windows recognizes (actual font family names)
        try:
            system_font_families = tkFont.families()
            # Filter out fonts starting with @ (vertical variants) and add to set
            for font_name in system_font_families:
                if not font_name.startswith('@'):
                    fonts.add(font_name)
        except Exception as e:
            logger.warning(f"Could not load system fonts: {e}")
            # Fallback to scanning font files
            windows_fonts_path = Path('C:/Windows/Fonts')
            if windows_fonts_path.exists():
                for font_file in windows_fonts_path.glob('*.ttf'):
                    font_name = font_file.stem
                    base_name = font_name.split('-')[0].replace('_', ' ')
                    fonts.add(base_name)
                for font_file in windows_fonts_path.glob('*.otf'):
                    font_name = font_file.stem
                    base_name = font_name.split('-')[0].replace('_', ' ')
                    fonts.add(base_name)

        # Custom fonts folder for this prefix
        if prefix:
            custom_folder = self.settings.get(f'{prefix}_custom_fonts_folder', '')
            if custom_folder and Path(custom_folder).exists():
                custom_path = Path(custom_folder)
                for font_file in custom_path.glob('*.ttf'):
                    font_name = font_file.stem
                    base_name = font_name.split('-')[0].replace('_', ' ')
                    fonts.add(f"[Custom] {base_name}")
                for font_file in custom_path.glob('*.otf'):
                    font_name = font_file.stem
                    base_name = font_name.split('-')[0].replace('_', ' ')
                    fonts.add(f"[Custom] {base_name}")

        # Fallback fonts if none found
        if not fonts:
            fonts = {'Arial', 'Impact', 'Helvetica', 'Times New Roman', 'Verdana',
                    'Georgia', 'Comic Sans MS', 'Trebuchet MS', 'Courier New'}

        return sorted(list(fonts))

    def pick_bg_color(self, prefix, var, preview_frame):
        """Open background color picker"""
        color = colorchooser.askcolor(title=f"Choose {prefix} background color")
        if color[1]:
            var.set(color[1])
            preview_frame.config(bg=color[1])
            self.update_setting(f'{prefix}_bg_color', color[1])
            self.update_text_preview(prefix)

    def update_setting(self, key, value):
        """Update a setting value"""
        self.settings[key] = value
        logger.debug(f"Setting updated: {key} = {value}")

        # Update live preview if it's a text setting
        for prefix in ['title', 'quote', 'cta']:
            if key.startswith(f'{prefix}_'):
                self.update_text_preview(prefix)
                break

    def update_text_preview(self, prefix):
        """Update the live preview for a text section"""
        try:
            canvas = getattr(self, f'{prefix}_preview_canvas', None)
            text_id = getattr(self, f'{prefix}_preview_text_id', None)
            sample_text = getattr(self, f'{prefix}_sample_text', 'Sample')

            if canvas and text_id:
                # Get current settings
                font_family = self.settings.get(f'{prefix}_font_family', 'Arial')
                # Remove [Custom] prefix if present
                if font_family.startswith('[Custom] '):
                    font_family = font_family[9:]

                font_size = min(int(self.settings.get(f'{prefix}_font_size', 30)) // 2, 18)
                text_color = self.settings.get(f'{prefix}_text_color', '#FFFFFF')
                bg_color = self.settings.get(f'{prefix}_bg_color', '#000000')
                outline_color = self.settings.get(f'{prefix}_outline_color', '#000000')
                outline_enabled = self.settings.get(f'{prefix}_outline', True)
                is_bold = self.settings.get(f'{prefix}_font_bold', True)
                is_italic = self.settings.get(f'{prefix}_font_italic', False)

                # Build font style
                style = ''
                if is_bold:
                    style += 'bold '
                if is_italic:
                    style += 'italic'
                style = style.strip() or 'normal'

                # Update canvas background (simulated text background)
                bg_opacity = self.settings.get(f'{prefix}_bg_opacity', 80) / 100
                canvas.config(bg=bg_color if bg_opacity > 0.5 else '#1a1a2e')

                # Clear existing outline text items if any
                outline_tag = f'{prefix}_outline'
                canvas.delete(outline_tag)

                # Get text position from main text item
                coords = canvas.coords(text_id)
                if coords:
                    x, y = coords[0], coords[1]

                    # Draw outline if enabled and color differs from text color
                    if outline_enabled and outline_color != text_color:
                        # Draw outline by creating text at offset positions
                        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1),
                                      (-1, 0), (1, 0), (0, -1), (0, 1)]:
                            canvas.create_text(
                                x + dx, y + dy,
                                text=sample_text,
                                fill=outline_color,
                                font=(font_family, font_size, style),
                                tags=outline_tag
                            )

                    # Lower outline items below main text
                    canvas.tag_lower(outline_tag)

                # Update main text properties
                canvas.itemconfig(text_id,
                                 fill=text_color,
                                 font=(font_family, font_size, style))

        except Exception as e:
            logger.debug(f"Preview update error for {prefix}: {e}")

    def pick_color(self, prefix, var, preview_frame):
        """Open color picker"""
        color = colorchooser.askcolor(title=f"Choose {prefix} color")
        if color[1]:
            var.set(color[1])
            preview_frame.config(bg=color[1])
            self.update_setting(f'{prefix}_text_color', color[1])
            self.update_text_preview(prefix)

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

    def update_caption_preview(self):
        """Update the live preview of captions with current settings"""
        if not hasattr(self, 'caption_preview_canvas'):
            return

        canvas = self.caption_preview_canvas
        canvas.delete('all')

        # Get current settings
        highlight_enabled = self.settings.get('caption_highlight_enabled', False)
        font_style = self.settings.get('caption_font_style', 'segoeui.ttf')
        highlight_font_size = int(self.settings.get('caption_highlight_font_size', 42))
        caption_font_size = int(self.settings.get('caption_font_size', 38))

        # Colors
        highlight_color = self.settings.get('caption_highlight_color', '#FFD700')
        inactive_color = self.settings.get('caption_inactive_color', '#FFFFFF')
        bg_enabled = self.settings.get('caption_bg_enabled', False)
        bg_color = self.settings.get('caption_bg_color', '#000000')
        stroke_enabled = self.settings.get('caption_stroke_enabled', False)
        stroke_color = self.settings.get('caption_active_stroke_color', '#000000')

        # Sample text
        sample_words = ["This", "Is", "Your", "Caption", "Preview"]

        # Draw preview
        x_start = 50
        y = 60
        x = x_start

        for i, word in enumerate(sample_words):
            # Determine if this is the "active" word (middle word for demo)
            is_active = (i == 2) and highlight_enabled
            color = highlight_color if is_active else inactive_color
            size = highlight_font_size if is_active else caption_font_size
            font = ('Segoe UI Bold' if is_active else 'Segoe UI', size)

            # Draw background if enabled
            if bg_enabled:
                bbox = canvas.bbox(canvas.create_text(x, y, text=word, font=font))
                if bbox:
                    canvas.create_rectangle(bbox[0]-5, bbox[1]-3, bbox[2]+5, bbox[3]+3,
                                          fill=bg_color, outline='')

            # Draw stroke if enabled
            if stroke_enabled:
                for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                    canvas.create_text(x+dx, y+dy, text=word, font=font,
                                     fill=stroke_color, tags='preview')

            # Draw main text
            canvas.create_text(x, y, text=word, font=font, fill=color, tags='preview')

            x += len(word) * (size // 2) + 20

    def apply_caption_preset(self):
        """Apply selected caption preset"""
        preset = self.caption_preset_var.get()
        logger.info(f"Applying caption preset: {preset}")

        # Update preview after applying preset
        self.update_caption_preview()

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
                'caption_stroke_width': 3,
                'caption_word_animation': 'pop',
                'caption_animation_intensity': 1.2
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
                'caption_stroke_width': 4,
                'caption_word_animation': 'bounce',
                'caption_animation_intensity': 1.3
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

    # ═══════════════════════════════════════════════════════════
    # STANDALONE VOICEOVER GENERATION FUNCTIONS
    # ═══════════════════════════════════════════════════════════

    def browse_standalone_file(self):
        """Browse for a single text file for standalone voiceover"""
        file = filedialog.askopenfilename(title="Select Text File",
                                         filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file:
            self.standalone_file_var.set(file)
            self.standalone_folder_var.set('')  # Clear folder if file selected
            logger.info(f"Standalone voiceover file selected: {file}")

    def browse_standalone_folder(self):
        """Browse for folder containing text files"""
        folder = filedialog.askdirectory(title="Select Folder with Text Files")
        if folder:
            self.standalone_folder_var.set(folder)
            self.standalone_file_var.set('')  # Clear file if folder selected
            logger.info(f"Standalone voiceover folder selected: {folder}")

    def browse_standalone_output(self):
        """Browse for output folder for generated voiceovers"""
        folder = filedialog.askdirectory(title="Select Output Folder for Audio Files")
        if folder:
            self.standalone_output_var.set(folder)
            logger.info(f"Standalone output folder selected: {folder}")

    def stop_standalone_generation(self):
        """Stop standalone voiceover generation"""
        self.standalone_stop_flag = True
        self.standalone_progress_label.config(text="⏹ Stopping...")

    def generate_standalone_voiceovers(self):
        """Generate voiceovers from text file(s) using current TTS settings"""
        import subprocess

        # Check inputs
        input_file = self.standalone_file_var.get().strip()
        input_folder = self.standalone_folder_var.get().strip()
        output_folder = self.standalone_output_var.get().strip()

        if not input_file and not input_folder:
            messagebox.showerror("Error", "Please select an input text file or folder")
            return

        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder for audio files")
            return

        # Create output folder if needed
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get list of files to process
        files_to_process = []
        if input_file:
            files_to_process = [Path(input_file)]
        elif input_folder:
            folder_path = Path(input_folder)
            files_to_process = list(folder_path.glob('*.txt'))
            if not files_to_process:
                messagebox.showwarning("Warning", "No .txt files found in the selected folder")
                return

        # Get TTS settings
        tts_engine = self.settings.get('tts_engine', 'cloud')

        self.standalone_stop_flag = False
        self.standalone_progress_label.config(text=f"🔄 Starting... ({len(files_to_process)} files)")
        self.root.update()

        def generate_voiceovers():
            try:
                for i, text_file in enumerate(files_to_process):
                    if self.standalone_stop_flag:
                        self.standalone_progress_label.config(text="⏹ Stopped by user")
                        return

                    # Update progress
                    self.standalone_progress_label.config(
                        text=f"🔄 Processing {i+1}/{len(files_to_process)}: {text_file.name}"
                    )
                    self.root.update()

                    # Read text content
                    try:
                        with open(text_file, 'r', encoding='utf-8') as f:
                            text_content = f.read().strip()
                        if not text_content:
                            logger.warning(f"Empty file: {text_file}")
                            continue
                    except Exception as e:
                        logger.error(f"Error reading {text_file}: {e}")
                        continue

                    # Output file path
                    output_file = output_path / f"{text_file.stem}.mp3"
                    wav_file = output_path / f"{text_file.stem}.wav"

                    try:
                        if tts_engine == 'cloud':
                            # Use Edge TTS
                            import edge_tts
                            import asyncio

                            voice_key = self.settings.get('tts_voice', 'aria')
                            if TTSGenerator:
                                voice_id = TTSGenerator.VOICES.get(voice_key, 'en-US-AriaNeural')
                            else:
                                voice_id = 'en-US-AriaNeural'

                            speed = self.settings.get('tts_speed', 150)
                            pitch = self.settings.get('tts_pitch', 0)

                            async def generate_audio():
                                rate_percent = int((speed - 150) / 150 * 100)
                                rate = f"{rate_percent:+d}%"
                                pitch_str = f"{pitch:+d}Hz"
                                communicate = edge_tts.Communicate(text_content, voice_id, rate=rate, pitch=pitch_str)
                                await communicate.save(str(output_file))

                            asyncio.run(generate_audio())

                        elif tts_engine == 'local':
                            # Use Kokoro TTS
                            from kokoro_onnx import Kokoro
                            import soundfile as sf

                            voice_setting = self.settings.get('kokoro_voice', 'af_bella')
                            if ' - ' in voice_setting:
                                voice = voice_setting.split(' - ')[0].strip()
                            else:
                                voice = voice_setting
                            speed = float(self.settings.get('kokoro_speed', 1.0))

                            # Find Kokoro model
                            model_path = self.settings.get('kokoro_model_path', '')
                            search_paths = [
                                model_path,
                                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VoiceModules', 'KokoroTTS'),
                                os.path.dirname(os.path.abspath(__file__)),
                            ]

                            kokoro = None
                            for base_path in search_paths:
                                if not base_path or not os.path.exists(base_path):
                                    continue
                                for model_name in ['kokoro-v0_19.onnx', 'kokoro-v1.0.onnx', 'kokoro.onnx']:
                                    model_file = os.path.join(base_path, model_name)
                                    if os.path.exists(model_file):
                                        for voices_name in ['voices-multilingual.bin', 'voices-v1.0.bin', 'voices.bin']:
                                            voices_file = os.path.join(base_path, voices_name)
                                            if os.path.exists(voices_file):
                                                kokoro = Kokoro(model_file, voices_file)
                                                break
                                    if kokoro:
                                        break
                                if kokoro:
                                    break

                            if kokoro:
                                audio, sample_rate = kokoro.create(text=text_content, voice=voice, speed=speed)
                                sf.write(str(wav_file), audio, sample_rate)
                                # Convert to MP3
                                subprocess.run([
                                    'ffmpeg', '-y', '-i', str(wav_file),
                                    '-acodec', 'libmp3lame', '-q:a', '2',
                                    str(output_file)
                                ], capture_output=True, check=True)
                                wav_file.unlink()

                        elif tts_engine == 'neutts':
                            # Use NeuTTS
                            if NeuTTSHelper:
                                server_url = self.settings.get('neutts_server_url', 'http://localhost:7860')
                                helper = NeuTTSHelper(server_url)
                                helper.load_voice_library('neutts_voices.json')

                                selected_voice = self.settings.get('neutts_voice', '')
                                speed = float(self.settings.get('neutts_speed', 1.0))

                                success, message = helper.generate_speech(
                                    text=text_content,
                                    voice_name=selected_voice,
                                    output_path=str(wav_file),
                                    speed=speed,
                                    pitch=1.0
                                )

                                if success:
                                    # Convert to MP3
                                    subprocess.run([
                                        'ffmpeg', '-y', '-i', str(wav_file),
                                        '-acodec', 'libmp3lame', '-q:a', '2',
                                        str(output_file)
                                    ], capture_output=True, check=True)
                                    if wav_file.exists():
                                        wav_file.unlink()

                        # Apply voice effects if selected
                        voice_effect = self.settings.get('voice_effect', 'none')
                        if voice_effect != 'none' and output_file.exists():
                            effect_file = output_path / f"{text_file.stem}_effect.mp3"
                            filters = []

                            if voice_effect == 'deep':
                                filters.append("asetrate=44100*0.5,aresample=44100")
                            elif voice_effect == 'high':
                                filters.append("asetrate=44100*2,aresample=44100")
                            elif voice_effect == 'robot':
                                filters.append("afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75")
                            elif voice_effect == 'echo':
                                filters.append("aecho=0.8:0.88:60:0.4")
                            elif voice_effect == 'whisper':
                                filters.append("highpass=f=1000,lowpass=f=3000,volume=1.5")
                            elif voice_effect == 'radio':
                                filters.append("highpass=f=300,lowpass=f=3400,equalizer=f=1000:t=h:w=200:g=3")
                            elif voice_effect == 'chipmunk':
                                filters.append("asetrate=44100*2.5,aresample=44100")

                            if filters:
                                filter_chain = ','.join(filters)
                                subprocess.run([
                                    'ffmpeg', '-y', '-i', str(output_file),
                                    '-af', filter_chain,
                                    '-acodec', 'libmp3lame', '-q:a', '2',
                                    str(effect_file)
                                ], capture_output=True, check=True)
                                output_file.unlink()
                                effect_file.rename(output_file)

                        logger.info(f"Generated voiceover: {output_file}")

                    except Exception as e:
                        logger.error(f"Error generating voiceover for {text_file}: {e}")
                        continue

                # Done
                self.standalone_progress_label.config(
                    text=f"✅ Completed! {len(files_to_process)} files processed. Output: {output_folder}"
                )
                messagebox.showinfo("Success", f"Generated {len(files_to_process)} voiceover(s)\nOutput folder: {output_folder}")

            except Exception as e:
                self.standalone_progress_label.config(text=f"❌ Error: {str(e)}")
                logger.error(f"Standalone voiceover error: {e}")
                messagebox.showerror("Error", str(e))

        # Run in background thread
        thread = threading.Thread(target=generate_voiceovers, daemon=True)
        thread.start()

    def play_voice_preview(self):
        """Generate and play voice preview"""
        import tempfile
        import subprocess
        import platform

        # Check if using Kokoro or Cloud TTS
        tts_engine = self.settings.get('tts_engine', 'cloud')

        # Get test text from Text widget
        test_text = self.preview_text_widget.get('1.0', 'end-1c').strip()
        if not test_text:
            self.preview_status_label.config(text="⚠ Please enter test text")
            return

        # Update status
        self.preview_status_label.config(text="🔄 Generating preview audio...")
        self.root.update()

        # Generate audio in background thread
        def generate_and_play():
            try:
                temp_dir = tempfile.gettempdir()

                if tts_engine == 'local':
                    # Use Kokoro TTS
                    try:
                        from kokoro_onnx import Kokoro
                        import numpy as np
                        import soundfile as sf
                    except ImportError as e:
                        self.preview_status_label.config(text=f"❌ Missing package: {e}")
                        return

                    # Get Kokoro voice
                    voice_setting = self.kokoro_voice_var.get()
                    if ' - ' in voice_setting:
                        voice = voice_setting.split(' - ')[0].strip()
                    else:
                        voice = voice_setting

                    speed = float(self.settings.get('kokoro_speed', 1.0))

                    preview_file = Path(temp_dir) / f"tts_preview_kokoro_{voice}.mp3"

                    # Find and initialize Kokoro
                    import os
                    model_path = self.settings.get('kokoro_model_path', '')

                    # Search for model files
                    search_paths = [
                        model_path,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VoiceModules', 'KokoroTTS'),
                        os.path.dirname(os.path.abspath(__file__)),
                    ]

                    kokoro = None
                    for base_path in search_paths:
                        if not base_path or not os.path.exists(base_path):
                            continue

                        found_model = None
                        found_voices = None

                        for model_name in ['kokoro-v0_19.onnx', 'kokoro-v1.0.onnx', 'kokoro.onnx']:
                            test_path = os.path.join(base_path, model_name)
                            if os.path.exists(test_path):
                                found_model = test_path
                                break

                        for voices_name in ['voices-multilingual.bin', 'voices-v1.0.bin', 'voices.bin']:
                            test_path = os.path.join(base_path, voices_name)
                            if os.path.exists(test_path):
                                found_voices = test_path
                                break

                        if found_model and found_voices:
                            kokoro = Kokoro(found_model, found_voices)
                            break

                    if not kokoro:
                        self.preview_status_label.config(text="❌ Kokoro models not found")
                        return

                    # Generate audio
                    audio, sample_rate = kokoro.create(text=test_text, voice=voice, speed=speed)

                    # Save as WAV then convert to MP3
                    wav_path = preview_file.with_suffix('.wav')
                    sf.write(str(wav_path), audio, sample_rate)

                    # Get pitch and voice effect settings
                    pitch_semitones = self.settings.get('kokoro_pitch', 0)
                    voice_effect = self.settings.get('voice_effect', 'none')

                    # Build FFmpeg filter chain
                    filters = []

                    # Apply pitch shift if not zero
                    if pitch_semitones != 0:
                        # Calculate pitch factor: 2^(semitones/12)
                        pitch_factor = 2 ** (pitch_semitones / 12)
                        filters.append(f"asetrate={sample_rate}*{pitch_factor},aresample={sample_rate}")

                    # Apply voice effects
                    if voice_effect == 'deep':
                        if pitch_semitones == 0:  # Only apply if not already pitch shifted
                            filters.append(f"asetrate={sample_rate}*0.5,aresample={sample_rate}")
                    elif voice_effect == 'high':
                        if pitch_semitones == 0:
                            filters.append(f"asetrate={sample_rate}*2,aresample={sample_rate}")
                    elif voice_effect == 'robot':
                        filters.append("afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75")
                    elif voice_effect == 'echo':
                        filters.append("aecho=0.8:0.88:60:0.4")
                    elif voice_effect == 'whisper':
                        filters.append("highpass=f=1000,lowpass=f=3000,volume=1.5")
                    elif voice_effect == 'radio':
                        filters.append("highpass=f=300,lowpass=f=3400,equalizer=f=1000:t=h:w=200:g=3")
                    elif voice_effect == 'chipmunk':
                        if pitch_semitones == 0:
                            filters.append(f"asetrate={sample_rate}*2.5,aresample={sample_rate}")

                    # Build FFmpeg command
                    ffmpeg_cmd = ['ffmpeg', '-y', '-i', str(wav_path)]

                    if filters:
                        filter_chain = ','.join(filters)
                        ffmpeg_cmd.extend(['-af', filter_chain])

                    ffmpeg_cmd.extend(['-acodec', 'libmp3lame', '-q:a', '2', str(preview_file)])

                    subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
                    wav_path.unlink()

                    voice_display = voice_setting
                    effect_label = f" + {voice_effect}" if voice_effect != 'none' else ""
                    pitch_label = f" (pitch: {pitch_semitones:+d})" if pitch_semitones != 0 else ""
                    self.preview_status_label.config(text=f"▶ Playing Kokoro: {voice}{pitch_label}{effect_label}")

                elif tts_engine == 'neutts':
                    # Use NeuTTS (Voice Cloning)
                    if not NeuTTSHelper:
                        self.preview_status_label.config(text="❌ NeuTTS helper not available")
                        return

                    # Get selected voice
                    selected_voice = self.settings.get('neutts_voice', '')
                    if not selected_voice:
                        self.preview_status_label.config(text="❌ No NeuTTS voice selected")
                        return

                    server_url = self.settings.get('neutts_server_url', 'http://localhost:7860')
                    speed = float(self.settings.get('neutts_speed', 1.0))
                    pitch_semitones = self.settings.get('neutts_pitch', 0)

                    preview_file = Path(temp_dir) / f"tts_preview_neutts_{selected_voice}.mp3"
                    wav_path = preview_file.with_suffix('.wav')

                    try:
                        # Initialize NeuTTS helper
                        helper = NeuTTSHelper(server_url)

                        # Load voice library from saved file
                        lib_success, lib_msg = helper.load_voice_library('neutts_voices.json')
                        if not lib_success:
                            self.preview_status_label.config(text=f"❌ Failed to load voices: {lib_msg}")
                            return

                        # Generate speech - returns (success, message)
                        success, message = helper.generate_speech(
                            text=test_text,
                            voice_name=selected_voice,
                            output_path=str(wav_path),
                            speed=speed,
                            pitch=1.0  # NeuTTS pitch is 0.5-2.0 scale, we use semitones later
                        )

                        if success and wav_path.exists():
                            # Get voice effect settings
                            voice_effect = self.settings.get('voice_effect', 'none')

                            # Build FFmpeg filter chain
                            filters = []

                            # Apply pitch shift if not zero
                            if pitch_semitones != 0:
                                pitch_factor = 2 ** (pitch_semitones / 12)
                                filters.append(f"asetrate=22050*{pitch_factor},aresample=22050")

                            # Apply voice effects
                            if voice_effect == 'deep':
                                if pitch_semitones == 0:
                                    filters.append("asetrate=22050*0.5,aresample=22050")
                            elif voice_effect == 'high':
                                if pitch_semitones == 0:
                                    filters.append("asetrate=22050*2,aresample=22050")
                            elif voice_effect == 'robot':
                                filters.append("afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75")
                            elif voice_effect == 'echo':
                                filters.append("aecho=0.8:0.88:60:0.4")
                            elif voice_effect == 'whisper':
                                filters.append("highpass=f=1000,lowpass=f=3000,volume=1.5")
                            elif voice_effect == 'radio':
                                filters.append("highpass=f=300,lowpass=f=3400,equalizer=f=1000:t=h:w=200:g=3")
                            elif voice_effect == 'chipmunk':
                                if pitch_semitones == 0:
                                    filters.append("asetrate=22050*2.5,aresample=22050")

                            # Build FFmpeg command
                            ffmpeg_cmd = ['ffmpeg', '-y', '-i', str(wav_path)]

                            if filters:
                                filter_chain = ','.join(filters)
                                ffmpeg_cmd.extend(['-af', filter_chain])

                            ffmpeg_cmd.extend(['-acodec', 'libmp3lame', '-q:a', '2', str(preview_file)])

                            subprocess.run(ffmpeg_cmd, capture_output=True, check=True)

                            # Clean up wav file
                            if wav_path.exists():
                                wav_path.unlink()

                            effect_label = f" + {voice_effect}" if voice_effect != 'none' else ""
                            pitch_label = f" (pitch: {pitch_semitones:+d})" if pitch_semitones != 0 else ""
                            self.preview_status_label.config(text=f"▶ Playing NeuTTS: {selected_voice}{pitch_label}{effect_label}")
                        else:
                            self.preview_status_label.config(text=f"❌ NeuTTS failed: {message}")
                            return

                    except Exception as e:
                        self.preview_status_label.config(text=f"❌ NeuTTS error: {str(e)}")
                        logger.error(f"NeuTTS preview error: {e}")
                        return

                else:
                    # Use Cloud TTS (edge-tts)
                    try:
                        import edge_tts
                        import asyncio
                    except ImportError:
                        self.preview_status_label.config(text="❌ edge-tts not installed. Run: pip install edge-tts")
                        return

                    # Get selected voice key
                    display_name = self.tts_voice_var.get()
                    voice_key = 'aria'

                    if TTSGenerator:
                        voice_options = [TTSGenerator.VOICE_NAMES.get(k, k) for k in self.tts_voice_keys]
                        try:
                            voice_index = voice_options.index(display_name)
                            voice_key = self.tts_voice_keys[voice_index]
                        except (ValueError, IndexError):
                            voice_key = 'aria'

                    # Get voice mapping
                    if TTSGenerator:
                        voice_id = TTSGenerator.VOICES.get(voice_key, 'en-US-AriaNeural')
                    else:
                        voice_id = 'en-US-AriaNeural'

                    preview_file = Path(temp_dir) / f"tts_preview_{voice_key}.mp3"
                    speed = self.settings.get('tts_speed', 150)
                    pitch = self.settings.get('tts_pitch', 0)

                    # Generate audio using edge-tts
                    async def generate_audio():
                        rate_percent = int((speed - 150) / 150 * 100)
                        rate = f"{rate_percent:+d}%"
                        pitch_str = f"{pitch:+d}Hz"
                        communicate = edge_tts.Communicate(test_text, voice_id, rate=rate, pitch=pitch_str)
                        await communicate.save(str(preview_file))

                    asyncio.run(generate_audio())

                    # Apply voice effects using FFmpeg
                    voice_effect = self.settings.get('voice_effect', 'none')
                    if voice_effect != 'none':
                        effect_file = preview_file.with_suffix('.effect.mp3')
                        filters = []

                        if voice_effect == 'deep':
                            filters.append("asetrate=44100*0.5,aresample=44100")
                        elif voice_effect == 'high':
                            filters.append("asetrate=44100*2,aresample=44100")
                        elif voice_effect == 'robot':
                            filters.append("afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75")
                        elif voice_effect == 'echo':
                            filters.append("aecho=0.8:0.88:60:0.4")
                        elif voice_effect == 'whisper':
                            filters.append("highpass=f=1000,lowpass=f=3000,volume=1.5")
                        elif voice_effect == 'radio':
                            filters.append("highpass=f=300,lowpass=f=3400,equalizer=f=1000:t=h:w=200:g=3")
                        elif voice_effect == 'chipmunk':
                            filters.append("asetrate=44100*2.5,aresample=44100")

                        if filters:
                            filter_chain = ','.join(filters)
                            ffmpeg_cmd = [
                                'ffmpeg', '-y', '-i', str(preview_file),
                                '-af', filter_chain,
                                '-acodec', 'libmp3lame', '-q:a', '2',
                                str(effect_file)
                            ]
                            subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
                            # Replace original with effected version
                            preview_file.unlink()
                            effect_file.rename(preview_file)

                    voice_display = TTSGenerator.VOICE_NAMES.get(voice_key, voice_key) if TTSGenerator else voice_key
                    effect_label = f" + {voice_effect}" if voice_effect != 'none' else ""
                    pitch_label = f" (pitch: {pitch:+d}Hz)" if pitch != 0 else ""
                    self.preview_status_label.config(text=f"▶ Playing: {voice_display}{pitch_label}{effect_label}")

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
        """Handle TTS engine selection change (Cloud vs Local vs NeuTTS)"""
        engine = self.tts_engine_var.get()
        self.update_setting('tts_engine', engine)
        logger.info(f"TTS engine changed to: {engine}")

        # Hide all settings frames first
        self.cloud_voice_frame.pack_forget()
        self.kokoro_settings_frame.pack_forget()
        self.neutts_settings_frame.pack_forget()

        # Show appropriate settings
        if engine == 'cloud':
            self.cloud_voice_frame.pack(fill='x', padx=20, pady=8)
        elif engine == 'local':  # Kokoro
            self.kokoro_settings_frame.pack(fill='x', padx=20, pady=8)
            # Check Kokoro installation
            self.check_kokoro_installation()
        elif engine == 'neutts':
            self.neutts_settings_frame.pack(fill='x', padx=20, pady=8)
            # Check NeuTTS server connection
            self.check_neutts_connection()

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

    # ═══════════════════════════════════════════════════════════
    # NEUTTS HANDLER METHODS
    # ═══════════════════════════════════════════════════════════

    def check_neutts_connection(self):
        """Check if NeuTTS server is running and update status"""
        if NeuTTSHelper is None:
            self.neutts_status_label.config(
                text='❌ NeuTTS: Module Not Installed',
                fg=AppStyles.ACCENT_DANGER
            )
            return

        def check_in_thread():
            try:
                server_url = self.neutts_url_var.get()
                helper = NeuTTSHelper(server_url)
                is_running, status_msg = helper.check_server_status()

                # Update UI in main thread
                self.root.after(0, lambda: self._update_neutts_status(is_running, status_msg, helper))
            except Exception as e:
                self.root.after(0, lambda: self.neutts_status_label.config(
                    text=f'❌ Error: {str(e)}',
                    fg=AppStyles.ACCENT_DANGER
                ))

        # Run in background thread
        thread = threading.Thread(target=check_in_thread, daemon=True)
        thread.start()

    def _update_neutts_status(self, is_running, status_msg, helper):
        """Update NeuTTS status label and load voices if connected"""
        if is_running:
            self.neutts_status_label.config(
                text=status_msg,
                fg=AppStyles.ACCENT_SUCCESS
            )
            # Store helper for later use
            self._neutts_helper = helper
            # Load saved voice library
            helper.load_voice_library()
            self._populate_neutts_voices(helper)
        else:
            self.neutts_status_label.config(
                text=status_msg,
                fg=AppStyles.ACCENT_WARNING
            )

    def _populate_neutts_voices(self, helper):
        """Populate the cloned voices dropdown"""
        voices = helper.get_available_voices()
        voice_names = list(voices.keys())
        self.neutts_voice_combo['values'] = voice_names

        # Select previously saved voice if available
        saved_voice = self.settings.get('neutts_voice', '')
        if saved_voice in voice_names:
            self.neutts_voice_var.set(saved_voice)
            self.update_setting('neutts_voice', saved_voice)
        elif voice_names:
            self.neutts_voice_var.set(voice_names[0])
            # Save the auto-selected voice
            self.update_setting('neutts_voice', voice_names[0])

    def browse_neutts_audio(self):
        """Browse for audio sample file for voice cloning"""
        filetypes = [
            ('Audio Files', '*.wav *.mp3 *.flac *.m4a'),
            ('WAV Files', '*.wav'),
            ('MP3 Files', '*.mp3'),
            ('All Files', '*.*')
        ]
        filename = filedialog.askopenfilename(
            title='Select Voice Sample Audio',
            filetypes=filetypes
        )
        if filename:
            self.neutts_audio_var.set(filename)

    def clone_neutts_voice(self):
        """Clone a voice from the provided audio sample"""
        if NeuTTSHelper is None:
            messagebox.showerror("Error", "NeuTTS module is not installed")
            return

        # Get input values
        voice_name = self.neutts_voice_name_var.get().strip()
        audio_file = self.neutts_audio_var.get().strip()
        ref_text = self.neutts_ref_text.get('1.0', 'end').strip()

        # Validate inputs
        if not voice_name:
            messagebox.showerror("Error", "Please enter a voice name")
            return
        if not audio_file:
            messagebox.showerror("Error", "Please select an audio sample file")
            return
        if not os.path.exists(audio_file):
            messagebox.showerror("Error", f"Audio file not found: {audio_file}")
            return
        if not ref_text:
            messagebox.showerror("Error", "Please enter the reference text (what is said in the audio)")
            return

        # Show progress
        self.neutts_status_label.config(
            text='⏳ Cloning voice...',
            fg=AppStyles.ACCENT_WARNING
        )

        def clone_in_thread():
            try:
                server_url = self.neutts_url_var.get()
                helper = NeuTTSHelper(server_url)

                # Load existing library
                helper.load_voice_library()

                # Clone the voice
                success, message = helper.clone_voice(
                    voice_name=voice_name,
                    audio_file_path=audio_file,
                    reference_text=ref_text,
                    language='en'
                )

                if success:
                    # Save library
                    helper.save_voice_library()
                    self._neutts_helper = helper

                # Update UI in main thread
                self.root.after(0, lambda: self._handle_clone_result(success, message, helper))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Clone Error", str(e)))
                self.root.after(0, lambda: self.neutts_status_label.config(
                    text='❌ Clone failed',
                    fg=AppStyles.ACCENT_DANGER
                ))

        # Run in background thread
        thread = threading.Thread(target=clone_in_thread, daemon=True)
        thread.start()

    def _handle_clone_result(self, success, message, helper):
        """Handle the result of voice cloning"""
        if success:
            self.neutts_status_label.config(
                text=message,
                fg=AppStyles.ACCENT_SUCCESS
            )
            messagebox.showinfo("Success", message)
            # Refresh voices list
            self._populate_neutts_voices(helper)
            # Clear input fields
            self.neutts_voice_name_var.set('')
            self.neutts_audio_var.set('')
            self.neutts_ref_text.delete('1.0', 'end')
        else:
            self.neutts_status_label.config(
                text=message,
                fg=AppStyles.ACCENT_DANGER
            )
            messagebox.showerror("Clone Failed", message)

    def refresh_neutts_voices(self):
        """Refresh the list of cloned voices from the server"""
        if NeuTTSHelper is None:
            messagebox.showerror("Error", "NeuTTS module is not installed")
            return

        try:
            server_url = self.neutts_url_var.get()
            helper = NeuTTSHelper(server_url)

            # Check connection first
            is_running, status_msg = helper.check_server_status()
            if not is_running:
                self.neutts_status_label.config(
                    text=status_msg,
                    fg=AppStyles.ACCENT_WARNING
                )
                messagebox.showwarning("Server Offline", "NeuTTS server is not running")
                return

            # Load voice library
            success, msg = helper.load_voice_library()
            if success:
                self._neutts_helper = helper
                self._populate_neutts_voices(helper)
                self.neutts_status_label.config(
                    text=f'✓ Loaded {len(helper.get_available_voices())} voices',
                    fg=AppStyles.ACCENT_SUCCESS
                )
            else:
                self.neutts_status_label.config(
                    text='No saved voices found',
                    fg=AppStyles.TEXT_MEDIUM
                )
                self.neutts_voice_combo['values'] = []

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh voices: {str(e)}")

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

                    # Process video with index
                    automation.process_single_video(video, video_index=i)
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

    def refresh_template_list(self):
        """Refresh the template dropdown with available templates"""
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)

        # Get list of template files
        templates = []
        if templates_dir.exists():
            for file in templates_dir.glob('*.json'):
                templates.append(file.stem)

        # Update dropdown
        self.template_dropdown['values'] = templates
        if templates:
            self.template_var.set(templates[0])

    def save_template(self):
        """Save current settings as a template"""
        from tkinter import simpledialog, messagebox

        # Ask for template name
        template_name = simpledialog.askstring("Save Template", "Enter template name:")

        if template_name:
            templates_dir = Path('templates')
            templates_dir.mkdir(exist_ok=True)

            template_file = templates_dir / f"{template_name}.json"

            try:
                # Save current settings
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", f"Template '{template_name}' saved successfully!")
                self.refresh_template_list()
                self.template_var.set(template_name)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save template: {str(e)}")

    def load_template(self):
        """Load a template and apply settings"""
        from tkinter import messagebox

        template_name = self.template_var.get()

        if not template_name:
            messagebox.showwarning("No Template", "Please select a template to load")
            return

        templates_dir = Path('templates')
        template_file = templates_dir / f"{template_name}.json"

        if not template_file.exists():
            messagebox.showerror("Error", f"Template '{template_name}' not found")
            return

        try:
            # Load template settings
            with open(template_file, 'r', encoding='utf-8') as f:
                template_settings = json.load(f)

            # Apply settings
            self.settings.update(template_settings)

            # Save to main settings file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Success", f"Template '{template_name}' loaded! Restart the GUI to see all changes.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load template: {str(e)}")

    def delete_template(self):
        """Delete selected template"""
        from tkinter import messagebox

        template_name = self.template_var.get()

        if not template_name:
            messagebox.showwarning("No Template", "Please select a template to delete")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete template '{template_name}'?"):
            return

        templates_dir = Path('templates')
        template_file = templates_dir / f"{template_name}.json"

        try:
            if template_file.exists():
                template_file.unlink()
                messagebox.showinfo("Success", f"Template '{template_name}' deleted")
                self.refresh_template_list()
            else:
                messagebox.showerror("Error", f"Template '{template_name}' not found")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete template: {str(e)}")

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
