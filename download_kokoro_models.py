"""
Download Kokoro TTS Voice Models
Automatically downloads all required model files for Kokoro TTS
"""

import os
import urllib.request
from pathlib import Path

print("=" * 70)
print("KOKORO TTS MODEL DOWNLOADER")
print("=" * 70)

# Get the Kokoro installation directory
try:
    import kokoro_onnx
    kokoro_dir = Path(kokoro_onnx.__file__).parent
    print(f"\n✅ Found Kokoro installation at: {kokoro_dir}")
except ImportError:
    print("\n❌ Kokoro-onnx not installed. Please install it first:")
    print("   pip install kokoro-onnx")
    exit(1)

# Model files to download
models = [
    {
        'name': 'voices-v1.0.bin',
        'url': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin',
        'size': '~150 MB'
    },
    {
        'name': 'kokoro-v1.0.onnx',
        'url': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
        'size': '~200 MB'
    }
]

print(f"\nWill download {len(models)} model files:")
for model in models:
    print(f"  • {model['name']} ({model['size']})")

print("\n" + "=" * 70)
print("Starting downloads...")
print("=" * 70)

def download_with_progress(url, destination):
    """Download file with progress bar"""
    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = min(int(count * block_size * 100 / total_size), 100)
            mb_downloaded = count * block_size / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)

            # Progress bar
            bar_length = 40
            filled_length = int(bar_length * percent / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)

            print(f'\r  [{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)', end='', flush=True)
        else:
            mb_downloaded = count * block_size / (1024 * 1024)
            print(f'\r  Downloaded: {mb_downloaded:.1f} MB', end='', flush=True)

    urllib.request.urlretrieve(url, destination, reporthook)
    print()  # New line after progress bar

# Download each model
for i, model in enumerate(models, 1):
    destination = kokoro_dir / model['name']

    # Check if already exists
    if destination.exists():
        print(f"\n[{i}/{len(models)}] {model['name']}")
        print(f"  ✅ Already exists, skipping download")
        continue

    print(f"\n[{i}/{len(models)}] Downloading {model['name']}...")
    print(f"  URL: {model['url']}")

    try:
        download_with_progress(model['url'], str(destination))

        # Verify file exists and has size
        if destination.exists():
            file_size = destination.stat().st_size / (1024 * 1024)
            print(f"  ✅ Downloaded successfully ({file_size:.1f} MB)")
        else:
            print(f"  ❌ Download failed - file not found")

    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        print(f"\nManual download instructions:")
        print(f"1. Download: {model['url']}")
        print(f"2. Save to: {destination}")
        continue

print("\n" + "=" * 70)
print("DOWNLOAD COMPLETE!")
print("=" * 70)

# Verify all files are present
print("\nVerifying installation...")
all_present = True
for model in models:
    file_path = kokoro_dir / model['name']
    if file_path.exists():
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ {model['name']} ({size_mb:.1f} MB)")
    else:
        print(f"  ❌ {model['name']} - MISSING")
        all_present = False

if all_present:
    print("\n✅ All model files downloaded successfully!")
    print("\nYou can now:")
    print("1. Run: python test_kokoro.py")
    print("2. Use Kokoro TTS in Video Automation Studio")
    print("3. Generate unlimited FREE voiceovers offline!")
else:
    print("\n⚠️  Some model files are missing.")
    print("Please download them manually from:")
    print("https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0")

print("\n" + "=" * 70)
