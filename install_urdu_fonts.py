"""
Urdu Font Installer for Video Automation Studio
Automatically downloads and installs Urdu/Arabic fonts for caption rendering
"""

import os
import urllib.request
from pathlib import Path
import zipfile
import shutil

print("=" * 70)
print("URDU FONT INSTALLER FOR VIDEO AUTOMATION STUDIO")
print("=" * 70)

# Detect Windows fonts folder
if os.name == 'nt':  # Windows
    FONTS_DIR = Path(os.environ.get('WINDIR', 'C:\\Windows')) / 'Fonts'
    USER_FONTS_DIR = Path.home() / 'AppData/Local/Microsoft/Windows/Fonts'
    USER_FONTS_DIR.mkdir(parents=True, exist_ok=True)
else:  # Linux/Mac
    FONTS_DIR = Path.home() / '.fonts'
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    USER_FONTS_DIR = FONTS_DIR

print(f"\nFonts will be installed to: {USER_FONTS_DIR}")

# Fonts to download (Free & Open Source)
FONTS = [
    {
        'name': 'Jameel Noori Nastaleeq',
        'url': 'https://github.com/urdufont/jameel-noori-nastaleeq/raw/master/JameelNooriNastaleeq.ttf',
        'filename': 'JameelNooriNastaleeq.ttf',
        'description': '🌟 MOST POPULAR Urdu font - Beautiful Nastaliq script',
        'size': '~2.5 MB'
    },
    {
        'name': 'Jameel Noori Nastaleeq Kasheeda',
        'url': 'https://github.com/urdufont/jameel-noori-nastaleeq/raw/master/JameelNooriNastaleeqKasheeda.ttf',
        'filename': 'JameelNooriNastaleeqKasheeda.ttf',
        'description': 'Extended variant with Kasheeda',
        'size': '~2.5 MB'
    },
    {
        'name': 'Noto Nastaliq Urdu',
        'url': 'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNastaliqUrdu/NotoNastaliqUrdu-Regular.ttf',
        'filename': 'NotoNastaliqUrdu-Regular.ttf',
        'description': 'High quality Urdu font by Google',
        'size': '~1.5 MB'
    },
    {
        'name': 'Noto Nastaliq Urdu Bold',
        'url': 'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNastaliqUrdu/NotoNastaliqUrdu-Bold.ttf',
        'filename': 'NotoNastaliqUrdu-Bold.ttf',
        'description': 'Bold variant for emphasis',
        'size': '~1.5 MB'
    },
    {
        'name': 'Noto Naskh Arabic',
        'url': 'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Regular.ttf',
        'filename': 'NotoNaskhArabic-Regular.ttf',
        'description': 'Arabic font compatible with Urdu',
        'size': '~200 KB'
    }
]

print(f"\nWill download {len(FONTS)} fonts:")
for font in FONTS:
    print(f"  • {font['name']} ({font['size']})")
    print(f"    {font['description']}")

print("\n" + "=" * 70)
print("Starting downloads...")
print("=" * 70)

def download_with_progress(url, destination):
    """Download file with progress"""
    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = min(int(count * block_size * 100 / total_size), 100)
            mb_downloaded = count * block_size / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)

            bar_length = 40
            filled_length = int(bar_length * percent / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            print(f'\r  [{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)', end='', flush=True)
        else:
            mb_downloaded = count * block_size / (1024 * 1024)
            print(f'\r  Downloaded: {mb_downloaded:.1f} MB', end='', flush=True)

    urllib.request.urlretrieve(url, destination, reporthook)
    print()

# Download each font
success_count = 0
for i, font in enumerate(FONTS, 1):
    destination = USER_FONTS_DIR / font['filename']

    # Check if already exists
    if destination.exists():
        print(f"\n[{i}/{len(FONTS)}] {font['name']}")
        print(f"  ✅ Already installed, skipping")
        success_count += 1
        continue

    print(f"\n[{i}/{len(FONTS)}] Downloading {font['name']}...")

    try:
        download_with_progress(font['url'], str(destination))

        if destination.exists():
            file_size = destination.stat().st_size / (1024 * 1024)
            print(f"  ✅ Installed successfully ({file_size:.1f} MB)")
            success_count += 1
        else:
            print(f"  ❌ Installation failed - file not found")

    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        print(f"\n  Manual download:")
        print(f"  1. Download: {font['url']}")
        print(f"  2. Save to: {destination}")

print("\n" + "=" * 70)
print("INSTALLATION COMPLETE!")
print("=" * 70)

# Verify installation
print("\nVerifying fonts...")
for font in FONTS:
    file_path = USER_FONTS_DIR / font['filename']
    if file_path.exists():
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ {font['name']} ({size_mb:.1f} MB)")
    else:
        print(f"  ❌ {font['name']} - NOT FOUND")

if success_count == len(FONTS):
    print("\n✅ ALL FONTS INSTALLED SUCCESSFULLY!")
    print("\nUrdu fonts are ready to use in Video Automation Studio")
    print("\nYou can now:")
    print("  1. Select Urdu caption presets:")
    print("     • 📖 Urdu Poetry (شاعری - Nastaliq)")
    print("     • 🕌 Islamic Quotes (اسلامی - Calligraphy)")
    print("     • 🎭 Drama Serial (ڈرامہ - Pakistani Style)")
    print("  2. Create videos with beautiful Urdu captions")
    print("  3. Use right-to-left (RTL) text rendering")

    if os.name == 'nt':
        print("\n⚠️  IMPORTANT (Windows):")
        print("  You may need to restart the application for fonts to load properly")
else:
    print(f"\n⚠️  {success_count}/{len(FONTS)} fonts installed")
    print("Some fonts failed to download. Please install them manually.")

print("\n" + "=" * 70)

# Install RTL text rendering library
print("\nInstalling RTL text support libraries...")
print("=" * 70)

try:
    import subprocess
    import sys

    libraries = ['arabic-reshaper', 'python-bidi']

    for lib in libraries:
        print(f"\nInstalling {lib}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
        print(f"✅ {lib} installed successfully")

    print("\n✅ ALL RTL LIBRARIES INSTALLED!")
    print("\nUrdu/Arabic text will now render correctly (right-to-left)")

except Exception as e:
    print(f"\n❌ Failed to install RTL libraries: {e}")
    print("\nManual installation:")
    print("  pip install arabic-reshaper python-bidi")

print("\n" + "=" * 70)
print("SETUP COMPLETE! 🎉")
print("=" * 70)
