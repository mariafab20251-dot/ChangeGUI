"""
NeuTTS Integration Helper Module
Provides voice cloning and TTS generation using NeuTTS API
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading
import queue


class NeuTTSHelper:
    """Helper class for NeuTTS voice cloning and speech generation"""

    def __init__(self, server_url: str = "http://localhost:5000"):
        """
        Initialize NeuTTS helper

        Args:
            server_url: Base URL of NeuTTS server (default: http://localhost:5000)
        """
        self.server_url = server_url.rstrip('/')
        self.voices_library = {}  # Store cloned voices
        self.status = "disconnected"

    def check_server_status(self) -> Tuple[bool, str]:
        """
        Check if NeuTTS server is running

        Returns:
            Tuple of (is_running: bool, status_message: str)
        """
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=3)
            if response.status_code == 200:
                self.status = "connected"
                return True, "✓ NeuTTS Server Connected"
            else:
                self.status = "error"
                return False, f"⚠ Server Error: {response.status_code}"
        except requests.ConnectionError:
            self.status = "disconnected"
            return False, "✗ Server Not Running - Start run_new_tts.bat"
        except requests.Timeout:
            self.status = "timeout"
            return False, "⚠ Server Timeout"
        except Exception as e:
            self.status = "error"
            return False, f"✗ Error: {str(e)}"

    def clone_voice(self,
                   voice_name: str,
                   audio_file_path: str,
                   reference_text: str,
                   language: str = "en") -> Tuple[bool, str]:
        """
        Clone a voice from audio sample

        Args:
            voice_name: Name to identify this cloned voice
            audio_file_path: Path to audio sample file (WAV/MP3)
            reference_text: Text that matches the audio sample
            language: Language code (en, es, fr, etc.)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if file exists
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                return False, f"Audio file not found: {audio_file_path}"

            # Prepare multipart form data
            files = {
                'audio': open(audio_file_path, 'rb')
            }
            data = {
                'voice_name': voice_name,
                'reference_text': reference_text,
                'language': language
            }

            # Send clone request
            response = requests.post(
                f"{self.server_url}/api/clone",
                files=files,
                data=data,
                timeout=60
            )

            files['audio'].close()

            if response.status_code == 200:
                result = response.json()
                voice_id = result.get('voice_id', voice_name)

                # Store in library
                self.voices_library[voice_name] = {
                    'voice_id': voice_id,
                    'language': language,
                    'reference_text': reference_text,
                    'audio_file': audio_file_path,
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }

                return True, f"✓ Voice '{voice_name}' cloned successfully!"
            else:
                error_msg = response.json().get('error', 'Unknown error')
                return False, f"✗ Clone failed: {error_msg}"

        except Exception as e:
            return False, f"✗ Exception: {str(e)}"

    def generate_speech(self,
                       text: str,
                       voice_name: str,
                       output_path: str,
                       speed: float = 1.0,
                       pitch: float = 1.0) -> Tuple[bool, str]:
        """
        Generate speech from text using cloned voice

        Args:
            text: Text to convert to speech
            voice_name: Name of cloned voice to use
            output_path: Where to save the audio file
            speed: Speech speed multiplier (0.5 - 2.0)
            pitch: Pitch adjustment (0.5 - 2.0)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if voice exists
            if voice_name not in self.voices_library:
                return False, f"Voice '{voice_name}' not found in library"

            voice_info = self.voices_library[voice_name]

            # Prepare request
            data = {
                'text': text,
                'voice_id': voice_info['voice_id'],
                'speed': speed,
                'pitch': pitch
            }

            # Send generation request
            response = requests.post(
                f"{self.server_url}/api/generate",
                json=data,
                timeout=120
            )

            if response.status_code == 200:
                # Save audio to file
                with open(output_path, 'wb') as f:
                    f.write(response.content)

                return True, f"✓ Speech generated: {output_path}"
            else:
                error_msg = response.json().get('error', 'Unknown error')
                return False, f"✗ Generation failed: {error_msg}"

        except Exception as e:
            return False, f"✗ Exception: {str(e)}"

    def generate_speech_chunked(self,
                               text: str,
                               voice_name: str,
                               output_folder: str,
                               max_chunk_length: int = 500,
                               speed: float = 1.0,
                               pitch: float = 1.0) -> Tuple[bool, List[str], str]:
        """
        Generate speech for long text by chunking into smaller parts

        Args:
            text: Long text to convert
            voice_name: Name of cloned voice
            output_folder: Folder to save audio chunks
            max_chunk_length: Maximum characters per chunk
            speed: Speech speed multiplier
            pitch: Pitch adjustment

        Returns:
            Tuple of (success: bool, audio_files: List[str], message: str)
        """
        try:
            # Create output folder
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

            # Split text into chunks (by sentences)
            chunks = self._chunk_text(text, max_chunk_length)

            audio_files = []

            for i, chunk in enumerate(chunks):
                chunk_file = output_path / f"chunk_{i+1:03d}.wav"

                success, msg = self.generate_speech(
                    text=chunk,
                    voice_name=voice_name,
                    output_path=str(chunk_file),
                    speed=speed,
                    pitch=pitch
                )

                if not success:
                    return False, audio_files, f"Failed at chunk {i+1}: {msg}"

                audio_files.append(str(chunk_file))

            return True, audio_files, f"✓ Generated {len(chunks)} audio chunks"

        except Exception as e:
            return False, [], f"✗ Exception: {str(e)}"

    def _chunk_text(self, text: str, max_length: int) -> List[str]:
        """
        Split text into chunks at sentence boundaries

        Args:
            text: Text to split
            max_length: Maximum chunk length

        Returns:
            List of text chunks
        """
        # Split by sentences
        sentences = text.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence exceeds limit, save current chunk
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_available_voices(self) -> Dict[str, dict]:
        """
        Get all cloned voices in library

        Returns:
            Dictionary of voice_name -> voice_info
        """
        return self.voices_library.copy()

    def save_voice_library(self, filepath: str = "neutts_voices.json"):
        """
        Save voice library to JSON file

        Args:
            filepath: Path to save library
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.voices_library, f, indent=2)
            return True, f"✓ Library saved to {filepath}"
        except Exception as e:
            return False, f"✗ Save failed: {str(e)}"

    def load_voice_library(self, filepath: str = "neutts_voices.json"):
        """
        Load voice library from JSON file

        Args:
            filepath: Path to library file
        """
        try:
            if Path(filepath).exists():
                with open(filepath, 'r') as f:
                    self.voices_library = json.load(f)
                return True, f"✓ Loaded {len(self.voices_library)} voices"
            else:
                return False, f"✗ Library file not found: {filepath}"
        except Exception as e:
            return False, f"✗ Load failed: {str(e)}"

    def delete_voice(self, voice_name: str) -> Tuple[bool, str]:
        """
        Remove a voice from library

        Args:
            voice_name: Name of voice to delete

        Returns:
            Tuple of (success: bool, message: str)
        """
        if voice_name in self.voices_library:
            del self.voices_library[voice_name]
            return True, f"✓ Voice '{voice_name}' deleted"
        else:
            return False, f"✗ Voice '{voice_name}' not found"

    def test_voice(self, voice_name: str, test_text: str = None) -> Tuple[bool, str, str]:
        """
        Generate a test audio with the voice

        Args:
            voice_name: Name of voice to test
            test_text: Optional custom test text

        Returns:
            Tuple of (success: bool, audio_path: str, message: str)
        """
        if not test_text:
            test_text = "Hello! This is a test of my cloned voice. How does it sound?"

        # Generate in temp folder
        temp_folder = Path("temp_neutts_tests")
        temp_folder.mkdir(exist_ok=True)

        output_file = temp_folder / f"test_{voice_name}_{int(time.time())}.wav"

        success, msg = self.generate_speech(
            text=test_text,
            voice_name=voice_name,
            output_path=str(output_file)
        )

        if success:
            return True, str(output_file), msg
        else:
            return False, "", msg


# Async wrapper for GUI integration
class AsyncNeuTTSHelper:
    """Thread-safe async wrapper for NeuTTS operations"""

    def __init__(self, server_url: str = "http://localhost:5000"):
        self.helper = NeuTTSHelper(server_url)
        self.result_queue = queue.Queue()

    def check_status_async(self, callback):
        """Check server status in background thread"""
        def worker():
            result = self.helper.check_server_status()
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def clone_voice_async(self, voice_name, audio_file, ref_text, language, callback):
        """Clone voice in background thread"""
        def worker():
            result = self.helper.clone_voice(voice_name, audio_file, ref_text, language)
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def generate_speech_async(self, text, voice_name, output_path, speed, pitch, callback):
        """Generate speech in background thread"""
        def worker():
            result = self.helper.generate_speech(text, voice_name, output_path, speed, pitch)
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def test_voice_async(self, voice_name, test_text, callback):
        """Test voice in background thread"""
        def worker():
            result = self.helper.test_voice(voice_name, test_text)
            callback(result)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


if __name__ == "__main__":
    # Test the helper
    helper = NeuTTSHelper()

    print("Checking NeuTTS server status...")
    is_running, status = helper.check_server_status()
    print(f"Status: {status}")

    if is_running:
        print("\nServer is ready for voice cloning!")
    else:
        print("\nPlease start NeuTTS server: run_new_tts.bat")
