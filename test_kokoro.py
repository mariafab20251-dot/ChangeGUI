"""
Test Kokoro TTS Installation
Run this to verify Kokoro TTS is working correctly
"""

import sys

print("=" * 60)
print("KOKORO TTS INSTALLATION TEST")
print("=" * 60)

# Test 1: Check if kokoro-onnx is installed
print("\n[1/4] Checking kokoro-onnx installation...")
try:
    import kokoro_onnx
    print("✅ kokoro-onnx is installed")
    print(f"   Version: {kokoro_onnx.__version__ if hasattr(kokoro_onnx, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ kokoro-onnx not found: {e}")
    print("   Install with: pip install kokoro-onnx scipy numpy")
    sys.exit(1)

# Test 2: Check dependencies
print("\n[2/4] Checking dependencies...")
try:
    import numpy as np
    print(f"✅ numpy {np.__version__}")

    import scipy
    print(f"✅ scipy {scipy.__version__}")

    import onnxruntime
    print(f"✅ onnxruntime {onnxruntime.__version__}")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# Test 3: Check numpy version compatibility
print("\n[3/4] Checking numpy version compatibility...")
numpy_version = tuple(map(int, np.__version__.split('.')[:2]))
if numpy_version >= (2, 3):
    print(f"⚠️  WARNING: numpy {np.__version__} may be incompatible with OpenCV")
    print("   Recommended: pip install \"numpy>=2.0.0,<2.3.0\" --force-reinstall")
else:
    print(f"✅ numpy {np.__version__} is compatible")

# Test 4: Test voice generation
print("\n[4/4] Testing voice generation...")
try:
    from kokoro_onnx import Kokoro

    print("   Initializing Kokoro with voice 'af' (American Male)...")
    kokoro = Kokoro('af', 'af')

    print("   Generating test audio...")
    test_text = "Hello! This is a test of Kokoro text to speech."
    samples = kokoro.create(test_text, speed=1.0)

    print(f"✅ Successfully generated {len(samples)} audio samples")
    print(f"   Sample rate: 24000 Hz")
    print(f"   Duration: ~{len(samples)/24000:.2f} seconds")

    # Save test audio
    import scipy.io.wavfile as wavfile
    test_output = "kokoro_test.wav"
    audio_int16 = (samples * 32767).astype(np.int16)
    wavfile.write(test_output, 24000, audio_int16)

    print(f"✅ Test audio saved: {test_output}")
    print("   You can play this file to hear the voice!")

except Exception as e:
    print(f"❌ Voice generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ KOKORO TTS IS FULLY WORKING!")
print("=" * 60)
print("\nYou can now use Kokoro TTS in Video Automation Studio:")
print("1. Open Audio Settings tab")
print("2. Select 'Local TTS (Kokoro - FREE & Offline)'")
print("3. Choose your preferred voice")
print("4. Start processing videos with FREE offline TTS!")
print("\n" + "=" * 60)
