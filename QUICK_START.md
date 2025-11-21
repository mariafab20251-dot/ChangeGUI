# Quick Start Guide

## First Time Setup

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/)
   - Check "Add to PATH" during installation

2. **Install FFmpeg**
   - Download from [ffmpeg.org](https://ffmpeg.org/)
   - Add to system PATH

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python complete_automation_gui.py
```

## Basic Usage

### 1. Quick Process Tab
- **Video Folder**: Select folder with your MP4/AVI/MOV files
- **Quotes File**: Select a .txt file with quotes (one per line)
- **Output Folder**: Where processed videos will be saved
- Enable desired features:
  - ✅ Generate Captions - Auto-generated word-by-word captions
  - ✅ Generate TTS Voiceover - AI voice reading the quote
  - ✅ Add Background Music - Add BGM to your videos
  - ✅ Apply Video Zoom Effect - Ken Burns style zoom
  - ✅ Pulsing Call-to-Action - Animated CTA text

### 2. Text Settings Tab
Configure your text overlays:
- **Title Settings** - Top text layer
- **Quote Settings** - Main quote text
- **Call-to-Action Settings** - Bottom CTA text

Adjust:
- Font size (10-100)
- Text color (click "Pick Color")
- Enable/disable each layer

### 3. Visual Effects Tab
Add professional effects:
- **Text Effects**: Fade In, Slide Up, Bounce, Kinetic Typing, Glitch
- **Visual Effects**: Text Glow, Vignette, Background Dim, Film Grain
- **Particle Effects**: Glitter, Stars, Hearts, Confetti

### 4. Audio Settings Tab
Configure audio:
- **TTS Voice**: Choose from multiple voices (andrew_multi, aria_multi, etc.)
- **TTS Speed**: Adjust speaking speed (50-200)
- **Background Music**: Select BGM file and adjust volume
- **Audio Mixing**: Mute original audio if needed

### 5. Captions Tab
Customize captions:
- Enable/disable captions
- Adjust font size
- Enable word highlighting (like CapCut)
- Include emojis in captions

### 6. Transitions Tab
Add professional transitions:
- **Fade**: Fade in/out effects
- **Zoom**: Zoom in/out transitions
- **Cinematic**: Lens flares, light leaks, film burn

## Example Workflow

1. **Prepare Your Files**
   - Put videos in a folder (e.g., `C:\Videos\Source`)
   - Create quotes file (use `example_quotes.txt` as template)
   - Create output folder (e.g., `C:\Videos\Output`)

2. **Configure Settings**
   - Go to **Quick Process** tab
   - Browse and select your folders
   - Enable desired features
   - Click **💾 Save Settings**

3. **Customize Appearance**
   - Go to **Text Settings** tab
   - Adjust font sizes and colors
   - Preview in your mind or process one test video first

4. **Add Effects** (Optional)
   - Go to **Visual Effects** tab
   - Enable effects you want
   - Go to **Audio Settings** for voiceover
   - Go to **Captions** for subtitles

5. **Process Videos**
   - Return to **Quick Process** tab
   - Click **▶ Process Now**
   - Watch progress bar
   - Find processed videos in output folder!

## Tips & Tricks

### Quick Tips
- **Start Simple**: First time? Just enable TTS and captions, skip effects
- **Test First**: Process 1 video before doing a batch of 100
- **Save Settings**: Click **💾 Save Settings** before processing
- **Font Sizes**: Start with default sizes, adjust if text is too big/small

### Performance
- **Processing Time**: Depends on video length and effects enabled
  - Simple (TTS only): ~30-60 seconds per video
  - With effects: ~2-5 minutes per video
- **Memory**: Close other apps during large batches
- **FFmpeg**: Make sure FFmpeg is installed or processing will fail

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg and add to PATH
- Restart terminal after installing

**"No videos found"**
- Check video folder path is correct
- Supported formats: MP4, AVI, MOV, MKV

**"TTS not working"**
- Check internet connection (TTS requires internet)
- Verify edge-tts is installed: `pip install edge-tts`

**"Font not found"**
- Use default fonts first (Arial, Impact)
- For custom fonts, use full path: `C:\Windows\Fonts\fontname.ttf`

## Quotes File Format

Simple text file, one quote per line:

```
Success is not final, failure is not fatal.
Dream big, work hard, stay focused.
Believe you can and you're halfway there.
```

## Output

Processed videos are saved with descriptive filenames:
```
Success is not final #Motivation #Inspiration.mp4
Dream big work hard #Success #Goals.mp4
```

## Need Help?

- Check `README.md` for detailed documentation
- See `example_quotes.txt` for quote format examples
- Check `video_automation.log` for error details
- Open issue on GitHub if you find bugs

---

**Happy video creating! 🎬✨**
