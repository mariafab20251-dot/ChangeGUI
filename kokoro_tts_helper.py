"""
Kokoro TTS Helper - Local Offline Text-to-Speech Integration
Provides FREE, unlimited, studio-quality voice generation
"""

import logging
from pathlib import Path
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class KokoroTTSGenerator:
    """Helper class for Kokoro TTS voice generation"""

    # Voice ID mapping from display names to Kokoro voice IDs
    VOICE_MAP = {
        'af - Male 1 (American, Deep)': 'af',
        'af_bella - Female 1 (American, Warm)': 'af_bella',
        'af_sarah - Female 2 (American, Clear)': 'af_sarah',
        'am_adam - Male 2 (American, Professional)': 'am_adam',
        'am_michael - Male 3 (American, Energetic)': 'am_michael',
        'bf_emma - Female 3 (British, Elegant)': 'bf_emma',
        'bf_isabella - Female 4 (British, Sophisticated)': 'bf_isabella',
        'bm_george - Male 4 (British, Distinguished)': 'bm_george',
        'bm_lewis - Male 5 (British, Authoritative)': 'bm_lewis'
    }

    def __init__(self):
        """Initialize Kokoro TTS generator"""
        self.kokoro_available = self._check_installation()

    def _check_installation(self):
        """Check if Kokoro TTS is installed"""
        try:
            import importlib.util
            spec = importlib.util.find_spec("kokoro_onnx")
            if spec is not None:
                logger.info("Kokoro TTS is installed and available")
                return True
            else:
                logger.warning("Kokoro TTS is not installed. Install with: pip install kokoro-onnx")
                return False
        except Exception as e:
            logger.error(f"Error checking Kokoro installation: {e}")
            return False

    def generate_voice(self, text, output_path, voice='af', speed=1.0, quality='wav'):
        """
        Generate voice using Kokoro TTS

        Args:
            text (str): Text to convert to speech
            output_path (str): Path where the audio file should be saved
            voice (str): Voice display name (e.g., 'af - Male 1 (American, Deep)')
            speed (float): Speech speed multiplier (0.5 to 2.0)
            quality (str): 'wav' for studio quality or 'mp3' for compressed

        Returns:
            str: Path to generated audio file, or None if failed
        """
        if not self.kokoro_available:
            logger.error("Kokoro TTS is not available. Cannot generate voice.")
            return None

        try:
            # Convert display name to voice ID
            voice_id = self.VOICE_MAP.get(voice, 'af')

            # Import Kokoro
            from kokoro_onnx import Kokoro

            logger.info(f"Generating voice with Kokoro TTS: voice={voice_id}, quality={quality}")

            # Initialize Kokoro with the selected voice
            kokoro = Kokoro(voice_id, voice_id)

            # Generate audio samples
            # Kokoro generates audio as numpy array
            samples = kokoro.create(text, speed=speed)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save as WAV
            import scipy.io.wavfile as wavfile
            import numpy as np

            # Kokoro outputs at 24kHz sample rate
            sample_rate = 24000

            # Convert to int16 format
            audio_int16 = (samples * 32767).astype(np.int16)

            # Save WAV file
            temp_wav = str(output_file.with_suffix('.wav'))
            wavfile.write(temp_wav, sample_rate, audio_int16)

            logger.info(f"Kokoro TTS generated: {temp_wav}")

            # If MP3 quality requested, convert WAV to MP3
            if quality == 'mp3':
                mp3_path = str(output_file.with_suffix('.mp3'))
                self._convert_to_mp3(temp_wav, mp3_path)

                # Remove temp WAV if MP3 conversion succeeded
                if Path(mp3_path).exists():
                    Path(temp_wav).unlink()
                    logger.info(f"Converted to MP3: {mp3_path}")
                    return mp3_path
                else:
                    logger.warning("MP3 conversion failed, using WAV")
                    return temp_wav
            else:
                return temp_wav

        except ImportError as e:
            logger.error(f"Kokoro TTS import failed. Install with: pip install kokoro-onnx scipy numpy")
            logger.error(f"Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating Kokoro TTS voice: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _convert_to_mp3(self, wav_path, mp3_path):
        """Convert WAV to MP3 using ffmpeg"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', wav_path,
                '-codec:a', 'libmp3lame',
                '-qscale:a', '2',  # High quality MP3
                mp3_path
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Converted WAV to MP3: {mp3_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
        except FileNotFoundError:
            logger.error("FFmpeg not found. Install FFmpeg to enable MP3 conversion.")
        except Exception as e:
            logger.error(f"Error converting to MP3: {e}")

    def test_voice(self, voice='af'):
        """
        Test Kokoro TTS with a sample text

        Args:
            voice (str): Voice display name to test

        Returns:
            bool: True if test successful, False otherwise
        """
        if not self.kokoro_available:
            return False

        try:
            test_text = "Hello! This is a test of the Kokoro text to speech system."
            temp_dir = Path(tempfile.gettempdir())
            test_output = temp_dir / "kokoro_test.wav"

            result = self.generate_voice(test_text, str(test_output), voice=voice)

            if result and Path(result).exists():
                logger.info(f"Kokoro TTS test successful: {result}")
                # Clean up test file
                Path(result).unlink()
                return True
            else:
                logger.error("Kokoro TTS test failed")
                return False

        except Exception as e:
            logger.error(f"Kokoro TTS test error: {e}")
            return False


# Convenience function for easy import
def generate_kokoro_voice(text, output_path, voice='af - Male 1 (American, Deep)',
                          speed=1.0, quality='wav'):
    """
    Convenience function to generate voice using Kokoro TTS

    Args:
        text (str): Text to convert to speech
        output_path (str): Path where the audio file should be saved
        voice (str): Voice display name
        speed (float): Speech speed multiplier (0.5 to 2.0)
        quality (str): 'wav' for studio quality or 'mp3' for compressed

    Returns:
        str: Path to generated audio file, or None if failed
    """
    generator = KokoroTTSGenerator()
    return generator.generate_voice(text, output_path, voice, speed, quality)


if __name__ == "__main__":
    # Test the Kokoro TTS generator
    logging.basicConfig(level=logging.INFO)

    print("Testing Kokoro TTS Generator...")
    generator = KokoroTTSGenerator()

    if generator.kokoro_available:
        print("✅ Kokoro TTS is installed")

        # Test voice generation
        test_text = "Success is not final, failure is not fatal. It is the courage to continue that counts."
        test_output = "test_kokoro_voice.wav"

        print(f"\nGenerating test voice: {test_text}")
        result = generator.generate_voice(test_text, test_output,
                                         voice='af - Male 1 (American, Deep)',
                                         quality='wav')

        if result:
            print(f"✅ Voice generated successfully: {result}")
        else:
            print("❌ Voice generation failed")
    else:
        print("❌ Kokoro TTS is not installed")
        print("Install with: pip install kokoro-onnx scipy numpy")
