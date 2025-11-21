"""
NeuTTS Voice Cloning Helper
Integrates NeuTTS (open-source voice cloning TTS) with Video Automation Studio

Based on: https://github.com/Neurolingua/NeuTTS
Features:
- Clone any voice with 3-5 second audio sample
- Generate speech with cloned voices
- Auto-chunk long paragraphs (30+ seconds)
- Near 11Labs quality, 100% local & offline
"""

import requests
import json
import time
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class NeuTTSHelper:
    """Helper class for NeuTTS voice cloning and speech generation"""

    def __init__(self, server_url: str = "http://localhost:5000"):
        """
        Initialize NeuTTS helper

        Args:
            server_url: URL of the NeuTTS server (default: http://localhost:5000)
        """
        self.server_url = server_url.rstrip('/')
        self.voices_dir = Path("neutts_voices")
        self.voices_dir.mkdir(exist_ok=True)
        self.cloned_voices = self._load_cloned_voices()

    def _load_cloned_voices(self) -> Dict[str, Dict]:
        """Load list of cloned voices from voices directory"""
        voices = {}
        voices_file = self.voices_dir / "voices.json"

        if voices_file.exists():
            try:
                with open(voices_file, 'r', encoding='utf-8') as f:
                    voices = json.load(f)
            except Exception as e:
                logger.error(f"Error loading voices: {e}")

        return voices

    def _save_cloned_voices(self):
        """Save cloned voices list to JSON"""
        voices_file = self.voices_dir / "voices.json"
        try:
            with open(voices_file, 'w', encoding='utf-8') as f:
                json.dump(self.cloned_voices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving voices: {e}")

    def is_server_running(self) -> bool:
        """Check if NeuTTS server is running"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def clone_voice(self,
                    voice_name: str,
                    audio_sample_path: str,
                    reference_text: str) -> bool:
        """
        Clone a voice from audio sample

        Args:
            voice_name: Name for the cloned voice
            audio_sample_path: Path to 3-5 second audio sample
            reference_text: Text that matches the audio sample

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if server is running
            if not self.is_server_running():
                logger.error("NeuTTS server is not running!")
                return False

            # Prepare the request
            with open(audio_sample_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                data = {
                    'voice_name': voice_name,
                    'reference_text': reference_text
                }

                # Clone voice via API
                response = requests.post(
                    f"{self.server_url}/clone_voice",
                    files=files,
                    data=data,
                    timeout=30
                )

            if response.status_code == 200:
                # Save voice info
                self.cloned_voices[voice_name] = {
                    'reference_text': reference_text,
                    'audio_sample': str(audio_sample_path),
                    'cloned_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self._save_cloned_voices()

                logger.info(f"✓ Voice '{voice_name}' cloned successfully!")
                return True
            else:
                logger.error(f"Clone failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            return False

    def generate_speech(self,
                       text: str,
                       voice_name: str,
                       output_path: str,
                       chunk_size: int = 200) -> bool:
        """
        Generate speech with cloned voice

        Args:
            text: Text to convert to speech
            voice_name: Name of cloned voice to use
            output_path: Path to save output audio
            chunk_size: Max characters per chunk (default: 200)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if server is running
            if not self.is_server_running():
                logger.error("NeuTTS server is not running!")
                return False

            # Check if voice exists
            if voice_name not in self.cloned_voices:
                logger.error(f"Voice '{voice_name}' not found!")
                return False

            # Split text into chunks if too long
            chunks = self._split_text_into_chunks(text, chunk_size)

            if len(chunks) > 1:
                logger.info(f"Text split into {len(chunks)} chunks for processing")

            # Generate audio for each chunk
            chunk_paths = []
            for i, chunk in enumerate(chunks, 1):
                chunk_output = f"{output_path}.chunk_{i}.wav"

                data = {
                    'text': chunk,
                    'voice_name': voice_name
                }

                response = requests.post(
                    f"{self.server_url}/generate",
                    json=data,
                    timeout=60
                )

                if response.status_code == 200:
                    # Save audio chunk
                    with open(chunk_output, 'wb') as f:
                        f.write(response.content)
                    chunk_paths.append(chunk_output)
                    logger.info(f"✓ Generated chunk {i}/{len(chunks)}")
                else:
                    logger.error(f"Failed to generate chunk {i}: {response.text}")
                    return False

            # Merge chunks if multiple
            if len(chunk_paths) > 1:
                self._merge_audio_chunks(chunk_paths, output_path)
                # Clean up chunk files
                for chunk_path in chunk_paths:
                    Path(chunk_path).unlink(missing_ok=True)
            elif len(chunk_paths) == 1:
                # Single chunk, just rename
                Path(chunk_paths[0]).rename(output_path)

            logger.info(f"✓ Speech generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return False

    def _split_text_into_chunks(self, text: str, max_chars: int = 200) -> List[str]:
        """
        Split text into chunks at sentence boundaries

        Args:
            text: Text to split
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        # Split by sentences
        import re
        sentences = re.split(r'([.!?]+\s+)', text)

        chunks = []
        current_chunk = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + punctuation

            # If adding this sentence exceeds max, start new chunk
            if len(current_chunk) + len(full_sentence) > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = full_sentence
            else:
                current_chunk += full_sentence

        # Add remaining text
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def _merge_audio_chunks(self, chunk_paths: List[str], output_path: str):
        """
        Merge multiple audio chunks into single file

        Args:
            chunk_paths: List of audio chunk file paths
            output_path: Path to save merged audio
        """
        try:
            from pydub import AudioSegment

            # Load and concatenate all chunks
            combined = AudioSegment.empty()
            for chunk_path in chunk_paths:
                audio = AudioSegment.from_wav(chunk_path)
                combined += audio

            # Export merged audio
            combined.export(output_path, format="wav")
            logger.info(f"✓ Merged {len(chunk_paths)} chunks into {output_path}")

        except ImportError:
            logger.error("pydub not installed! Run: pip install pydub")
            # Fallback: use first chunk only
            if chunk_paths:
                Path(chunk_paths[0]).rename(output_path)
        except Exception as e:
            logger.error(f"Error merging chunks: {e}")
            # Fallback: use first chunk only
            if chunk_paths:
                Path(chunk_paths[0]).rename(output_path)

    def get_available_voices(self) -> List[str]:
        """Get list of all cloned voices"""
        return list(self.cloned_voices.keys())

    def delete_voice(self, voice_name: str) -> bool:
        """Delete a cloned voice"""
        if voice_name in self.cloned_voices:
            del self.cloned_voices[voice_name]
            self._save_cloned_voices()
            logger.info(f"✓ Deleted voice: {voice_name}")
            return True
        return False


# Convenience functions for easy integration
def clone_voice(voice_name: str, audio_sample: str, reference_text: str) -> bool:
    """Clone a voice (convenience function)"""
    helper = NeuTTSHelper()
    return helper.clone_voice(voice_name, audio_sample, reference_text)


def generate_speech(text: str, voice_name: str, output_file: str) -> bool:
    """Generate speech with cloned voice (convenience function)"""
    helper = NeuTTSHelper()
    return helper.generate_speech(text, voice_name, output_file)


def get_available_voices() -> List[str]:
    """Get list of cloned voices (convenience function)"""
    helper = NeuTTSHelper()
    return helper.get_available_voices()


if __name__ == "__main__":
    # Test if server is running
    helper = NeuTTSHelper()
    if helper.is_server_running():
        print("✓ NeuTTS server is running!")
        print(f"Available voices: {helper.get_available_voices()}")
    else:
        print("✗ NeuTTS server is not running")
        print("Please start the server first (run_new_tts.bat)")
