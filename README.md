# ChangeGUI - Video Automation Studio

A professional desktop application for creating automated video content with text overlays, effects, and audio. Perfect for content creators making engaging social media videos for YouTube, Instagram Reels, TikTok, and more.

## Features

### Visual Effects
- **3-Layer Subtitle System** - Title, Quote, and Call-to-Action overlays
- **Text Animations** - Fade, slide, bounce, kinetic typing, glitch effects
- **Motion Effects** - Video zoom, Ken Burns pan, parallax scrolling
- **Lighting Effects** - Neon glow, drop shadows, gradient overlays, light leaks, lens flares
- **Particle Effects** - Glitter, stars, hearts, confetti animations
- **Color Grading** - Warm, cold, cinematic color filters
- **Visual Enhancements** - Vignette, film grain, background dim

### Professional Transitions
- Fade in/out
- Zoom in/out
- Blur transitions
- Slide transitions
- Wipe effects
- Glitch transitions
- Cinematic bars

### Audio Features
- **Text-to-Speech** - Natural voiceover generation using edge-tts
- **Multiple TTS Voices** - Choose from various human-like voices
- **Background Music** - Add custom BGM with volume control and looping
- **Audio Mixing** - Mix original audio, voiceover, and background music
- **Volume Control** - Independent volume controls for each audio layer

### Caption System
- Auto-generated captions synchronized with TTS
- Word-by-word highlighting
- Multiple caption presets
- Customizable fonts, colors, and strokes
- Emoji support in captions
- Multi-line caption layouts

### Professional Tools
- Live video preview
- Batch processing for multiple videos
- Watermark/logo blur
- Progress tracking
- Custom font support
- Comprehensive settings management

## Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (required for video processing)
- Windows OS (currently optimized for Windows, paths need manual configuration on other systems)

### Step 1: Install Python
Download and install Python from [python.org](https://www.python.org/downloads/)

Make sure to check "Add Python to PATH" during installation.

### Step 2: Install FFmpeg
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the files
3. Add FFmpeg to your system PATH

### Step 3: Clone or Download the Repository
```bash
git clone https://github.com/mariafab20251-dot/ChangeGUI.git
cd ChangeGUI
```

### Step 4: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 5 (Linux only): Install tkinter
On Linux systems, you may need to install tkinter separately:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## Usage

### Starting the Application
```bash
python complete_automation_gui.py
```

### Basic Workflow

1. **Select Input Folder** - Choose folder containing your video files
2. **Select Quotes File** - Choose a text file with quotes (one per line)
3. **Select Output Folder** - Choose where to save processed videos
4. **Configure Settings** - Use the tabs to customize:
   - **Text Settings** - Font, size, colors, position
   - **Effects** - Visual effects and animations
   - **Audio** - TTS voiceover and background music
   - **Captions** - Auto-generated caption styling
   - **Transitions** - Video transition effects
5. **Preview** - Use live preview to see how your video looks
6. **Process** - Click "Process Videos" to start automation

### Configuration Files

- **config.py** - Default paths (modify for your system)
- **overlay_settings.json** - All visual and audio settings
- **processing_paths.json** - Current working paths
- **NotoColorEmoji.ttf** - Emoji font for text overlays

### Quotes File Format
Create a text file with one quote per line:
```
Success is not final, failure is not fatal.
Dream big, work hard, stay focused.
Believe you can and you're halfway there.
```

The application will automatically pair each video with a random quote.

## Configuration

### Manual Path Setup
When using on a different PC or drive:
1. Launch the application
2. Use "Browse" buttons to select your folders
3. Paths are saved in `processing_paths.json`

### Font Configuration
- Windows fonts are automatically detected from `C:\Windows\Fonts`
- Custom fonts can be added to the project folder
- Font selection available in Text Settings tab

## Project Structure

```
ChangeGUI/
├── complete_automation_gui.py      # Main GUI application
├── youtube_video_automation_enhanced.py  # Video processing engine
├── config.py                        # Configuration file
├── overlay_settings.json           # Settings storage
├── processing_paths.json           # Current paths
├── NotoColorEmoji.ttf              # Emoji font
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Troubleshooting

### "FFmpeg not found"
- Install FFmpeg and add to system PATH
- Restart your terminal/command prompt after installation

### "ModuleNotFoundError"
- Run `pip install -r requirements.txt` again
- Make sure you're using Python 3.8 or higher

### "Font not found"
- Check that font files exist in Windows Fonts folder
- Use absolute paths for custom fonts
- Restart application after installing new fonts

### "TTS not working"
- Check internet connection (edge-tts requires internet)
- Verify edge-tts is installed: `pip install edge-tts`

### Video processing errors
- Ensure input videos are in supported format (MP4, AVI, MOV)
- Check that videos are not corrupted
- Verify FFmpeg is properly installed

## Advanced Features

### Custom TTS Voices
Available voices include:
- `andrew_multi` - Male, clear and professional
- `aria_multi` - Female, warm and friendly
- `emily_multi` - Female, energetic
- And many more...

### Particle Effects
- **Glitter** - Sparkling particle overlay
- **Stars** - Twinkling star animations
- **Hearts** - Floating heart particles
- **Confetti** - Celebration confetti effect

### Light Leaks
- Multiple color options (pink, blue, golden, purple)
- Adjustable intensity and duration
- Repeating intervals for longer videos
- Direction control (center, left, right)

## Tips for Best Results

1. **Video Quality** - Use high-quality source videos (1080p recommended)
2. **Quote Length** - Keep quotes concise for better readability
3. **Font Selection** - Choose bold fonts for better visibility
4. **Background Opacity** - Adjust to ensure text is readable
5. **Preview First** - Always preview before batch processing
6. **Audio Levels** - Test volume levels before processing multiple videos

## Known Limitations

- Currently optimized for Windows (manual path configuration needed on Linux/Mac)
- Requires internet connection for TTS voiceover generation
- Processing time depends on video length and effects enabled
- Large font files may slow down initial loading

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub: https://github.com/mariafab20251-dot/ChangeGUI/issues

## License

This project is provided as-is for educational and personal use.

## Credits

- **MoviePy** - Video processing library
- **edge-tts** - Text-to-speech generation
- **Pillow** - Image processing
- **FFmpeg** - Media framework

---

**Made with ❤️ for content creators**
