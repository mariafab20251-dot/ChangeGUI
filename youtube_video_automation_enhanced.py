"""
Video Quote Overlay Automation - ENHANCED with Advanced Effects
Compatible with MoviePy 2.x
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional
import json
from datetime import datetime
import numpy as np

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

try:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
    from moviepy.video.fx import Resize, FadeIn
    from moviepy.audio.fx import MultiplyVolume, AudioLoop
except ImportError:
    from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
    from moviepy.video.fx.resize import resize as Resize
    from moviepy.audio.fx.volumex import volumex as MultiplyVolume
    AudioLoop = None
    FadeIn = None

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Text-to-Speech - Using edge-tts for natural, human-like voices
try:
    import edge_tts
    import asyncio
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("[WARNING] edge-tts not available - TTS voiceover generation disabled")
    print("  Install with: pip install edge-tts")


def set_volume(clip, volume):
    """Compatible volume adjustment for MoviePy 1.x and 2.x"""
    try:
        return clip.with_effects([MultiplyVolume(volume)])
    except:
        return clip.volumex(volume)


def set_duration(clip, duration):
    """Compatible duration setting for MoviePy 1.x and 2.x"""
    try:
        return clip.with_duration(duration)
    except:
        return clip.set_duration(duration)


def subclip(clip, start, end):
    """Compatible subclipping for MoviePy 1.x and 2.x"""
    try:
        return clip.subclipped(start, end)
    except:
        return clip.subclip(start, end)


def set_audio(clip, audio):
    """Compatible audio setting for MoviePy 1.x and 2.x"""
    try:
        return clip.with_audio(audio)
    except:
        return clip.set_audio(audio)


def set_position(clip, position):
    """Compatible position setting for MoviePy 1.x and 2.x"""
    try:
        return clip.with_position(position)
    except:
        return clip.set_position(position)


class VideoEffects:
    """Advanced video effects module"""

    @staticmethod
    def apply_color_grade(frame, grade_type='warm', intensity=0.5):
        """Apply color grading to frame"""
        # Work on a copy to avoid modifying read-only arrays
        frame = frame.copy()
        if grade_type == 'warm':
            frame[:,:,0] = np.clip(frame[:,:,0] * (1 + intensity * 0.2), 0, 255)
            frame[:,:,2] = np.clip(frame[:,:,2] * (1 - intensity * 0.1), 0, 255)
        elif grade_type == 'cold':
            frame[:,:,2] = np.clip(frame[:,:,2] * (1 + intensity * 0.2), 0, 255)
            frame[:,:,0] = np.clip(frame[:,:,0] * (1 - intensity * 0.1), 0, 255)
        elif grade_type == 'cinematic':
            frame = frame * 0.95
            frame[:,:,1] = np.clip(frame[:,:,1] * 1.05, 0, 255)
        elif grade_type == 'vintage':
            frame[:,:,0] = np.clip(frame[:,:,0] * 1.1, 0, 255)
            frame[:,:,1] = np.clip(frame[:,:,1] * 0.95, 0, 255)
            frame[:,:,2] = np.clip(frame[:,:,2] * 0.85, 0, 255)
        return frame.astype('uint8')

    @staticmethod
    def apply_vignette(frame, intensity=0.4):
        """Apply vignette darkening"""
        # Work on a copy to avoid modifying read-only arrays
        frame = frame.copy()
        h, w = frame.shape[:2]
        y, x = np.ogrid[:h, :w]
        cx, cy = w / 2, h / 2
        max_dist = np.sqrt(cx**2 + cy**2)
        distance = np.sqrt((x - cx)**2 + (y - cy)**2)
        vignette = 1 - (distance / max_dist * intensity)
        vignette = np.clip(vignette, 0, 1)
        return (frame * vignette[:,:,np.newaxis]).astype('uint8')

    @staticmethod
    def apply_film_grain(frame, intensity=0.15):
        """Apply film grain overlay"""
        # Work on a copy to avoid modifying read-only arrays
        frame = frame.copy()
        noise = np.random.normal(0, intensity * 255, frame.shape)
        return np.clip(frame + noise, 0, 255).astype('uint8')


    @staticmethod
    def apply_selective_blur(get_frame, t):
        """Apply blur to a specific region (for hiding watermarks/logos)"""
        frame = get_frame(t)
        
        # Get blur settings
        if not hasattr(apply_selective_blur, 'settings'):
            return frame
            
        settings = apply_selective_blur.settings
        
        if not settings.get('blur_watermark_enabled', False):
            return frame
        
        try:
            from PIL import Image, ImageFilter
            import numpy as np
            
            # Get blur region
            x = settings.get('blur_x', 50)
            y = settings.get('blur_y', 700)
            width = settings.get('blur_width', 200)
            height = settings.get('blur_height', 50)
            intensity = settings.get('blur_intensity', 15)
            
            # Convert frame to PIL Image
            img = Image.fromarray(frame.astype('uint8'), 'RGB')
            
            # Extract region to blur
            region = img.crop((x, y, x + width, y + height))
            
            # Apply blur
            blurred_region = region.filter(ImageFilter.GaussianBlur(radius=intensity))
            
            # Paste back
            img.paste(blurred_region, (x, y))
            
            # Convert back to numpy array
            return np.array(img)
        except Exception as e:
            print(f"Blur error: {e}")
            return frame

    @staticmethod
    def apply_background_dim(frame, intensity=0.25):
        """Dim the background"""
        # Work on a copy to avoid modifying read-only arrays
        frame = frame.copy()
        return (frame * (1 - intensity)).astype('uint8')

    @staticmethod
    def apply_gradient_overlay(frame, gradient_type='top_to_bottom', intensity=0.3):
        """Apply gradient overlay effect"""
        frame = frame.copy()
        h, w = frame.shape[:2]

        # Create gradient
        if gradient_type == 'top_to_bottom':
            gradient = np.linspace(1, 1 - intensity, h)[:, np.newaxis]
            gradient = np.repeat(gradient, w, axis=1)
        elif gradient_type == 'bottom_to_top':
            gradient = np.linspace(1 - intensity, 1, h)[:, np.newaxis]
            gradient = np.repeat(gradient, w, axis=1)
        elif gradient_type == 'left_to_right':
            gradient = np.linspace(1, 1 - intensity, w)[np.newaxis, :]
            gradient = np.repeat(gradient, h, axis=0)
        elif gradient_type == 'right_to_left':
            gradient = np.linspace(1 - intensity, 1, w)[np.newaxis, :]
            gradient = np.repeat(gradient, h, axis=0)
        elif gradient_type == 'radial':
            y, x = np.ogrid[:h, :w]
            cx, cy = w / 2, h / 2
            max_dist = np.sqrt(cx**2 + cy**2)
            distance = np.sqrt((x - cx)**2 + (y - cy)**2)
            gradient = 1 - (distance / max_dist * intensity)
        else:
            gradient = np.ones((h, w))

        gradient = np.clip(gradient, 0, 1)
        return (frame * gradient[:, :, np.newaxis]).astype('uint8')


class TransitionEffects:
    """Professional transition effects for video intro/outro"""

    @staticmethod
    def apply_fade_transition(clip, fade_in_duration=0, fade_out_duration=0):
        """Apply fade in/out transitions"""
        if fade_in_duration > 0:
            try:
                clip = clip.with_effects([FadeIn(fade_in_duration)])
            except:
                try:
                    clip = clip.fadein(fade_in_duration)
                except:
                    pass

        if fade_out_duration > 0:
            try:
                from moviepy.video.fx import FadeOut
                clip = clip.with_effects([FadeOut(fade_out_duration)])
            except:
                try:
                    clip = clip.fadeout(fade_out_duration)
                except:
                    pass

        return clip

    @staticmethod
    def create_zoom_transition(clip, zoom_in=True, duration=1.0, zoom_scale=1.3):
        """Create zoom in/out transition effect"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def zoom_effect(get_frame, t):
            frame = get_frame(t)

            if zoom_in:
                # Zoom from scale to 1.0
                progress = min(t / duration, 1.0)
                current_scale = zoom_scale - (zoom_scale - 1.0) * progress
            else:
                # Zoom from 1.0 to scale
                progress = max((t - (clip.duration - duration)) / duration, 0.0)
                current_scale = 1.0 + (zoom_scale - 1.0) * progress

            if abs(current_scale - 1.0) > 0.01:  # Only apply if zoom needed
                h, w = frame.shape[:2]
                new_h, new_w = int(h * current_scale), int(w * current_scale)

                from PIL import Image as PILImage
                pil_frame = PILImage.fromarray(frame)
                pil_frame = pil_frame.resize((new_w, new_h), PILImage.LANCZOS)

                # Crop to original size (center crop)
                crop_x = (new_w - w) // 2
                crop_y = (new_h - h) // 2
                pil_frame = pil_frame.crop((crop_x, crop_y, crop_x + w, crop_y + h))

                return np.array(pil_frame).copy()

            return frame

        try:
            return clip.transform(zoom_effect)
        except:
            return clip.fl(zoom_effect)

    @staticmethod
    def create_blur_transition(clip, blur_in=True, duration=0.5, max_blur=15):
        """Create blur in/out transition"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def blur_effect(get_frame, t):
            frame = get_frame(t)

            if blur_in:
                # Blur from max to 0
                progress = min(t / duration, 1.0)
                blur_amount = int(max_blur * (1 - progress))
            else:
                # Blur from 0 to max
                progress = max((t - (clip.duration - duration)) / duration, 0.0)
                blur_amount = int(max_blur * progress)

            if blur_amount > 0:
                pil_img = Image.fromarray(frame)
                pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=blur_amount))
                return np.array(pil_img).copy()

            return frame

        try:
            return clip.image_transform(blur_effect)
        except:
            return clip.fl_image(blur_effect)

    @staticmethod
    def create_slide_transition(clip, direction='left', in_transition=True, duration=0.8):
        """Create slide in/out transition (video slides into frame)"""
        def slide_position(t):
            w, h = clip.size

            if in_transition:
                # Slide in
                progress = min(t / duration, 1.0)
                # Ease out cubic
                progress = 1 - (1 - progress) ** 3
            else:
                # Slide out
                progress = max((t - (clip.duration - duration)) / duration, 0.0)
                # Ease in cubic
                progress = progress ** 3

            if direction == 'left':
                offset = w * (1 - progress) if in_transition else -w * progress
                return (int(offset), 0)
            elif direction == 'right':
                offset = -w * (1 - progress) if in_transition else w * progress
                return (int(offset), 0)
            elif direction == 'up':
                offset = h * (1 - progress) if in_transition else -h * progress
                return (0, int(offset))
            elif direction == 'down':
                offset = -h * (1 - progress) if in_transition else h * progress
                return (0, int(offset))

            return (0, 0)

        try:
            return clip.with_position(slide_position)
        except:
            return clip.set_position(slide_position)

    @staticmethod
    def create_wipe_transition(clip, direction='right', in_transition=True, duration=0.8):
        """Create wipe transition (reveals video gradually)"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def wipe_mask(t):
            w, h = clip.size
            mask = np.zeros((h, w), dtype=np.uint8)

            if in_transition:
                progress = min(t / duration, 1.0)
            else:
                progress = 1.0 - max((t - (clip.duration - duration)) / duration, 0.0)

            if direction == 'right':
                reveal_x = int(w * progress)
                mask[:, :reveal_x] = 255
            elif direction == 'left':
                reveal_x = int(w * (1 - progress))
                mask[:, reveal_x:] = 255
            elif direction == 'down':
                reveal_y = int(h * progress)
                mask[:reveal_y, :] = 255
            elif direction == 'up':
                reveal_y = int(h * (1 - progress))
                mask[reveal_y:, :] = 255

            return mask

        mask_clip = VideoClip(wipe_mask, duration=clip.duration, is_mask=True)
        try:
            mask_clip = mask_clip.with_fps(clip.fps if hasattr(clip, 'fps') else 30)
            return clip.with_mask(mask_clip)
        except:
            mask_clip = mask_clip.set_fps(clip.fps if hasattr(clip, 'fps') else 30)
            return clip.set_mask(mask_clip)

    @staticmethod
    def create_glitch_transition(clip, glitch_start=True, duration=0.5, intensity=0.5):
        """Create digital glitch transition effect"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def glitch_effect(get_frame, t):
            frame = get_frame(t)

            if glitch_start:
                if t > duration:
                    return frame
                progress = t / duration
            else:
                if t < (clip.duration - duration):
                    return frame
                progress = (t - (clip.duration - duration)) / duration

            # Apply glitch only during transition
            glitch_amount = intensity * (1 - progress) if glitch_start else intensity * progress

            if glitch_amount > 0.1:
                frame = frame.copy()
                h, w = frame.shape[:2]

                # RGB channel shift
                shift = int(w * 0.02 * glitch_amount)
                if shift > 0:
                    frame[:, shift:, 0] = frame[:, :-shift, 0]
                    frame[:, :-shift, 2] = frame[:, shift:, 2]

                # Random horizontal slices
                if np.random.random() < glitch_amount:
                    num_slices = int(5 * glitch_amount)
                    for _ in range(num_slices):
                        y1 = np.random.randint(0, h - 10)
                        y2 = y1 + np.random.randint(5, 30)
                        offset = np.random.randint(-int(w * 0.1), int(w * 0.1))
                        if offset > 0:
                            frame[y1:y2, offset:] = frame[y1:y2, :-offset]
                        elif offset < 0:
                            frame[y1:y2, :offset] = frame[y1:y2, -offset:]

            return frame

        try:
            return clip.image_transform(glitch_effect)
        except:
            return clip.fl_image(glitch_effect)

    @staticmethod
    def create_cinematic_bars(clip, fade_in=True, duration=0.8, bar_height_percent=10):
        """Create cinematic letterbox bars (black bars top/bottom)"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def bars_frame(t):
            w, h = clip.size
            bar_height = int(h * bar_height_percent / 100)

            # Create bars
            bars = np.zeros((h, w, 3), dtype=np.uint8)

            if fade_in:
                progress = min(t / duration, 1.0)
                current_height = int(bar_height * progress)
            else:
                current_height = bar_height

            # Top and bottom bars
            bars[:current_height, :] = 0
            bars[-current_height:, :] = 0

            return bars

        bars_clip = VideoClip(bars_frame, duration=clip.duration)
        try:
            bars_clip = bars_clip.with_fps(clip.fps if hasattr(clip, 'fps') else 30)
        except:
            bars_clip = bars_clip.set_fps(clip.fps if hasattr(clip, 'fps') else 30)

        # Composite bars over video
        try:
            from moviepy import CompositeVideoClip
        except:
            from moviepy.editor import CompositeVideoClip

        return CompositeVideoClip([clip, bars_clip])


class LightLeaksEffects:
    """Cinematic light leaks and lens flare effects"""

    @staticmethod
    def create_light_leak(width, height, duration, fps, color='warm', intensity=0.6,
                         start_time=0, leak_duration=None, direction='top_right'):
        """
        Create light leak overlay effect

        Args:
            color: 'warm' (orange/yellow), 'cold' (blue/cyan), 'pink', 'purple', 'rainbow'
            direction: 'top_right', 'top_left', 'bottom_right', 'bottom_left', 'center'
        """
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        if leak_duration is None:
            leak_duration = duration

        # Color palettes
        colors = {
            'warm': [(255, 200, 100), (255, 150, 50), (255, 100, 0)],
            'cold': [(100, 200, 255), (50, 150, 255), (0, 100, 255)],
            'pink': [(255, 100, 150), (255, 150, 200), (255, 50, 100)],
            'purple': [(200, 100, 255), (150, 50, 255), (100, 0, 200)],
            'rainbow': [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130)]
        }

        color_palette = colors.get(color, colors['warm'])

        def make_frame(t):
            # Create RGBA frame
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Calculate progress (0 to 1 and back)
            relative_t = t - start_time
            if relative_t < 0 or relative_t > leak_duration:
                return np.array(img).copy()

            progress = relative_t / leak_duration
            # Fade in and out
            if progress < 0.3:
                alpha = progress / 0.3
            elif progress > 0.7:
                alpha = (1.0 - progress) / 0.3
            else:
                alpha = 1.0

            # Position based on direction
            positions = {
                'top_right': (width * 0.7, -height * 0.2),
                'top_left': (-width * 0.2, -height * 0.2),
                'bottom_right': (width * 0.7, height * 0.7),
                'bottom_left': (-width * 0.2, height * 0.7),
                'center': (width * 0.3, height * 0.3)
            }

            pos_x, pos_y = positions.get(direction, positions['top_right'])

            # Draw multiple overlapping ellipses for organic look
            for i, color_rgb in enumerate(color_palette):
                offset_x = i * 50 + int(progress * 100)
                offset_y = i * 30

                size_w = int(width * 0.6 * (1 + i * 0.1))
                size_h = int(height * 0.8 * (1 + i * 0.1))

                bbox = [
                    int(pos_x + offset_x),
                    int(pos_y + offset_y),
                    int(pos_x + offset_x + size_w),
                    int(pos_y + offset_y + size_h)
                ]

                # Calculate alpha for this layer
                layer_alpha = int(255 * intensity * alpha * (1 - i * 0.2))

                draw.ellipse(bbox, fill=color_rgb + (layer_alpha,))

            # Apply gaussian blur for soft glow
            img = img.filter(ImageFilter.GaussianBlur(radius=50))

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip

    @staticmethod
    def create_lens_flare(width, height, duration, fps, intensity=0.5,
                         start_time=0, flare_duration=2.0, position='center'):
        """Create lens flare effect"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            relative_t = t - start_time
            if relative_t < 0 or relative_t > flare_duration:
                return np.array(img).copy()

            progress = relative_t / flare_duration
            # Quick flash
            if progress < 0.2:
                alpha = progress / 0.2
            else:
                alpha = max(0, 1.0 - (progress - 0.2) / 0.8)

            # Position
            if position == 'center':
                center_x, center_y = width // 2, height // 2
            elif position == 'top':
                center_x, center_y = width // 2, height // 4
            else:
                center_x, center_y = width // 2, height // 2

            # Main flare
            flare_size = int(min(width, height) * 0.3)
            bbox = [
                center_x - flare_size,
                center_y - flare_size,
                center_x + flare_size,
                center_y + flare_size
            ]

            flare_alpha = int(255 * intensity * alpha)
            draw.ellipse(bbox, fill=(255, 255, 255, flare_alpha))

            # Additional smaller flares
            for i in range(3):
                offset = (i + 1) * 100
                size = flare_size // (i + 2)
                bbox = [
                    center_x + offset - size,
                    center_y - size,
                    center_x + offset + size,
                    center_y + size
                ]
                draw.ellipse(bbox, fill=(255, 200, 100, flare_alpha // 2))

            img = img.filter(ImageFilter.GaussianBlur(radius=30))

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip

    @staticmethod
    def create_film_burn(width, height, duration, fps, start_time=0, burn_duration=1.5):
        """Create film burn effect (vintage film look)"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            relative_t = t - start_time
            if relative_t < 0 or relative_t > burn_duration:
                return np.array(img).copy()

            progress = relative_t / burn_duration

            # Burn effect spreads from corner
            spread = progress * max(width, height) * 1.5

            # Create irregular burn shape
            np.random.seed(int(progress * 100))
            num_circles = int(20 * progress)

            for _ in range(num_circles):
                angle = np.random.uniform(0, np.pi / 2)
                dist = np.random.uniform(0, spread)

                x = width + int(dist * np.cos(angle))
                y = height + int(dist * np.sin(angle))

                size = np.random.randint(50, 200)

                # Orange/yellow burn colors
                colors = [(255, 200, 0), (255, 150, 0), (255, 100, 0), (200, 50, 0)]
                color = colors[int(np.random.random() * len(colors))]

                alpha = int(200 * progress)

                bbox = [x - size, y - size, x + size, y + size]
                draw.ellipse(bbox, fill=color + (alpha,))

            img = img.filter(ImageFilter.GaussianBlur(radius=20))

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip


class ParticleEffects:
    """Particle effects for viral videos (glitter, stars, hearts, confetti)"""

    @staticmethod
    def create_glitter(width, height, duration, fps, intensity=0.5):
        """Create glitter/sparkle particle effect"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        # Number of particles based on intensity
        num_particles = int(20 * intensity)

        # Generate random particle positions and timing
        np.random.seed(42)
        particles = []
        for _ in range(num_particles):
            particles.append({
                'x': np.random.randint(0, width),
                'y': np.random.randint(0, height),
                'size': np.random.randint(3, 8),
                'phase': np.random.uniform(0, 2 * np.pi),
                'speed': np.random.uniform(0.5, 2.0)
            })

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            for particle in particles:
                # Twinkling effect using sine wave
                alpha = abs(np.sin(t * particle['speed'] + particle['phase']))

                # Add some vertical drift
                y_offset = int(t * 10) % height
                y = (particle['y'] + y_offset) % height

                # Draw sparkle (small cross shape)
                size = particle['size']
                x = particle['x']

                particle_alpha = int(255 * alpha * intensity)
                color = (255, 255, 255, particle_alpha)

                # Center dot
                draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=color)

                # Sparkle rays
                ray_length = size * 2
                draw.line([x-ray_length, y, x+ray_length, y], fill=color, width=1)
                draw.line([x, y-ray_length, x, y+ray_length], fill=color, width=1)

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip

    @staticmethod
    def create_stars(width, height, duration, fps):
        """Create floating star particles"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        num_stars = 15

        np.random.seed(43)
        stars = []
        for _ in range(num_stars):
            stars.append({
                'x': np.random.randint(0, width),
                'y': np.random.randint(0, height),
                'size': np.random.randint(15, 30),
                'speed_x': np.random.uniform(-20, 20),
                'speed_y': np.random.uniform(-30, -10),  # Float upward
                'phase': np.random.uniform(0, 2 * np.pi),
                'rotation_speed': np.random.uniform(1, 3)
            })

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            for star in stars:
                # Moving position
                x = (star['x'] + int(star['speed_x'] * t)) % width
                y = (star['y'] + int(star['speed_y'] * t)) % height

                # Fade in/out
                alpha = abs(np.sin(t * 0.5 + star['phase']))

                size = star['size']
                star_alpha = int(200 * alpha)

                # Draw 5-pointed star using emoji-like shape
                # Yellow/gold color
                color = (255, 215, 0, star_alpha)

                # Simple star using triangles
                points = []
                for i in range(5):
                    angle = i * 4 * np.pi / 5 - np.pi/2 + (t * star['rotation_speed'])
                    points.append((x + int(size * np.cos(angle)),
                                 y + int(size * np.sin(angle))))

                # Draw star outline
                for i in range(5):
                    j = (i + 2) % 5
                    draw.line([points[i], points[j]], fill=color, width=2)

                # Fill center
                center_size = size // 3
                draw.ellipse([x-center_size, y-center_size, x+center_size, y+center_size],
                           fill=color)

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip

    @staticmethod
    def create_hearts(width, height, duration, fps):
        """Create floating heart particles"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        num_hearts = 12

        np.random.seed(44)
        hearts = []
        for _ in range(num_hearts):
            hearts.append({
                'x': np.random.randint(0, width),
                'y': height + np.random.randint(0, 200),  # Start below screen
                'size': np.random.randint(20, 40),
                'speed_y': np.random.uniform(30, 60),  # Float upward
                'speed_x': np.random.uniform(-10, 10),  # Slight horizontal drift
                'phase': np.random.uniform(0, 2 * np.pi),
                'sway': np.random.uniform(10, 30)
            })

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            for heart in hearts:
                # Moving position with sway
                x = heart['x'] + int(heart['speed_x'] * t) + int(heart['sway'] * np.sin(t + heart['phase']))
                y = (heart['y'] - int(heart['speed_y'] * t)) % (height + 200)

                # Skip if off screen
                if y > height or y < -100:
                    continue

                # Fade based on position
                if y < 100:
                    alpha = y / 100
                elif y > height - 100:
                    alpha = (height - y) / 100
                else:
                    alpha = 1.0

                size = heart['size']
                heart_alpha = int(220 * alpha)

                # Pink/red hearts
                colors = [(255, 20, 147, heart_alpha), (255, 105, 180, heart_alpha)]
                color = colors[int(t * 2) % 2]

                # Draw heart shape using two circles and triangle
                half_size = size // 2
                draw.ellipse([x-half_size, y-half_size//2, x, y+half_size//2], fill=color)
                draw.ellipse([x, y-half_size//2, x+half_size, y+half_size//2], fill=color)
                draw.polygon([x-half_size, y, x+half_size, y, x, y+size], fill=color)

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip

    @staticmethod
    def create_confetti(width, height, duration, fps):
        """Create falling confetti particles"""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        num_confetti = 30

        np.random.seed(45)
        confetti_pieces = []
        for _ in range(num_confetti):
            confetti_pieces.append({
                'x': np.random.randint(0, width),
                'y': -np.random.randint(0, 300),  # Start above screen
                'size': np.random.randint(5, 15),
                'speed_y': np.random.uniform(100, 200),  # Fall speed
                'speed_x': np.random.uniform(-30, 30),
                'rotation': np.random.uniform(0, 2 * np.pi),
                'rotation_speed': np.random.uniform(2, 5),
                'color': tuple(np.random.randint(0, 255, 3).tolist() + [220])
            })

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            for confetti in confetti_pieces:
                # Moving position
                x = (confetti['x'] + int(confetti['speed_x'] * t)) % width
                y = (confetti['y'] + int(confetti['speed_y'] * t)) % (height + 300)

                # Skip if way off screen
                if y < -100 or y > height + 100:
                    continue

                size = confetti['size']
                rotation = confetti['rotation'] + t * confetti['rotation_speed']

                # Draw rectangle with rotation effect (simplified)
                # Rotate by changing width/height ratio
                w = abs(int(size * np.cos(rotation)))
                h = abs(int(size * np.sin(rotation)))
                w = max(2, w)
                h = max(2, h)

                draw.rectangle([x-w, y-h, x+w, y+h], fill=confetti['color'])

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip

    @staticmethod
    def create_combined(width, height, duration, fps, glitter=False, glitter_intensity=0.5,
                       stars=False, hearts=False, confetti=False):
        """Create combined particle effects in single layer for better performance.
        This is much faster than rendering multiple separate particle layers."""
        try:
            from moviepy import VideoClip
        except ImportError:
            from moviepy.editor import VideoClip

        # Initialize all particles we need
        np.random.seed(42)  # Reproducible

        # Glitter particles
        glitter_particles = []
        if glitter:
            num_particles = int(15 * glitter_intensity)  # Reduced from 20 for performance
            for _ in range(num_particles):
                glitter_particles.append({
                    'x': np.random.randint(0, width),
                    'y': np.random.randint(0, height),
                    'size': np.random.randint(2, 6),  # Smaller for performance
                    'phase': np.random.uniform(0, 2 * np.pi),
                    'speed': np.random.uniform(0.5, 2.0)
                })

        # Star particles
        star_particles = []
        if stars:
            num_stars = 10  # Reduced from 15
            np.random.seed(43)
            for _ in range(num_stars):
                star_particles.append({
                    'x': np.random.randint(0, width),
                    'y': np.random.randint(0, height),
                    'size': np.random.randint(12, 25),  # Smaller
                    'speed_x': np.random.uniform(-15, 15),
                    'speed_y': np.random.uniform(-25, -8),
                    'phase': np.random.uniform(0, 2 * np.pi),
                    'rotation_speed': np.random.uniform(1, 3)
                })

        # Heart particles
        heart_particles = []
        if hearts:
            num_hearts = 8  # Reduced from 12
            np.random.seed(44)
            for _ in range(num_hearts):
                heart_particles.append({
                    'x': np.random.randint(0, width),
                    'y': np.random.randint(0, height),
                    'size': np.random.randint(15, 30),
                    'speed_y': np.random.uniform(-30, -15),
                    'wobble': np.random.uniform(0.5, 2.0),
                    'phase': np.random.uniform(0, 2 * np.pi)
                })

        # Confetti particles
        confetti_particles = []
        if confetti:
            colors = [(255, 0, 100, 200), (255, 200, 0, 200), (0, 255, 100, 200),
                      (100, 100, 255, 200), (255, 100, 255, 200)]
            num_confetti = 20  # Reduced from 30
            np.random.seed(45)
            for _ in range(num_confetti):
                confetti_particles.append({
                    'x': np.random.randint(0, width),
                    'y': np.random.randint(-height, 0),
                    'size': np.random.randint(3, 8),
                    'speed_y': np.random.uniform(50, 120),
                    'speed_x': np.random.uniform(-20, 20),
                    'rotation': np.random.uniform(0, 2 * np.pi),
                    'rotation_speed': np.random.uniform(2, 5),
                    'color': colors[np.random.randint(0, len(colors))]
                })

        def make_frame(t):
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw glitter
            if glitter:
                for p in glitter_particles:
                    alpha = abs(np.sin(t * p['speed'] + p['phase']))
                    y_offset = int(t * 10) % height
                    y = (p['y'] + y_offset) % height
                    x = p['x']
                    size = p['size']
                    particle_alpha = int(255 * alpha * glitter_intensity)
                    color = (255, 255, 255, particle_alpha)
                    draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=color)

            # Draw stars
            if stars:
                for star in star_particles:
                    x = (star['x'] + int(star['speed_x'] * t)) % width
                    y = (star['y'] + int(star['speed_y'] * t)) % height
                    alpha = abs(np.sin(t * 0.5 + star['phase']))
                    size = star['size']
                    star_alpha = int(180 * alpha)
                    color = (255, 215, 0, star_alpha)
                    points = []
                    for i in range(5):
                        angle = i * 4 * np.pi / 5 - np.pi/2 + (t * star['rotation_speed'])
                        points.append((x + int(size * np.cos(angle)), y + int(size * np.sin(angle))))
                    for i in range(5):
                        j = (i + 2) % 5
                        draw.line([points[i], points[j]], fill=color, width=2)

            # Draw hearts
            if hearts:
                for heart in heart_particles:
                    x = heart['x'] + int(15 * np.sin(t * heart['wobble'] + heart['phase']))
                    y = (heart['y'] + int(heart['speed_y'] * t)) % height
                    alpha = abs(np.sin(t * 0.3 + heart['phase']))
                    size = heart['size']
                    heart_alpha = int(200 * alpha)
                    color = (255, 100, 150, heart_alpha)
                    draw.ellipse([x-size//2, y-size//2, x, y+size//4], fill=color)
                    draw.ellipse([x, y-size//2, x+size//2, y+size//4], fill=color)
                    draw.polygon([(x-size//2, y), (x+size//2, y), (x, y+size//2)], fill=color)

            # Draw confetti
            if confetti:
                for c in confetti_particles:
                    x = (c['x'] + int(c['speed_x'] * t)) % width
                    y = (c['y'] + int(c['speed_y'] * t)) % height
                    rotation = c['rotation'] + t * c['rotation_speed']
                    w = max(2, abs(int(c['size'] * np.cos(rotation))))
                    h = max(2, abs(int(c['size'] * np.sin(rotation))))
                    draw.rectangle([x-w, y-h, x+w, y+h], fill=c['color'])

            return np.array(img).copy()

        clip = VideoClip(make_frame, duration=duration)
        try:
            clip = clip.with_fps(fps)
        except:
            clip = clip.set_fps(fps)

        return clip


class TTSGenerator:
    """Text-to-Speech voiceover generator using Microsoft Edge TTS (natural voices)"""

    # Natural-sounding voice options with descriptions
    VOICES = {
        # US English - Female
        'aria': 'en-US-AriaNeural',           # Friendly, warm female
        'jenny': 'en-US-JennyNeural',         # Cheerful, energetic female
        'michelle': 'en-US-MichelleNeural',   # Professional, clear female
        'monica': 'en-US-MonicaNeural',       # Deep, mature female (DEEP)
        'nancy': 'en-US-NancyNeural',         # News anchor female, authoritative (DEEP)
        'amber': 'en-US-AmberNeural',         # Young, casual female
        'ashley': 'en-US-AshleyNeural',       # Bright, youthful female
        'sara': 'en-US-SaraNeural',           # Mature, calm female

        # US English - Male
        'guy': 'en-US-GuyNeural',             # Friendly, warm male
        'davis': 'en-US-DavisNeural',         # Professional, authoritative male
        'eric': 'en-US-EricNeural',           # Conversational, casual male
        'christopher': 'en-US-ChristopherNeural',  # Deep, mature male
        'jason': 'en-US-JasonNeural',         # Deep, powerful male (HEAVY)
        'tony': 'en-US-TonyNeural',           # News anchor, deep authoritative (HEAVY)
        'roger': 'en-US-RogerNeural',         # Older, wise male
        'steffan': 'en-US-SteffanNeural',     # Young, energetic male

        # British English
        'sonia': 'en-GB-SoniaNeural',         # British female
        'mia': 'en-GB-MiaNeural',             # British deeper, mature female (DEEP)
        'ryan': 'en-GB-RyanNeural',           # British male
        'thomas': 'en-GB-ThomasNeural',       # British deep, serious male (HEAVY)
        'libby': 'en-GB-LibbyNeural',         # British young female
        'alfie': 'en-GB-AlfieNeural',         # British young male

        # Australian English
        'natasha': 'en-AU-NatashaNeural',     # Australian female
        'annette': 'en-AU-AnnetteNeural',     # Australian deeper, professional female (DEEP)
        'william': 'en-AU-WilliamNeural',     # Australian male

        # Indian English
        'neerja': 'en-IN-NeerjaNeural',       # Indian female
        'prabhat': 'en-IN-PrabhatNeural',     # Indian male

        # Additional Professional Deep Voices
        'andrew': 'en-US-AndrewNeural',       # News anchor, very deep authoritative male (ULTRA DEEP)
        'brian': 'en-US-BrianNeural',         # Deep, serious male narrator (ULTRA DEEP)
        'ana': 'en-US-AnaNeural',             # Deep, professional female narrator (DEEP)
        'brandon': 'en-US-BrandonNeural',     # Deep, mature male (DEEP)
        'emma': 'en-US-EmmaNeural',           # Professional, warm female
        'jacob': 'en-US-JacobNeural',         # Deep, confident male (DEEP)

        # PREMIUM MOTIVATIONAL VOICES (Perfect for quotes & inspiration)
        'steffan_multi': 'en-US-SteffanMultilingualNeural',  # Powerful multilingual (MOTIVATION KING)
        'andrew_multi': 'en-US-AndrewMultilingualNeural',    # Deep motivational narrator (ULTRA POWERFUL)
        'ava_multi': 'en-US-AvaMultilingualNeural',          # Commanding female (POWERFUL MOTIVATION)
        'emma_multi': 'en-US-EmmaMultilingualNeural',        # Warm inspirational female (INSPIRING)
        'brian_multi': 'en-US-BrianMultilingualNeural',      # Deep powerful narrator (EPIC MOTIVATION)
        'alloy': 'en-US-AlloyMultilingualNeural',            # Smooth deep male (PREMIUM DEEP)
        'nova': 'en-US-NovaMultilingualNeural',              # Clear powerful female (PREMIUM)
        'shimmer': 'en-US-ShimmerMultilingualNeural',        # Energetic motivational (HIGH ENERGY)

        # ROMANTIC & RELATIONSHIP VOICES (Perfect for love quotes & relationships)
        'aria_whisper': 'en-US-AriaNeural',          # Soft intimate female (WHISPER STYLE)
        'jenny_tender': 'en-US-JennyNeural',         # Gentle caring female (TENDER)
        'sara_whisper': 'en-US-SaraNeural',          # Deep soothing female (INTIMATE)
        'guy_soft': 'en-US-GuyNeural',               # Gentle romantic male (SOFT)
        'davis_tender': 'en-US-DavisNeural',         # Warm comforting male (TENDER)
        'christopher_whisper': 'en-US-ChristopherNeural',  # Deep intimate male (WHISPER)

        # Additional Powerful Voices
        'kai': 'en-US-KaiNeural',                            # Deep authoritative male (COMMAND)
        'luna': 'en-US-LunaNeural',                          # Rich warm female (INSPIRING)
        'jenny_multi': 'en-US-JennyMultilingualNeural',      # Energetic multilingual female (UPBEAT)
        'ryan_multi': 'en-US-RyanMultilingualNeural',        # Deep confident male (STRONG)

        # URDU VOICES (اردو آوازیں)
        # Pakistani Urdu (Best for Poetry & Motivation)
        'asad': 'ur-PK-AsadNeural',           # Pakistani Male (Deep Professional - BEST FOR MOTIVATION)
        'uzma': 'ur-PK-UzmaNeural',           # Pakistani Female (Clear Expressive - BEST FOR POETRY)

        # Indian Urdu (Rich & Cultural)
        'salman': 'ur-IN-SalmanNeural',       # Indian Male (Warm Poetic - GREAT FOR SHAYARI)
        'gul': 'ur-IN-GulNeural',             # Indian Female (Soft Melodious - POETRY)

        # Multilingual Urdu Support (Premium for Poetry)
        'asad_multi': 'ur-PK-AsadMultilingualNeural',    # Pakistani Multi (POWERFUL MOTIVATION)
        'uzma_multi': 'ur-PK-UzmaMultilingualNeural',    # Pakistani Multi (EXPRESSIVE POETRY)

        # Additional Regional Voices (Supporting Urdu)
        'faiz': 'ur-PK-AsadNeural',           # Alias for poetry (named after Faiz Ahmed Faiz)
        'parveen': 'ur-PK-UzmaNeural',        # Alias for female poetry (Parveen Shakir style)

        # Backward compatibility
        'female': 'en-US-AriaNeural',         # Default female
        'male': 'en-US-GuyNeural',            # Default male
    }

    # Voice display names for GUI
    VOICE_NAMES = {
        'aria': 'Aria - US Female (Friendly)',
        'jenny': 'Jenny - US Female (Cheerful)',
        'michelle': 'Michelle - US Female (Professional)',
        'monica': 'Monica - US Female (Deep & Mature) 💎',
        'nancy': 'Nancy - US Female (News Anchor, Deep) 💎',
        'amber': 'Amber - US Female (Young)',
        'ashley': 'Ashley - US Female (Bright)',
        'sara': 'Sara - US Female (Mature)',
        'guy': 'Guy - US Male (Friendly)',
        'davis': 'Davis - US Male (Professional)',
        'eric': 'Eric - US Male (Casual)',
        'christopher': 'Christopher - US Male (Deep)',
        'jason': 'Jason - US Male (Deep & Powerful) 🔥',
        'tony': 'Tony - US Male (News Anchor, Heavy) 🔥',
        'roger': 'Roger - US Male (Wise)',
        'steffan': 'Steffan - US Male (Energetic)',
        'sonia': 'Sonia - British Female',
        'mia': 'Mia - British Female (Deep & Mature) 💎',
        'ryan': 'Ryan - British Male',
        'thomas': 'Thomas - British Male (Deep & Serious) 🔥',
        'libby': 'Libby - British Female (Young)',
        'alfie': 'Alfie - British Male (Young)',
        'natasha': 'Natasha - Australian Female',
        'annette': 'Annette - Australian Female (Deep & Professional) 💎',
        'william': 'William - Australian Male',
        'neerja': 'Neerja - Indian Female',
        'prabhat': 'Prabhat - Indian Male',
        'andrew': 'Andrew - US Male (Ultra Deep News Anchor) 🎙️',
        'brian': 'Brian - US Male (Ultra Deep Narrator) 🎙️',
        'ana': 'Ana - US Female (Deep Professional Narrator) 💎',
        'brandon': 'Brandon - US Male (Deep & Mature) 🔥',
        'emma': 'Emma - US Female (Professional & Warm)',
        'jacob': 'Jacob - US Male (Deep & Confident) 🔥',

        # Premium Motivational Voices
        'steffan_multi': '⭐ Steffan Multi - US Male (MOTIVATION KING) 👑',
        'andrew_multi': '⭐ Andrew Multi - US Male (Ultra Powerful Motivation) 🚀',
        'ava_multi': '⭐ Ava Multi - US Female (Commanding & Powerful) 💪',
        'emma_multi': '⭐ Emma Multi - US Female (Warm & Inspiring) ✨',

        # Romantic & Relationship Voices
        'aria_whisper': '💕 Aria Whisper - US Female (Soft & Intimate) 🌹',
        'jenny_tender': '💕 Jenny Tender - US Female (Gentle & Caring) 💗',
        'sara_whisper': '💕 Sara Whisper - US Female (Deep & Soothing) 🌙',
        'guy_soft': '💕 Guy Soft - US Male (Gentle & Romantic) 💝',
        'davis_tender': '💕 Davis Tender - US Male (Warm & Comforting) ❤️',
        'christopher_whisper': '💕 Christopher Whisper - US Male (Deep & Intimate) 🌹',
        'brian_multi': '⭐ Brian Multi - US Male (Epic Deep Narrator) [VIDEO]',
        'alloy': '⭐ Alloy - US Male (Premium Smooth Deep) 💎',
        'nova': '⭐ Nova - US Female (Premium Clear & Powerful) 🌟',
        'shimmer': '⭐ Shimmer - US Female (High Energy Motivation) ⚡',
        'kai': 'Kai - US Male (Deep Authoritative Command) 🎖️',
        'luna': 'Luna - US Female (Rich Warm Inspiring) 🌙',
        'jenny_multi': 'Jenny Multi - US Female (Energetic Upbeat) 🎉',
        'ryan_multi': 'Ryan Multi - US Male (Deep Confident Strong) 💪',

        # Urdu Voices - اردو آوازیں
        # Pakistani Urdu (پاکستانی اردو)
        'asad': '⭐ اسد Asad - Pakistani Male (MOTIVATION MASTER) 🇵🇰💪',
        'uzma': '⭐ عظمیٰ Uzma - Pakistani Female (POETRY QUEEN) 🇵🇰📖',
        'asad_multi': '🌟 اسد Multi - Pakistani (Powerful Motivation) 🇵🇰🚀',
        'uzma_multi': '🌟 عظمیٰ Multi - Pakistani (Expressive Poetry) 🇵🇰✨',

        # Indian Urdu (ہندوستانی اردو)
        'salman': '📜 سلمان Salman - Indian Male (Shayari Master) 🇮🇳',
        'gul': '🌺 گل Gul - Indian Female (Melodious Poetry) 🇮🇳',

        # Poetry Aliases (شاعری)
        'faiz': '🎭 فیض Faiz - Poetry Deep (Like Faiz Ahmed Faiz) 📖',
        'parveen': '💫 پروین Parveen - Female Poetry (Parveen Shakir) 🌹',
    }

    @staticmethod
    async def _generate_async_with_timing(text: str, output_path: Path, voice: str, rate: str, style: str = None):
        """Async TTS generation with word-level timing data and speaking style support"""
        try:
            # Apply speaking style for romantic/whisper voices
            # SSML styles: "gentle", "soft", "whispered", "calm", "cheerful", "sad", etc.
            if style:
                # Use SSML format for style control
                ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US"><voice name="{voice}"><express-as style="{style}">{text}</express-as></voice></speak>'
                communicate = edge_tts.Communicate(ssml_text, voice, rate=rate)
            else:
                # Regular text without style
                communicate = edge_tts.Communicate(text, voice, rate=rate)

            # Collect word timings
            word_timings = []
            chunk_count = 0
            audio_chunks = 0
            word_boundary_chunks = 0

            # Generate and save audio with word boundaries
            with open(str(output_path), 'wb') as audio_file:
                async for chunk in communicate.stream():
                    chunk_count += 1
                    chunk_type = chunk.get("type", "unknown")

                    if chunk_type == "audio":
                        audio_file.write(chunk["data"])
                        audio_chunks += 1
                    elif chunk_type == "WordBoundary":
                        word_boundary_chunks += 1
                        # Word timing info from edge-tts
                        word_info = {
                            'word': chunk.get('text', ''),
                            'offset': chunk.get('offset', 0) / 10000000.0,  # Convert to seconds
                            'duration': chunk.get('duration', 0) / 10000000.0  # Convert to seconds
                        }
                        word_timings.append(word_info)
                    # Also check for lowercase variant
                    elif chunk_type == "word_boundary":
                        word_boundary_chunks += 1
                        word_info = {
                            'word': chunk.get('text', ''),
                            'offset': chunk.get('offset', 0) / 10000000.0,
                            'duration': chunk.get('duration', 0) / 10000000.0
                        }
                        word_timings.append(word_info)

            print(f"  TTS Debug: {chunk_count} total chunks, {audio_chunks} audio, {word_boundary_chunks} word boundaries")

            # If no word boundaries, split text into words and estimate timing
            if not word_timings:
                print(f"  [WARNING] No word boundaries from TTS - using text splitting for word-level captions")
                words = text.split()
                if words:
                    # Estimate word duration (total audio duration / number of words)
                    # We'll calculate actual duration after file is created
                    for i, word in enumerate(words):
                        word_timings.append({
                            'word': word,
                            'offset': i,  # Placeholder - will be calculated later
                            'duration': 1  # Placeholder
                        })

            return True, word_timings
        except Exception as e:
            print(f"[WARNING] Async TTS generation error: {e}")
            import traceback
            traceback.print_exc()
            return False, []

    @staticmethod
    async def _generate_async(text: str, output_path: Path, voice: str, rate: str) -> bool:
        """Async TTS generation using edge-tts (legacy - no timing)"""
        try:
            # Create TTS communicator
            communicate = edge_tts.Communicate(text, voice, rate=rate)

            # Generate and save audio
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            print(f"[WARNING] Async TTS generation error: {e}")
            return False

    @staticmethod
    def _generate_kokoro_voiceover(text: str, output_path: Path, settings: dict):
        """Generate voiceover using local Kokoro TTS (offline)
        Returns: (success: bool, word_timings: list)
        """
        try:
            # Try to import Kokoro
            try:
                from kokoro_onnx import Kokoro
            except ImportError:
                print("[ERROR] Kokoro TTS not installed. Install with: pip install kokoro-onnx")
                print("[INFO] Falling back to Cloud TTS...")
                # Fallback to cloud TTS
                settings['tts_engine'] = 'cloud'
                return TTSGenerator.generate_voiceover(text, output_path, settings)

            # Get Kokoro settings
            voice = settings.get('kokoro_voice', 'af_bella')
            speed = settings.get('tts_speed', 130) / 100  # Convert to multiplier (1.0 = normal)

            # Clean text for TTS
            clean_text = re.sub(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+', '', text)
            clean_text = clean_text.strip()

            if not clean_text:
                print("[WARNING] No text to convert after cleaning")
                return False, []

            print(f"[INFO] Generating Kokoro TTS with voice: {voice}")

            # Initialize Kokoro with model paths
            # Kokoro requires model_path and voices_path
            try:
                import os
                kokoro_dir = os.path.expanduser("~/.kokoro")
                model_path = os.path.join(kokoro_dir, "kokoro-v0_19.onnx")
                voices_path = os.path.join(kokoro_dir, "voices.json")

                # Check if default paths exist, try settings otherwise
                if not os.path.exists(model_path):
                    model_path = settings.get('kokoro_model_path', model_path)
                if not os.path.exists(voices_path):
                    voices_path = settings.get('kokoro_voices_path', voices_path)

                if not os.path.exists(model_path):
                    print(f"[ERROR] Kokoro model not found at: {model_path}")
                    print("[INFO] Falling back to Cloud TTS...")
                    settings['tts_engine'] = 'cloud'
                    return TTSGenerator.generate_voiceover(text, output_path, settings)

                kokoro = Kokoro(model_path, voices_path)
            except Exception as init_error:
                print(f"[ERROR] Failed to initialize Kokoro: {init_error}")
                print("[INFO] Falling back to Cloud TTS...")
                settings['tts_engine'] = 'cloud'
                return TTSGenerator.generate_voiceover(text, output_path, settings)

            # Generate audio
            audio, sample_rate = kokoro.create(
                text=clean_text,
                voice=voice,
                speed=speed
            )

            # Save as WAV first, then convert to MP3
            import soundfile as sf
            wav_path = output_path.with_suffix('.wav')
            sf.write(str(wav_path), audio, sample_rate)

            # Convert to MP3 using ffmpeg
            import subprocess
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-i', str(wav_path),
                    '-acodec', 'libmp3lame', '-q:a', '2',
                    str(output_path)
                ], capture_output=True, check=True)
                wav_path.unlink()  # Remove WAV file
            except Exception as e:
                print(f"[WARNING] Could not convert to MP3: {e}")
                # Use WAV directly
                output_path = wav_path

            # Generate word timings (estimated based on text)
            words = clean_text.split()
            word_timings = []

            # Calculate audio duration
            audio_duration = len(audio) / sample_rate

            # Use character-weighted timing
            word_lengths = [max(2, len(w)) for w in words]
            total_chars = sum(word_lengths)

            current_time = 0.0
            for i, word in enumerate(words):
                word_duration = (word_lengths[i] / total_chars) * audio_duration
                word_timings.append({
                    'word': word,
                    'offset': current_time,
                    'duration': word_duration
                })
                current_time += word_duration

            print(f"[OK] Generated Kokoro TTS voiceover: {output_path.name}")
            print(f"  {len(word_timings)} words, {audio_duration:.2f}s duration")
            return True, word_timings

        except Exception as e:
            print(f"[ERROR] Kokoro TTS generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False, []

    @staticmethod
    def generate_voiceover(text: str, output_path: Path, settings: dict = None):
        """Generate natural-sounding voiceover from text using selected TTS engine
        Returns: (success: bool, word_timings: list)
        """
        settings = settings or {}

        # Check which TTS engine to use
        tts_engine = settings.get('tts_engine', 'cloud')

        # Use Kokoro (local) TTS if selected
        if tts_engine == 'local':
            return TTSGenerator._generate_kokoro_voiceover(text, output_path, settings)

        # Otherwise use Cloud TTS (edge-tts)
        if not TTS_AVAILABLE:
            print("[WARNING] Cloud TTS not available - skipping voiceover generation")
            return False, []

        try:
            # Select voice based on preference (defaults to 'aria')
            voice_key = settings.get('tts_voice', 'aria').lower()
            voice = TTSGenerator.VOICES.get(voice_key, TTSGenerator.VOICES['aria'])

            # Detect speaking style based on voice key
            speaking_style = None
            if '_whisper' in voice_key:
                speaking_style = 'gentle'  # Soft, intimate tone
            elif '_tender' in voice_key or '_soft' in voice_key:
                speaking_style = 'calm'    # Warm, comforting tone

            # Calculate speech rate adjustment
            # Settings range: 100-250 (default 130 - slower for better caption sync)
            # edge-tts rate format: "+0%", "-20%", "+50%"
            speed = settings.get('tts_speed', 130)
            rate_percent = int((speed - 150) / 150 * 100)  # Convert to percentage
            rate = f"{rate_percent:+d}%" if rate_percent != 0 else "+0%"

            # Clean text for TTS (remove emojis and special characters)
            clean_text = re.sub(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+', '', text)
            clean_text = clean_text.strip()

            if not clean_text:
                print("[WARNING] No text to convert after cleaning")
                return False, []

            # Run async TTS generation with word timing
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create a new one in a thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            TTSGenerator._generate_async_with_timing(clean_text, output_path, voice, rate, speaking_style)
                        )
                        success, word_timings = future.result(timeout=30)
                else:
                    success, word_timings = loop.run_until_complete(
                        TTSGenerator._generate_async_with_timing(clean_text, output_path, voice, rate, speaking_style)
                    )
            except RuntimeError:
                # No event loop, create a new one
                success, word_timings = asyncio.run(
                    TTSGenerator._generate_async_with_timing(clean_text, output_path, voice, rate, speaking_style)
                )

            if success:
                print(f"[OK] Generated natural TTS voiceover: {output_path.name} (voice: {voice})")
                print(f"  {len(word_timings)} words with timing data")
                return True, word_timings
            else:
                return False, []

        except Exception as e:
            print(f"[WARNING] TTS generation failed: {e}")
            return False, []


class CaptionRenderer:
    """Render synchronized captions/subtitles"""

    @staticmethod
    def create_highlighted_word_captions(text, audio_duration, video_width, video_height, settings):
        """Create CapCut-style highlighted captions where current word is highlighted in different color"""
        import re
        # ImageClip is already imported at module level, no need to re-import
        print(f"[EFFECT] CAPCUT CAPTIONS: Creating highlighted captions")
        print(f"   Text: {text[:100]}...")
        print(f"   Duration: {audio_duration}s")
        print(f"   Video size: {video_width}x{video_height}")

        # Extract emojis and clean text
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+')
        clean_text = emoji_pattern.sub('', text).strip()

        print(f"   Clean text (no emojis): {clean_text}")

        if not clean_text or audio_duration <= 0:
            print(f"[WARNING]️ CAPCUT: Skipping - empty text or invalid duration")
            return []

        words = clean_text.split()
        if not words:
            return []

        # Settings
        words_per_caption = settings.get('caption_words_per_line', 3)
        font_size = settings.get('caption_highlight_font_size', 42)  # CapCut-specific font size
        font_style = settings.get('caption_highlight_font_style', 'Arial Bold')  # CapCut-specific font style
        position = settings.get('caption_position', 'bottom')
        emoji_enabled = settings.get('emoji_in_captions', True)

        # Get emoji preset
        emoji_preset_category = settings.get('emoji_preset_category', 'general')
        if emoji_preset_category in CaptionRenderer.EMOJI_PRESETS:
            emoji_list = CaptionRenderer.EMOJI_PRESETS[emoji_preset_category]
            print(f"   Using emoji preset: {emoji_preset_category} ({len(emoji_list)} emojis)")
        else:
            emoji_list = CaptionRenderer.EMOJI_PRESETS['general']
            print(f"   Using default emoji preset: general")

        # Colors
        inactive_color_hex = settings.get('caption_inactive_color', '#FFFFFF')  # White for non-active words
        active_color_hex = settings.get('caption_highlight_color', '#FFD700')  # Yellow/gold for active word

        # Stroke/outline settings
        stroke_enabled = settings.get('caption_stroke_enabled', True)
        active_stroke_hex = settings.get('caption_active_stroke_color', '#FF1493')  # Pink for active word outline
        inactive_stroke_hex = settings.get('caption_inactive_stroke_color', '#000000')  # Black for inactive outline
        stroke_width = settings.get('caption_stroke_width', 4)

        # Convert hex to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        inactive_color = hex_to_rgb(inactive_color_hex)
        active_color = hex_to_rgb(active_color_hex)
        active_stroke = hex_to_rgb(active_stroke_hex)
        inactive_stroke = hex_to_rgb(inactive_stroke_hex)

        print(f"   Stroke enabled: {stroke_enabled}, width: {stroke_width}")
        print(f"   Active: {active_color_hex} with stroke {active_stroke_hex}")
        print(f"   Inactive: {inactive_color_hex} with stroke {inactive_stroke_hex}")

        # Load fonts
        # Map font style names to font file names
        font_map = {
            "Arial": "arial.ttf",
            "Arial Black": "ariblk.ttf",
            "Arial Bold": "arialbd.ttf",
            "Arial Italic": "ariali.ttf",
            "Arial Bold Italic": "arialbi.ttf",
            "Calibri": "calibri.ttf",
            "Calibri Bold": "calibrib.ttf",
            "Times New Roman": "times.ttf",
            "Times New Roman Bold": "timesbd.ttf",
            "Verdana": "verdana.ttf",
            "Verdana Bold": "verdanab.ttf",
            "Georgia": "georgia.ttf",
            "Georgia Bold": "georgiab.ttf",
            "Comic Sans MS": "comic.ttf",
            "Comic Sans MS Bold": "comicbd.ttf",
            "Impact": "impact.ttf",
            "Trebuchet MS": "trebuc.ttf",
            "Trebuchet MS Bold": "trebucbd.ttf",
            "Segoe UI": "segoeui.ttf",
            "Segoe UI Bold": "segoeuib.ttf",
            "Courier New": "cour.ttf",
            "Courier New Bold": "courbd.ttf",
            "Tahoma": "tahoma.ttf",
            "Tahoma Bold": "tahomabd.ttf",
            "Montserrat Bold": "arialbd.ttf",  # Fallback to Arial Bold
            "Bebas Neue": "impact.ttf",  # Fallback to Impact
            "Poppins Bold": "arialbd.ttf",  # Fallback to Arial Bold
            "Roboto Bold": "arialbd.ttf"  # Fallback to Arial Bold
        }

        try:
            font_file = font_map.get(font_style, 'arialbd.ttf')
            font_path = str(Path(r"C:\Windows\Fonts") / font_file)
            font = ImageFont.truetype(font_path, font_size)
            print(f"   Using font: {font_style} ({font_file}) at {font_size}px")
            # Emoji font
            emoji_font_path = str(Path(r"C:\Windows\Fonts") / 'seguiemj.ttf')
            emoji_font = ImageFont.truetype(emoji_font_path, int(font_size * 0.8))
        except Exception as e:
            print(f"   [WARNING]️ Font loading failed: {e}, using default")
            font = ImageFont.load_default()
            emoji_font = font

        # Timing
        speaking_rate_wpm = settings.get('tts_speed', 150)
        time_per_word = 60.0 / speaking_rate_wpm

        caption_clips = []
        current_time = 0.0

        # Distribute emojis across words
        total_segments = len(words)
        emoji_distribution = []
        if emoji_enabled and emoji_list:
            for i in range(total_segments):
                emoji_distribution.append(emoji_list[i % len(emoji_list)])
        else:
            emoji_distribution = [''] * total_segments

        # Process each word individually for highlighting effect
        for word_idx, word in enumerate(words):
            word_start = current_time
            word_duration = time_per_word

            # Get context (words before and after for display)
            # Get caption_layout (1-line vs 2-line) - this controls LINE ARRANGEMENT
            caption_layout = settings.get('caption_layout', '2-line')

            # Get words_per_caption - this controls HOW MANY words to display
            words_per_caption = settings.get('caption_words_per_line', 3)

            # Calculate total words to show based on layout
            if caption_layout == '1-line':
                # 1-line layout: Show words_per_caption words on ONE line
                context_words = words_per_caption
            else:
                # 2-line layout: Show words_per_caption * 2 words (split across 2 lines)
                context_words = words_per_caption * 2

            # Calculate display range to show active word in center/focus
            half_context = context_words // 2
            display_start_idx = max(0, word_idx - half_context)
            display_end_idx = min(len(words), display_start_idx + context_words)

            # Adjust if we're near the start (show more words after)
            if display_start_idx == 0:
                display_end_idx = min(len(words), context_words)

            # Adjust if we're near the end (show more words before)
            if display_end_idx == len(words) and len(words) >= context_words:
                display_start_idx = max(0, len(words) - context_words)

            display_words = words[display_start_idx:display_end_idx]
            active_word_in_display = word_idx - display_start_idx

            # Get emoji for current word (if enabled)
            current_emoji = emoji_distribution[word_idx] if emoji_enabled else ''

            # Create image with highlighted word + emoji
            img = Image.new('RGBA', (video_width, 250), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Measure emoji size if present
            emoji_height = 0
            emoji_width = 0
            if current_emoji:
                emoji_bbox = draw.textbbox((0, 0), current_emoji, font=emoji_font)
                emoji_width = emoji_bbox[2] - emoji_bbox[0]
                emoji_height = emoji_bbox[3] - emoji_bbox[1]

            # Layout words based on user preference
            if caption_layout == '1-line':
                # Single line layout - all display_words on ONE line
                words_per_line = len(display_words)
                line1_words = display_words
                line2_words = []
                line_spacing = 0
            else:
                # Two-line layout - split display_words across 2 lines
                # Use words_per_caption to determine words per line
                words_per_line = words_per_caption
                line_spacing = int(font_size * 1.3)  # Space between lines
                line1_words = display_words[:words_per_line] if len(display_words) > 0 else []
                line2_words = display_words[words_per_line:words_per_line*2] if len(display_words) > words_per_line else []

            # Starting Y position for first line - leave space for emoji at top
            # Emoji needs space (emoji height + gap above + gap below), so start text lower
            if current_emoji:
                emoji_gap_top = 20  # Gap above emoji
                emoji_gap_bottom = 30  # Gap between emoji and text
                emoji_space = emoji_gap_top + emoji_height + emoji_gap_bottom
                first_line_y = emoji_space + 50  # Start text below emoji
            else:
                first_line_y = 100  # No emoji, start at normal position

            # Draw Line 1 (First 2 words)
            if line1_words:
                line1_text = ' '.join(line1_words)
                bbox1 = draw.textbbox((0, 0), line1_text, font=font)
                line1_width = bbox1[2] - bbox1[0]
                x_offset = (video_width - line1_width) // 2
                y_pos = first_line_y

                for idx, display_word in enumerate(line1_words):
                    is_active = idx == active_word_in_display

                    # Draw emoji above active word (if enabled)
                    if current_emoji and is_active:
                        word_bbox = draw.textbbox((0, 0), display_word, font=font)
                        word_width = word_bbox[2] - word_bbox[0]
                        emoji_x = x_offset + (word_width - emoji_width) // 2
                        emoji_y = y_pos - emoji_height - 30  # Increased gap from 15 to 30
                        draw.text((emoji_x, emoji_y), current_emoji, font=emoji_font, embedded_color=True)

                    text_color = active_color if is_active else inactive_color
                    stroke_color = active_stroke if is_active else inactive_stroke

                    # Draw stroke/outline first (if enabled)
                    # Active word gets THICKER stroke for prominence
                    current_stroke_width = stroke_width + 2 if is_active else stroke_width

                    if stroke_enabled:
                        for adj_x in range(-current_stroke_width, current_stroke_width + 1):
                            for adj_y in range(-current_stroke_width, current_stroke_width + 1):
                                if adj_x*adj_x + adj_y*adj_y <= current_stroke_width*current_stroke_width:
                                    draw.text((x_offset + adj_x, y_pos + adj_y), display_word,
                                            font=font, fill=stroke_color)

                    # Draw main text on top
                    draw.text((x_offset, y_pos), display_word, font=font, fill=text_color)

                    # Move to next word position
                    word_bbox = draw.textbbox((0, 0), display_word + ' ', font=font)
                    word_width = word_bbox[2] - word_bbox[0]
                    x_offset += word_width

            # Draw Line 2 (Next 2 words)
            if line2_words:
                line2_text = ' '.join(line2_words)
                bbox2 = draw.textbbox((0, 0), line2_text, font=font)
                line2_width = bbox2[2] - bbox2[0]
                x_offset = (video_width - line2_width) // 2
                y_pos = first_line_y + line_spacing

                for idx, display_word in enumerate(line2_words):
                    # Index in display_words array
                    overall_idx = words_per_line + idx
                    is_active = overall_idx == active_word_in_display

                    # Draw emoji above active word (if enabled)
                    if current_emoji and is_active:
                        word_bbox = draw.textbbox((0, 0), display_word, font=font)
                        word_width = word_bbox[2] - word_bbox[0]
                        emoji_x = x_offset + (word_width - emoji_width) // 2
                        emoji_y = y_pos - emoji_height - 30  # Increased gap from 15 to 30
                        draw.text((emoji_x, emoji_y), current_emoji, font=emoji_font, embedded_color=True)

                    text_color = active_color if is_active else inactive_color
                    stroke_color = active_stroke if is_active else inactive_stroke

                    # Draw stroke/outline first (if enabled)
                    # Active word gets THICKER stroke for prominence
                    current_stroke_width = stroke_width + 2 if is_active else stroke_width

                    if stroke_enabled:
                        for adj_x in range(-current_stroke_width, current_stroke_width + 1):
                            for adj_y in range(-current_stroke_width, current_stroke_width + 1):
                                if adj_x*adj_x + adj_y*adj_y <= current_stroke_width*current_stroke_width:
                                    draw.text((x_offset + adj_x, y_pos + adj_y), display_word,
                                            font=font, fill=stroke_color)

                    # Draw main text on top
                    draw.text((x_offset, y_pos), display_word, font=font, fill=text_color)

                    # Move to next word position
                    word_bbox = draw.textbbox((0, 0), display_word + ' ', font=font)
                    word_width = word_bbox[2] - word_bbox[0]
                    x_offset += word_width

            # Convert to frame array
            frame = np.array(img).copy()

            # Create clip
            clip = ImageClip(frame, is_mask=False)

            try:
                clip = clip.set_duration(word_duration)
                clip = clip.set_start(word_start)
            except AttributeError:
                clip = clip.with_duration(word_duration)
                clip = clip.with_start(word_start)

            # Position
            if position == 'top':
                y_pos = int(video_height * 0.1)
            elif position == 'center':
                y_pos = 'center'
            else:
                y_pos = int(video_height * 0.75)

            try:
                clip = clip.set_position(('center', y_pos))
            except AttributeError:
                clip = clip.with_position(('center', y_pos))

            # Apply animation effects
            animation_style = settings.get('caption_word_animation', 'none')
            animation_intensity = settings.get('caption_animation_intensity', 1.2)
            anim_duration = min(0.2, word_duration * 0.5)  # Animation takes first 20% of word duration

            if animation_style == 'pop':
                # Pop effect: scale from small to full size quickly
                def pop_scale(t):
                    if t < anim_duration:
                        progress = min(1.0, t / anim_duration)
                        # Ease-out for smooth pop (starts at 0.3, grows to 1.0)
                        scale = 0.3 + 0.7 * (progress ** 0.5)
                        return scale
                    return 1.0

                try:
                    # Use resize with time-varying function
                    try:
                        clip = clip.resized(pop_scale)
                    except:
                        clip = clip.resize(pop_scale)
                except Exception as e:
                    print(f"[DEBUG] Pop animation failed: {e}")

            elif animation_style == 'bounce':
                # Bounce effect: scale up beyond size, then bounce back
                def bounce_scale(t):
                    if t < anim_duration:
                        progress = t / anim_duration
                        # Overshoot and bounce back with elastic effect
                        # Goes from 1.0 -> 1.3 -> 1.0 (or whatever animation_intensity is set to)
                        if progress < 0.6:
                            # First part: scale up to peak
                            scale = 1.0 + (animation_intensity - 1.0) * (progress / 0.6)
                        else:
                            # Second part: bounce back to 1.0
                            bounce_back = (progress - 0.6) / 0.4
                            scale = animation_intensity - (animation_intensity - 1.0) * bounce_back
                        return scale
                    return 1.0

                try:
                    # Use resize with time-varying function
                    try:
                        clip = clip.resized(bounce_scale)
                    except:
                        clip = clip.resize(bounce_scale)
                except Exception as e:
                    print(f"[DEBUG] Bounce animation failed: {e}")

            elif animation_style == 'fade':
                # Fade effect: fade in from transparent
                try:
                    # Use MoviePy's built-in fadein
                    if anim_duration > 0:
                        try:
                            from moviepy.video.fx import FadeIn
                            clip = clip.with_effects([FadeIn(anim_duration)])
                        except:
                            clip = clip.fadein(anim_duration)
                except Exception as e:
                    print(f"[DEBUG] Fade animation failed: {e}")

            elif animation_style == 'slide':
                # Slide effect: slide in from right
                slide_distance = 100  # pixels

                def slide_position(t):
                    if t < anim_duration:
                        progress = t / anim_duration
                        # Ease-out for smooth deceleration
                        offset = slide_distance * (1.0 - progress ** 2)
                        return (video_width // 2 + int(offset), y_pos)
                    else:
                        return ('center', y_pos)

                try:
                    try:
                        clip = clip.with_position(slide_position)
                    except:
                        clip = clip.set_position(slide_position)
                except Exception as e:
                    print(f"[DEBUG] Slide animation failed: {e}")

            caption_clips.append(clip)
            current_time += word_duration

        print(f"[OK] Created {len(caption_clips)} highlighted caption clips (word-by-word)")
        return caption_clips

    # Emoji preset categories for different video themes
    EMOJI_PRESETS = {
        # Motivational & Inspirational
        'motivational': ['🔥', '💪', '⭐', '🚀', '💯', '✨', '🎯', '👑', '🏆', '⚡', '💎', '🌟', '🙌', '💫', '🌈'],

        # Love & Relationships
        'love': ['❤️', '💕', '💖', '💗', '💓', '💞', '💝', '💘', '😍', '🥰', '😘', '💑', '💏', '👫', '💐', '🌹', '💌'],

        # Heartbreak & Sad
        'heartbreak': ['💔', '😢', '😭', '🥺', '😞', '😔', '💧', '🌧️', '⛈️', '🖤', '🥀', '😪', '😿'],

        # Success & Achievement
        'success': ['🏆', '🥇', '🎯', '💰', '💵', '💸', '📈', '👑', '🔝', '💎', '[OK]', '🎊', '🎉', '🙌', '👏'],

        # Fitness & Health
        'fitness': ['💪', '🏋️', '🏃', '⚡', '🔥', '💯', '🥇', '🎯', '🏆', '💦', '🥗', '🍎', '[TIME]️', '📊'],

        # Business & Money
        'business': ['💼', '💰', '💵', '💸', '📈', '💎', '🏦', '💳', '🤑', '📊', '📉', '💹', '🏢', '👔', '⏰'],

        # Food & Cooking
        'food': ['🍕', '🍔', '🍟', '🌮', '🍜', '🍱', '🍣', '🍰', '🎂', '🍪', '☕', '🍷', '🔪', '👨‍🍳', '🍴'],

        # Travel & Adventure
        'travel': ['✈️', '🌍', '🗺️', '🏖️', '🏔️', '🚀', '🎒', '📸', '🌅', '🌴', '🗽', '🗼', '🏰', '⛰️', '🌊'],

        # Technology & Gaming
        'tech': ['💻', '📱', '🎮', '🖥️', '⚡', '🔌', '🤖', '🚀', '💾', '🖱️', '⌨️', '🎧', '📡', '🔋', '💿'],

        # Party & Celebration
        'party': ['🎉', '🎊', '🥳', '🎈', '🎆', '🎇', '✨', '🍾', '🥂', '🍻', '🎵', '🎶', '💃', '🕺', '🪩'],

        # Nature & Environment
        'nature': ['🌿', '🌱', '🌳', '🌲', '🌺', '🌸', '🌼', '🌻', '🌞', '🌙', '⭐', '🌈', '🦋', '🐝', '🌍'],

        # Warning & Alert
        'warning': ['[WARNING]️', '🚨', '⛔', '🚫', '❗', '❓', '💥', '🔥', '⚡', '☢️', '⚡', '🆘', '🔴', '⭕'],

        # Thinking & Learning
        'educational': ['📚', '📖', '✏️', '📝', '🎓', '🧠', '💡', '🤔', '💭', '🔍', '📊', '📈', '🎯', '[OK]', '⭐'],

        # Funny & Comedy
        'funny': ['😂', '🤣', '😆', '😹', '🤪', '😜', '😝', '🤭', '😅', '🙃', '🤡', '💀', '👻', '🤠', '🥳'],

        # Spiritual & Mindfulness
        'spiritual': ['🙏', '✨', '💫', '🌟', '⭐', '🕉️', '☮️', '💜', '🧘', '🕯️', '🌙', '☀️', '🌈', '💎', '🦋'],

        # Fashion & Beauty
        'fashion': ['👗', '👠', '💄', '💅', '👑', '💎', '✨', '👜', '🕶️', '💃', '🌟', '💫', '🎀', '👒', '💍'],

        # Animals & Pets
        'animals': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵'],

        # General/Mixed (default)
        'general': ['🔥', '💯', '✨', '⭐', '💪', '🚀', '💎', '👑', '🎯', '⚡', '❤️', '😍', '🎉', '💰', '🏆']
    }

    @staticmethod
    def create_estimated_captions(text, audio_duration, video_width, video_height, settings):
        """Create captions with estimated timing when word-level timing is unavailable"""
        # ImageClip is already imported at module level, no need to re-import
        caption_clips = []

        # Extract emojis from text (CapCut-style emoji integration)
        import re
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+')
        emojis_found = emoji_pattern.findall(text)

        # Remove emojis from text for word counting
        clean_text = emoji_pattern.sub('', text).strip()

        if not clean_text or audio_duration <= 0:
            return []

        # Split into words
        words = clean_text.split()
        if not words:
            return []

        # Caption settings
        words_per_caption = settings.get('caption_words_per_line', 3)
        font_size = settings.get('caption_font_size', 60)
        position = settings.get('caption_position', 'bottom')
        emoji_in_captions = settings.get('emoji_in_captions', True)  # Enable/disable emoji feature

        # ========== FIX: Use character-weighted timing for better caption sync ==========
        # Longer words take longer to say, so weight duration by character count
        # This provides much better synchronization with TTS voiceover

        # Calculate character-weighted durations for each word
        word_lengths = []
        for word in words:
            # Minimum effective length of 2 chars for short words like "I", "a"
            effective_length = max(2, len(word))
            word_lengths.append(effective_length)

        total_chars = sum(word_lengths)
        if total_chars == 0:
            total_chars = 1

        # Use the full audio duration and distribute by character weight
        caption_duration = audio_duration

        # Calculate time per character unit
        time_per_char = caption_duration / total_chars

        # Calculate average for logging
        avg_time_per_word = caption_duration / len(words) if words else 0

        print(f"  Caption timing: {len(words)} words, {caption_duration:.2f}s duration ({avg_time_per_word:.2f}s avg per word)")

        # No timing offset - start at 0 for better sync
        timing_offset = 0.0

        # Load fonts
        try:
            # Text font (Arial Bold)
            font_path = str(Path(r"C:\Windows\Fonts") / 'arialbd.ttf')
            font = ImageFont.truetype(font_path, font_size)

            # Emoji font (Segoe UI Emoji for proper emoji rendering)
            emoji_font_path = str(Path(r"C:\Windows\Fonts") / 'seguiemj.ttf')
            emoji_font = ImageFont.truetype(emoji_font_path, int(font_size * 1.2))  # Slightly larger
        except:
            font = ImageFont.load_default()
            emoji_font = font

        # Distribute emojis across segments (1 emoji per caption line, context-based)
        emoji_distribution = []
        if emoji_in_captions:
            total_segments = (len(words) + words_per_caption - 1) // words_per_caption

            # ALWAYS use emoji preset from settings (ignore emojis in text)
            # Get emoji preset category from settings
            emoji_preset = settings.get('emoji_preset_category', 'general')

            # Use the selected preset, fallback to general if invalid
            if emoji_preset in CaptionRenderer.EMOJI_PRESETS:
                emojis_found = CaptionRenderer.EMOJI_PRESETS[emoji_preset]
                print(f"  Using '{emoji_preset}' emoji preset ({len(emojis_found)} emojis)")
            else:
                emojis_found = CaptionRenderer.EMOJI_PRESETS['general']
                print(f"  Invalid preset '{emoji_preset}', using 'general' preset ({len(emojis_found)} emojis)")

            if emojis_found:
                print(f"  Preset emojis: {emojis_found[:5]}..." if len(emojis_found) > 5 else f"  Preset emojis: {emojis_found}")

            # Cycle through all emojis - different emoji for each caption
            for seg_idx in range(total_segments):
                # Always cycle through emojis to ensure variety
                emoji_distribution.append(emojis_found[seg_idx % len(emojis_found)])

            print(f"  Emoji distribution: {emoji_distribution}")
            print(f"  Total: {len(emoji_distribution)} captions, each with different emoji from {len(emojis_found)} emoji set")

        # Create caption segments
        current_time = 0.0
        for i in range(0, len(words), words_per_caption):
            segment_words = words[i:i+words_per_caption]
            text_content = ' '.join(segment_words)

            # Add emoji for this segment (CapCut style)
            segment_index = i // words_per_caption
            emoji_for_segment = ''
            if emoji_in_captions and segment_index < len(emoji_distribution):
                emoji_for_segment = emoji_distribution[segment_index]

            # Calculate timing using character-weighted approach
            start_time = current_time  # Exact timing, no offset needed

            # Sum character weights for words in this segment
            segment_start_idx = i
            segment_end_idx = min(i + words_per_caption, len(words))
            segment_char_weight = sum(word_lengths[segment_start_idx:segment_end_idx])

            # Duration proportional to character weight
            duration = segment_char_weight * time_per_char
            current_time += duration

            try:
                # Calculate dimensions for text + emoji
                dummy_img = Image.new('RGBA', (1, 1))
                dummy_draw = ImageDraw.Draw(dummy_img)

                # Get layout preference (1-line or 2-line)
                caption_layout = settings.get('caption_layout', '2-line')

                # Layout words based on user preference
                if caption_layout == '1-line':
                    # Single line layout - all words on one line
                    line1_words = segment_words
                    line2_words = []
                    line1_text = ' '.join(line1_words) if line1_words else ''
                    line2_text = ''

                    line1_bbox = dummy_draw.textbbox((0, 0), line1_text, font=font) if line1_text else (0, 0, 0, 0)
                    line1_width = line1_bbox[2] - line1_bbox[0]
                    line2_width = 0
                    text_width = line1_width
                    text_height = line1_bbox[3] - line1_bbox[1]
                    line_height = text_height
                    line_spacing = 0
                else:
                    # Two-line layout - 2 words per line (like CapCut captions)
                    words_per_line = 2
                    line1_words = segment_words[:words_per_line] if len(segment_words) > 0 else []
                    line2_words = segment_words[words_per_line:words_per_line*2] if len(segment_words) > words_per_line else []

                    # Measure each line
                    line1_text = ' '.join(line1_words) if line1_words else ''
                    line2_text = ' '.join(line2_words) if line2_words else ''

                    line1_bbox = dummy_draw.textbbox((0, 0), line1_text, font=font) if line1_text else (0, 0, 0, 0)
                    line2_bbox = dummy_draw.textbbox((0, 0), line2_text, font=font) if line2_text else (0, 0, 0, 0)

                    line1_width = line1_bbox[2] - line1_bbox[0]
                    line2_width = line2_bbox[2] - line2_bbox[0]
                    line_height = line1_bbox[3] - line1_bbox[1]

                    # Total width is the max of both lines
                    text_width = max(line1_width, line2_width)
                    line_spacing = int(font_size * 1.3)  # Space between lines

                    # Total text height = line height + spacing + line height
                    text_height = line_height
                    if line2_text:
                        text_height = line_height * 2 + line_spacing

                # Measure emoji if present
                emoji_width = 0
                emoji_height = 0
                emoji_spacing = 15  # Space between text and emoji
                if emoji_for_segment:
                    emoji_bbox = dummy_draw.textbbox((0, 0), emoji_for_segment, font=emoji_font)
                    emoji_width = (emoji_bbox[2] - emoji_bbox[0]) + emoji_spacing
                    emoji_height = emoji_bbox[3] - emoji_bbox[1]

                # Calculate total dimensions - emoji is ABOVE text, so add to height
                total_width = text_width  # Emoji doesn't add to width since it's above
                padding = 20
                emoji_gap = 10 if emoji_for_segment else 0

                img_width = min(max(total_width, emoji_width) + padding * 2, int(video_width * 0.9))

                # Height = text height + emoji height (if present) + gap + padding
                img_height = text_height + padding * 2
                if emoji_for_segment:
                    img_height += emoji_height + emoji_gap

                # Get background settings
                bg_enabled = settings.get('caption_bg_enabled', False)

                # Create caption image with or without background
                if bg_enabled:
                    # Background enabled - use user's color
                    bg_color_hex = settings.get('caption_bg_color', '#000000')
                    bg_color_rgb = tuple(int(bg_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    img = Image.new('RGB', (img_width, img_height), bg_color_rgb)
                    draw = ImageDraw.Draw(img)
                else:
                    # No background - transparent
                    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(img)

                # Get text color
                text_color_hex = settings.get('caption_text_color', '#FFFFFF')
                text_color_rgb = tuple(int(text_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

                # Stroke settings for regular captions
                stroke_enabled = settings.get('caption_stroke_enabled', False)
                stroke_color_hex = settings.get('caption_inactive_stroke_color', '#000000')  # Use inactive stroke for regular captions
                stroke_width = settings.get('caption_stroke_width', 4)
                stroke_color_rgb = tuple(int(stroke_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

                # Draw emoji FIRST (at top)
                emoji_y = padding
                if emoji_for_segment:
                    # Center emoji horizontally
                    emoji_x = (img_width - emoji_width) // 2

                    # Use embedded_color=True to preserve emoji colors (Pillow 8.0+)
                    try:
                        draw.text((emoji_x, emoji_y), emoji_for_segment, font=emoji_font, embedded_color=True)
                    except TypeError:
                        # Fallback for older Pillow versions - draw without fill to use emoji colors
                        draw.text((emoji_x, emoji_y), emoji_for_segment, font=emoji_font)

                # Draw text BELOW emoji on TWO LINES
                first_line_y = padding
                if emoji_for_segment:
                    first_line_y = emoji_y + emoji_height + emoji_gap

                # Draw Line 1 (First 2 words)
                if line1_text:
                    line1_x = (img_width - line1_width) // 2
                    line1_y = first_line_y

                    # Draw stroke/outline first (if enabled)
                    if stroke_enabled:
                        for adj_x in range(-stroke_width, stroke_width + 1):
                            for adj_y in range(-stroke_width, stroke_width + 1):
                                if adj_x*adj_x + adj_y*adj_y <= stroke_width*stroke_width:
                                    draw.text((line1_x + adj_x, line1_y + adj_y), line1_text,
                                            font=font, fill=stroke_color_rgb)

                    # Draw main text on top
                    draw.text((line1_x, line1_y), line1_text, font=font, fill=text_color_rgb)

                # Draw Line 2 (Next 2 words)
                if line2_text:
                    line2_x = (img_width - line2_width) // 2
                    line2_y = first_line_y + line_height + line_spacing

                    # Draw stroke/outline first (if enabled)
                    if stroke_enabled:
                        for adj_x in range(-stroke_width, stroke_width + 1):
                            for adj_y in range(-stroke_width, stroke_width + 1):
                                if adj_x*adj_x + adj_y*adj_y <= stroke_width*stroke_width:
                                    draw.text((line2_x + adj_x, line2_y + adj_y), line2_text,
                                            font=font, fill=stroke_color_rgb)

                    # Draw main text on top
                    draw.text((line2_x, line2_y), line2_text, font=font, fill=text_color_rgb)

                # Convert to frame array
                frame = np.array(img).copy()

                # ImageClip is now imported at function level
                clip = ImageClip(frame, is_mask=False)

                try:
                    clip = clip.set_duration(duration)
                    clip = clip.set_start(start_time)
                except AttributeError:
                    clip = clip.with_duration(duration)
                    clip = clip.with_start(start_time)

                # Position
                if position == 'top':
                    y_pos = int(video_height * 0.1)
                elif position == 'center':
                    y_pos = 'center'
                else:  # bottom
                    y_pos = int(video_height * 0.75)

                try:
                    clip = clip.set_position(('center', y_pos))
                except AttributeError:
                    clip = clip.with_position(('center', y_pos))

                caption_clips.append(clip)

            except Exception as e:
                print(f"[WARNING] Error creating caption segment: {e}")

        print(f"[OK] Created {len(caption_clips)} estimated caption segments")
        return caption_clips

    @staticmethod
    def create_word_captions(word_timings, video_width, video_height, settings):
        """Create synchronized caption clips for each word"""
        # ImageClip is already imported at module level
        caption_clips = []

        # Caption settings from config
        font_size = settings.get('caption_font_size', 70)

        # Parse hex color to RGB tuple
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        text_color = hex_to_rgb(settings.get('caption_text_color', '#FFFFFF'))
        bg_color = hex_to_rgb(settings.get('caption_bg_color', '#000000'))
        bg_opacity = settings.get('caption_bg_opacity', 180)  # 0-255
        bg_enabled = settings.get('caption_bg_enabled', True)  # Enable/disable background
        position = settings.get('caption_position', 'center')  # top, center, bottom
        words_per_caption = settings.get('caption_words_per_line', 3)  # Show 3 words at a time
        gap_between_captions = 0.0  # Perfect sync with voiceover (no gap)

        # Load font
        try:
            font_file = settings.get('caption_font_style', 'arialbd.ttf')
            font_path = str(Path(r"C:\Windows\Fonts") / font_file)
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        # Group words into caption segments
        caption_segments = []
        for i in range(0, len(word_timings), words_per_caption):
            segment_words = word_timings[i:i+words_per_caption]
            if not segment_words:
                continue

            # Calculate start and end time for this segment
            start_time = segment_words[0]['offset']
            end_time = segment_words[-1]['offset'] + segment_words[-1]['duration']

            # Add small gap before next caption (except for first caption)
            if i > 0:
                start_time += gap_between_captions
                end_time += gap_between_captions

            # Combine words
            text = ' '.join([w['word'] for w in segment_words])

            caption_segments.append({
                'text': text,
                'start': start_time,
                'end': end_time
            })

        print(f"[OK] Creating {len(caption_segments)} caption segments")

        # Create caption clips
        for segment in caption_segments:
            try:
                text = segment['text']

                # Create PIL image with text
                # First, get text size
                dummy_img = Image.new('RGBA', (1, 1))
                dummy_draw = ImageDraw.Draw(dummy_img)
                bbox = dummy_draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Add padding
                padding = 20
                img_width = min(text_width + padding * 2, int(video_width * 0.9))
                img_height = text_height + padding * 2

                # Create image with or without background based on setting
                if bg_enabled:
                    # Create image with SOLID background color
                    img_rgb = Image.new('RGB', (img_width, img_height), bg_color)
                    draw = ImageDraw.Draw(img_rgb)

                    # Draw text centered
                    text_x = (img_width - text_width) // 2
                    text_y = padding
                    draw.text((text_x, text_y), text, font=font, fill=text_color)

                    # Convert to numpy array (writable copy)
                    frame = np.array(img_rgb).copy()
                else:
                    # Create image with TRANSPARENT background
                    img_rgba = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(img_rgba)

                    # Draw text centered with full opacity
                    text_x = (img_width - text_width) // 2
                    text_y = padding
                    draw.text((text_x, text_y), text, font=font, fill=text_color + (255,))  # Add alpha

                    # Convert to numpy array (writable copy)
                    frame = np.array(img_rgba).copy()

                print(f"  Caption frame shape: {frame.shape}, dtype: {frame.dtype}")
                print(f"  Caption text: '{text}' ({segment['start']:.2f}s - {segment['end']:.2f}s)")

                # Create ImageClip - already imported at module level
                clip = ImageClip(frame, is_mask=False)

                duration = segment['end'] - segment['start']
                try:
                    clip = clip.with_duration(duration)
                    clip = clip.with_start(segment['start'])
                except AttributeError:
                    clip = clip.set_duration(duration)
                    clip = clip.set_start(segment['start'])

                # Position based on settings
                if position == 'top':
                    y_pos = int(video_height * 0.1)
                elif position == 'center':
                    y_pos = 'center'
                else:  # bottom
                    y_pos = int(video_height * 0.75)

                try:
                    clip = clip.with_position(('center', y_pos))
                except AttributeError:
                    clip = clip.set_position(('center', y_pos))

                print(f"  Caption positioned at: {clip.pos}, size: {clip.size}")
                caption_clips.append(clip)

            except Exception as e:
                print(f"[WARNING] Error creating caption for '{segment['text']}': {e}")
                import traceback
                traceback.print_exc()
                continue

        return caption_clips


class AudioProcessor:
    """Audio processing module for BGM and voiceovers"""

    @staticmethod
    def get_voiceover_files(folder_path: Path) -> List[Path]:
        """Get audio files from voiceover folder sorted by number"""
        if not folder_path or not folder_path.exists():
            return []
        audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
        files = [f for f in folder_path.iterdir()
                if f.suffix.lower() in audio_extensions and f.is_file()]

        # Sort by number in filename (1.mp3, 2.mp3, etc.)
        def extract_number(filepath):
            import re
            match = re.search(r'(\d+)', filepath.stem)
            return int(match.group(1)) if match else 999999

        return sorted(files, key=extract_number)

    @staticmethod
    def get_bgm_files(bgm_path: str) -> List[Path]:
        """Get BGM files - supports single file or folder with multiple files"""
        bgm_path = Path(bgm_path)

        if not bgm_path.exists():
            return []

        audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}

        # Single file
        if bgm_path.is_file() and bgm_path.suffix.lower() in audio_extensions:
            return [bgm_path]

        # Folder with multiple files
        if bgm_path.is_dir():
            files = [f for f in bgm_path.iterdir()
                    if f.suffix.lower() in audio_extensions and f.is_file()]
            return sorted(files)

        return []

    @staticmethod
    def create_looped_audio(audio_clip, target_duration):
        """Loop audio to match video duration"""
        if audio_clip.duration >= target_duration:
            return subclip(audio_clip, 0, target_duration)
        else:
            loops_needed = int(np.ceil(target_duration / audio_clip.duration))
            clips = [audio_clip] * loops_needed
            looped = set_duration(CompositeAudioClip(clips), target_duration)
            return looped

    @staticmethod
    def mix_audio_tracks(video_clip, settings, voiceover_file: Optional[Path] = None, bgm_file: Optional[Path] = None):
        """Mix original audio, BGM, and voiceover"""
        audio_tracks = []

        # Original audio
        if video_clip.audio and not settings.get('mute_original_audio', False):
            # Convert percentage (0-200) to decimal (0.0-2.0)
            volume_percent = settings.get('original_audio_volume', 100)
            original_volume = volume_percent / 100.0
            original_audio = set_volume(video_clip.audio, original_volume)
            audio_tracks.append(original_audio)
            print(f"[OK] Original audio volume: {volume_percent}%")

        # Custom BGM (use provided bgm_file or fall back to settings)
        if settings.get('add_custom_bgm', False):
            bgm_path = bgm_file if bgm_file else (Path(settings['bgm_file']) if settings.get('bgm_file') else None)

            if bgm_path and bgm_path.exists():
                try:
                    bgm_audio = AudioFileClip(str(bgm_path))

                    if settings.get('bgm_loop', True):
                        bgm_audio = AudioProcessor.create_looped_audio(bgm_audio, video_clip.duration)
                    else:
                        bgm_audio = subclip(bgm_audio, 0, min(bgm_audio.duration, video_clip.duration))

                    bgm_volume = settings.get('bgm_volume', 0.3)
                    bgm_audio = set_volume(bgm_audio, bgm_volume)
                    audio_tracks.append(bgm_audio)
                    print(f"[OK] Added BGM: {bgm_path.name}")
                except Exception as e:
                    print(f"[WARNING] Could not load BGM: {e}")

        # Voiceover
        voiceover_audio_clip = None
        if voiceover_file and voiceover_file.exists():
            try:
                voiceover_audio = AudioFileClip(str(voiceover_file))
                voiceover_volume = settings.get('voiceover_volume', 1.0)
                voiceover_delay = settings.get('voiceover_delay', 0.0)

                voiceover_audio = set_volume(voiceover_audio, voiceover_volume)

                if voiceover_delay > 0:
                    silence = set_volume(set_duration(AudioFileClip(str(voiceover_file)), voiceover_delay), 0)
                    try:
                        voiceover_audio = CompositeAudioClip([silence, voiceover_audio.set_start(voiceover_delay)])
                    except:
                        voiceover_audio = CompositeAudioClip([silence, voiceover_audio.with_start(voiceover_delay)])

                voiceover_audio_clip = voiceover_audio  # Store for ducking
                audio_tracks.append(voiceover_audio)
                print(f"[OK] Added voiceover: {voiceover_file.name}")
            except Exception as e:
                print(f"[WARNING] Could not load voiceover: {e}")

        # Apply BGM auto-ducking if enabled and we have both BGM and voiceover
        if settings.get('audio_auto_ducking', False) and voiceover_audio_clip is not None and len(audio_tracks) > 1:
            try:
                ducking_amount = settings.get('audio_ducking_amount', 0.3)

                # Find BGM track (it's the one that's not voiceover)
                for i, track in enumerate(audio_tracks):
                    if track != voiceover_audio_clip:
                        # This is BGM or original audio - apply ducking during voiceover
                        # Simple approach: just reduce the volume of BGM track
                        # (constant reduction instead of time-varying for reliability)
                        ducked_track = None

                        # Try method 1: MoviePy 2.x with_effects
                        if ducked_track is None:
                            try:
                                from moviepy.audio.fx import MultiplyVolume
                                ducked_track = track.with_effects([MultiplyVolume(ducking_amount)])
                            except:
                                pass

                        # Try method 2: MoviePy 1.x volumex
                        if ducked_track is None:
                            try:
                                ducked_track = track.volumex(ducking_amount)
                            except:
                                pass

                        # Try method 3: Direct function call
                        if ducked_track is None:
                            try:
                                from moviepy.audio.fx.MultiplyVolume import multiply_volume
                                ducked_track = multiply_volume(track, ducking_amount)
                            except:
                                pass

                        # Fallback: keep original track (no ducking)
                        if ducked_track is None:
                            ducked_track = track
                            print(f"[WARNING] Could not apply ducking, keeping original BGM volume")

                        audio_tracks[i] = ducked_track

                print(f"[OK] Applied BGM auto-ducking ({int((1-ducking_amount)*100)}% reduction during voice)")
            except Exception as e:
                print(f"[WARNING] BGM ducking failed: {e}")

        # Mix all tracks
        if audio_tracks:
            # Composite multiple tracks
            if len(audio_tracks) == 1:
                final_audio = audio_tracks[0]
            else:
                final_audio = CompositeAudioClip(audio_tracks)

            # Apply audio normalization if enabled
            if settings.get('audio_normalize', False):
                try:
                    target_level_db = settings.get('audio_target_level', -20)

                    # Normalize audio to target level
                    # MoviePy doesn't have built-in normalization, so we do it manually
                    # Get max amplitude and calculate gain needed
                    def normalize_audio(audio_clip, target_db=-20):
                        """Normalize audio to target dB level"""
                        try:
                            # Get audio as numpy array
                            audio_array = audio_clip.to_soundarray()

                            # Find peak amplitude
                            max_amplitude = np.max(np.abs(audio_array))

                            if max_amplitude > 0:
                                # Calculate current dB level
                                current_db = 20 * np.log10(max_amplitude)

                                # Calculate required gain
                                gain_db = target_db - current_db
                                gain_linear = 10 ** (gain_db / 20)

                                # Apply gain (use volumex for smoother result)
                                normalized = set_volume(audio_clip, gain_linear)

                                print(f"[NORMALIZE] Peak: {max_amplitude:.4f} ({current_db:.1f} dB) → Target: {target_db} dB (gain: {gain_db:+.1f} dB)")
                                return normalized
                            else:
                                return audio_clip
                        except Exception as e:
                            print(f"[WARNING] Normalization failed: {e}")
                            return audio_clip

                    final_audio = normalize_audio(final_audio, target_level_db)
                    print(f"[OK] Applied audio normalization (target: {target_level_db} dB)")
                except Exception as e:
                    print(f"[WARNING] Audio normalization failed: {e}")

            return final_audio
        else:
            return None


class TextEffects:
    """Text animation and effects module"""

    @staticmethod
    def create_glow_image(img, glow_color=(255, 255, 255), intensity=8):
        """Add glow effect to text image"""
        glow = img.copy()
        for i in range(intensity):
            glow = glow.filter(ImageFilter.GaussianBlur(radius=2))

        result = Image.new('RGBA', img.size, (0, 0, 0, 0))
        result.paste(glow, (0, 0), glow)
        result.paste(img, (0, 0), img)
        return result

    @staticmethod
    def create_shadow_image(img, offset=6, blur=12):
        """Add drop shadow to image"""
        shadow = Image.new('RGBA',
                          (img.width + offset*2, img.height + offset*2),
                          (0, 0, 0, 0))
        shadow_mask = Image.new('RGBA', img.size, (0, 0, 0, 180))
        shadow.paste(shadow_mask, (offset, offset), img)
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur))

        result = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
        result.paste(shadow, (0, 0), shadow)
        result.paste(img, (offset//2, offset//2), img)
        return result

    @staticmethod
    def create_neon_glow(img, neon_color=(0, 255, 136)):
        """Create neon glow effect"""
        glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow)

        for i in range(20, 0, -2):
            alpha = int(255 * (i / 20) * 0.3)
            color = neon_color + (alpha,)
            temp = img.copy()
            temp = temp.filter(ImageFilter.GaussianBlur(radius=i))

        result = Image.new('RGBA', img.size, (0, 0, 0, 0))
        for i in range(15):
            blur_img = img.filter(ImageFilter.GaussianBlur(radius=i))
            result = Image.alpha_composite(result, blur_img)
        result = Image.alpha_composite(result, img)
        return result

    @staticmethod
    def apply_gradient_overlay(img, gradient_type='top_to_bottom', intensity=0.3):
        """Apply gradient overlay"""
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if gradient_type == 'top_to_bottom':
            for y in range(img.height):
                alpha = int(255 * intensity * (y / img.height))
                draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))
        elif gradient_type == 'bottom_to_top':
            for y in range(img.height):
                alpha = int(255 * intensity * ((img.height - y) / img.height))
                draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

        return Image.alpha_composite(img, overlay)


class QuoteImageGenerator:
    """Generate beautiful template-based background images for quotes"""

    TEMPLATES = {
        'gradient_sunset': {
            'colors': [(255, 94, 77), (255, 154, 158), (250, 208, 196)],
            'direction': 'diagonal',
            'text_color': '#FFFFFF',
            'description': 'Warm sunset gradient (motivational)'
        },
        'gradient_ocean': {
            'colors': [(26, 42, 108), (58, 96, 115), (107, 140, 140)],
            'direction': 'vertical',
            'text_color': '#FFFFFF',
            'description': 'Deep ocean gradient (calm, wisdom)'
        },
        'gradient_fire': {
            'colors': [(255, 65, 108), (255, 75, 43), (255, 168, 0)],
            'direction': 'radial',
            'text_color': '#FFFFFF',
            'description': 'Fire energy gradient (high energy)'
        },
        'gradient_purple_dream': {
            'colors': [(67, 67, 255), (156, 81, 182), (255, 109, 255)],
            'direction': 'diagonal',
            'text_color': '#FFFFFF',
            'description': 'Purple dream gradient (creative, spiritual)'
        },
        'gradient_mint_fresh': {
            'colors': [(11, 163, 96), (60, 186, 146), (130, 224, 170)],
            'direction': 'vertical',
            'text_color': '#FFFFFF',
            'description': 'Mint fresh gradient (growth, success)'
        },
        'solid_black': {
            'colors': [(0, 0, 0)],
            'direction': 'solid',
            'text_color': '#FFFFFF',
            'description': 'Minimalist black (bold, modern)'
        },
        'solid_navy': {
            'colors': [(20, 30, 48)],
            'direction': 'solid',
            'text_color': '#FFFFFF',
            'description': 'Deep navy (professional, trust)'
        },
        'gradient_golden_hour': {
            'colors': [(255, 195, 113), (251, 144, 98), (247, 106, 104)],
            'direction': 'horizontal',
            'text_color': '#FFFFFF',
            'description': 'Golden hour (warm, inspiring)'
        },
        'gradient_sky': {
            'colors': [(2, 170, 176), (0, 205, 172), (134, 253, 232)],
            'direction': 'vertical',
            'text_color': '#000000',
            'description': 'Sky blue gradient (hopeful, peaceful)'
        },
        'gradient_dark_purple': {
            'colors': [(35, 7, 77), (79, 46, 109), (117, 86, 142)],
            'direction': 'radial',
            'text_color': '#FFFFFF',
            'description': 'Dark purple (luxury, mystery)'
        }
    }

    @staticmethod
    def create_gradient(width, height, colors, direction='vertical'):
        """Create a gradient background image"""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        if direction == 'solid':
            img.paste(colors[0], [0, 0, width, height])
            return img

        if direction == 'vertical':
            for y in range(height):
                # Calculate color interpolation
                position = y / height
                color = QuoteImageGenerator._interpolate_colors(colors, position)
                draw.line([(0, y), (width, y)], fill=color)

        elif direction == 'horizontal':
            for x in range(width):
                position = x / width
                color = QuoteImageGenerator._interpolate_colors(colors, position)
                draw.line([(x, 0), (x, height)], fill=color)

        elif direction == 'diagonal':
            for y in range(height):
                for x in range(width):
                    position = (x + y) / (width + height)
                    color = QuoteImageGenerator._interpolate_colors(colors, position)
                    draw.point((x, y), fill=color)

        elif direction == 'radial':
            center_x, center_y = width // 2, height // 2
            max_distance = np.sqrt(center_x**2 + center_y**2)

            for y in range(height):
                for x in range(width):
                    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    position = distance / max_distance
                    color = QuoteImageGenerator._interpolate_colors(colors, position)
                    draw.point((x, y), fill=color)

        return img

    @staticmethod
    def _interpolate_colors(colors, position):
        """Interpolate between multiple colors based on position (0.0 to 1.0)"""
        if len(colors) == 1:
            return colors[0]

        # Clamp position
        position = max(0.0, min(1.0, position))

        # Calculate which colors to interpolate between
        num_segments = len(colors) - 1
        segment = position * num_segments
        segment_index = int(segment)

        if segment_index >= num_segments:
            return colors[-1]

        # Interpolate between two adjacent colors
        local_position = segment - segment_index
        color1 = colors[segment_index]
        color2 = colors[segment_index + 1]

        r = int(color1[0] + (color2[0] - color1[0]) * local_position)
        g = int(color1[1] + (color2[1] - color1[1]) * local_position)
        b = int(color1[2] + (color2[2] - color1[2]) * local_position)

        return (r, g, b)

    @staticmethod
    def create_quote_image(quote, template_name='gradient_sunset', width=1080, height=1920):
        """Create a beautiful quote image using a template"""
        if template_name not in QuoteImageGenerator.TEMPLATES:
            print(f"[WARNING] Template '{template_name}' not found, using 'gradient_sunset'")
            template_name = 'gradient_sunset'

        template = QuoteImageGenerator.TEMPLATES[template_name]

        # Create gradient background
        img = QuoteImageGenerator.create_gradient(
            width, height,
            template['colors'],
            template['direction']
        )

        # Add text overlay
        draw = ImageDraw.Draw(img)

        # Detect if quote contains emojis
        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+')
        has_emojis = bool(emoji_pattern.search(quote))

        # Try to load a font that supports emojis
        font_size = 80
        emoji_font = None
        text_font = None

        try:
            # For Windows: Use Segoe UI Emoji which supports emojis
            if has_emojis:
                emoji_font_path = "C:/Windows/Fonts/seguiemj.ttf"  # Segoe UI Emoji
                if os.path.exists(emoji_font_path):
                    emoji_font = ImageFont.truetype(emoji_font_path, font_size)
                    text_font = ImageFont.truetype(emoji_font_path, font_size)
                    print(f"[OK] Using Segoe UI Emoji font for emoji support")
                else:
                    # Fallback: strip emojis if emoji font not available
                    print(f"[WARNING] Emoji font not found, removing emojis from text")
                    quote = emoji_pattern.sub(' ', quote).strip()
                    quote = ' '.join(quote.split())  # Remove extra spaces
                    has_emojis = False

            # If no emojis or couldn't load emoji font, use Arial Bold
            if not has_emojis:
                font_path = "C:/Windows/Fonts/arialbd.ttf"
                if not os.path.exists(font_path):
                    font_path = "C:/Windows/Fonts/arial.ttf"
                text_font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"[WARNING] Font loading error: {e}, using default font")
            text_font = ImageFont.load_default()

        # Use the loaded font
        font = text_font

        # Word wrap the quote
        words = quote.split()
        lines = []
        current_line = []
        max_width = width - 200  # 100px padding on each side

        for word in words:
            test_line = ' '.join(current_line + [word])
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                # Fallback for older Pillow versions
                text_width = len(test_line) * (font_size // 2)

            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Calculate total text height
        line_height = font_size + 20
        total_text_height = len(lines) * line_height

        # Center text vertically
        start_y = (height - total_text_height) // 2

        # Parse text color
        text_color = tuple(int(template['text_color'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

        # Draw each line centered
        for i, line in enumerate(lines):
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # Fallback for older Pillow versions
                text_width = len(line) * (font_size // 2)
                text_height = font_size

            x = (width - text_width) // 2
            y = start_y + i * line_height

            # Add subtle shadow for better readability
            shadow_offset = 3
            shadow_color = (0, 0, 0, 128) if has_emojis else (0, 0, 0)
            try:
                draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)
            except:
                pass  # Skip shadow if it causes issues

            # Draw main text
            draw.text((x, y), line, font=font, fill=text_color)

        return img

    @staticmethod
    def generate_images_from_quotes(quotes_list, output_folder, template_name='auto'):
        """Generate images for a list of quotes"""
        output_folder = Path(output_folder)
        output_folder.mkdir(exist_ok=True, parents=True)

        # Auto-select templates based on quote content
        template_keywords = {
            'gradient_fire': ['energy', 'power', 'passion', 'motivation', 'action', 'hustle'],
            'gradient_ocean': ['calm', 'peace', 'wisdom', 'deep', 'think', 'mind'],
            'gradient_purple_dream': ['dream', 'creative', 'spiritual', 'soul', 'art', 'imagine'],
            'gradient_mint_fresh': ['success', 'growth', 'money', 'wealth', 'win', 'achieve'],
            'gradient_sunset': ['inspire', 'hope', 'life', 'love', 'beautiful', 'happy'],
            'gradient_dark_purple': ['luxury', 'mystery', 'secret', 'truth', 'deep'],
            'solid_black': ['bold', 'strong', 'power', 'minimal', 'modern']
        }

        generated_images = []

        for i, quote in enumerate(quotes_list):
            # Auto-select template based on quote content
            if template_name == 'auto':
                quote_lower = quote.lower()
                selected_template = 'gradient_sunset'  # default

                for tmpl, keywords in template_keywords.items():
                    if any(keyword in quote_lower for keyword in keywords):
                        selected_template = tmpl
                        break
            else:
                selected_template = template_name

            # Generate image
            img = QuoteImageGenerator.create_quote_image(quote, selected_template)

            # Save image
            filename = f"quote_{i+1}_{selected_template}.png"
            filepath = output_folder / filename
            img.save(filepath)

            generated_images.append(filepath)
            print(f"[OK] Generated image {i+1}/{len(quotes_list)}: {filename} (template: {selected_template})")

        return generated_images


class VideoQuoteAutomation:
    """Automate adding quotes to videos with advanced effects"""

    def __init__(self, video_folder=None, quotes_file=None, output_folder=None):
        # Use provided paths or fall back to defaults
        self.video_folder = Path(video_folder) if video_folder else Path(r"E:\MyAutomations\ScriptAutomations\VideoFolder\SourceVideosToEdit\Libriana8")
        self.quotes_file = Path(quotes_file) if quotes_file else Path(r"E:\MyAutomations\ScriptAutomations\VideoFolder\Quotes.txt")
        self.output_folder = Path(output_folder) if output_folder else Path(r"E:\MyAutomations\ScriptAutomations\VideoFolder\FinalVideos")

        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.settings = self.load_settings()

        self.log_file = self.output_folder / "processing_log.json"
        self.processing_log = self._load_log()

        # Load voiceover files if enabled
        self.voiceover_files = []
        if self.settings.get('add_voiceover', False) and self.settings.get('voiceover_folder'):
            voiceover_folder = Path(self.settings['voiceover_folder'])
            self.voiceover_files = AudioProcessor.get_voiceover_files(voiceover_folder)
            if self.voiceover_files:
                print(f"[OK] Loaded {len(self.voiceover_files)} voiceover files (sorted by number)")
                for i, vf in enumerate(self.voiceover_files[:5], 1):
                    print(f"  {i}. {vf.name}")
            else:
                print(f"[WARNING] No voiceover files found in {voiceover_folder}")

        # Load BGM files if enabled
        self.bgm_files = []
        if self.settings.get('add_custom_bgm', False) and self.settings.get('bgm_file'):
            self.bgm_files = AudioProcessor.get_bgm_files(self.settings['bgm_file'])
            if self.bgm_files:
                if len(self.bgm_files) == 1:
                    print(f"[OK] Loaded 1 BGM file: {self.bgm_files[0].name}")
                else:
                    print(f"[OK] Loaded {len(self.bgm_files)} BGM files (will select randomly per video)")
                    for i, bf in enumerate(self.bgm_files[:5], 1):
                        print(f"  {i}. {bf.name}")
            else:
                print(f"[WARNING] No BGM files found")

    def load_settings(self) -> dict:
        """Load settings from GUI config file"""
        settings_file = Path('overlay_settings.json')

        default_settings = {
            'font_size': 45,
            'font_style': 'Arial Bold',
            'text_color': '#000000',
            'bg_color': '#FFFFFF',
            'bg_opacity': 90,
            'cta_enabled': True,
            'cta_font_size': 43,
            'cta_font_style': 'Arial Italic',
            'cta_bg_color': '#DC2626',
            'cta_text_color': '#FFFFFF',
            'emoji_enabled': True,
            'emoji_size_multiplier': 1.2,
            'bubble_width': 75,
            'padding_horizontal': 40,
            'padding_vertical': 20,
            'inner_padding': 15,
            'section_spacing': 15,
            'corner_radius': 15,
            'position': 'top',
            'text_fade_in': True,
            'text_fade_duration': 0.4,
            'text_glow': True,
            'glow_intensity': 8,
            'vignette': True,
            'vignette_intensity': 0.4,
            'video_zoom': True,
            'zoom_scale': 1.08,
            'drop_shadow': True,
            'shadow_offset': 6,
            'shadow_blur': 12
        }

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    print("[OK] Loaded enhanced settings from overlay_settings.json")
                    return loaded_settings
            except Exception as e:
                print(f"[WARNING] Could not load settings: {e}")
                return default_settings
        else:
            print("[WARNING] No settings file found")
            return default_settings

    def _load_log(self) -> dict:
        """Load processing log"""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"processed_count": 0, "processed_videos": []}

    def _save_log(self):
        """Save processing log"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.processing_log, f, indent=2, ensure_ascii=False)

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def read_quotes(self) -> List[dict]:
        """
        Read quotes from file(s) with support for separate subtitle and voiceover text.

        Format options:
        1. Single file (Quotes.txt only): Same text for subtitle and voiceover
        2. Two separate files: Quotes.txt for subtitles, VoiceoverText.txt for voiceover
           - Line 1 in Quotes.txt pairs with line 1 in VoiceoverText.txt
           - Line 2 in Quotes.txt pairs with line 2 in VoiceoverText.txt, etc.

        Returns list of dicts with 'subtitle' and 'voiceover' keys.
        """
        print(f"[DEBUG] Attempting to read quotes from: {self.quotes_file}")
        print(f"[DEBUG] File exists: {self.quotes_file.exists()}")

        if not self.quotes_file.exists():
            print(f"✗ Quotes file not found: {self.quotes_file}")
            return []

        # Read subtitle text (from Quotes.txt)
        with open(self.quotes_file, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()

        print(f"[DEBUG] File content length: {len(subtitle_content)} characters")
        print(f"[DEBUG] First 100 chars: {subtitle_content[:100]}")

        subtitle_lines = []
        if re.match(r'^\s*\d+\.', subtitle_content, re.MULTILINE):
            print(f"[DEBUG] Detected numbered format")
            parts = re.split(r'\n\s*\d+\.\s*', subtitle_content)
            print(f"[DEBUG] Split into {len(parts)} parts")
            subtitle_lines = [q.strip() for q in parts[1:] if q.strip()]
            print(f"[DEBUG] After filtering: {len(subtitle_lines)} lines")
        elif '\n\n' in subtitle_content:
            print(f"[DEBUG] Detected paragraph format (\\n\\n)")
            subtitle_lines = [q.strip() for q in subtitle_content.split('\n\n') if q.strip()]
        elif '---' in subtitle_content:
            print(f"[DEBUG] Detected dash separator format")
            subtitle_lines = [q.strip() for q in subtitle_content.split('---') if q.strip()]
        else:
            print(f"[DEBUG] Using line-by-line format")
            subtitle_lines = [line.strip() for line in subtitle_content.split('\n') if line.strip()]

        print(f"[DEBUG] Before cleaning: {len(subtitle_lines)} subtitle lines")

        # Clean subtitle lines
        subtitle_lines = [re.sub(r'^\d+\.\s*', '', line).strip() for line in subtitle_lines if line.strip()]

        print(f"[DEBUG] After cleaning: {len(subtitle_lines)} subtitle lines")

        # Check for separate voiceover text file
        voiceover_text_file = self.settings.get('voiceover_text_file', '')
        voiceover_lines = []

        if voiceover_text_file and Path(voiceover_text_file).exists():
            print(f"[OK] Using separate voiceover text file: {Path(voiceover_text_file).name}")
            with open(voiceover_text_file, 'r', encoding='utf-8') as f:
                voiceover_content = f.read()

            # Parse voiceover file same way as subtitle file
            if re.match(r'^\s*\d+\.', voiceover_content, re.MULTILINE):
                parts = re.split(r'\n\s*\d+\.\s*', voiceover_content)
                voiceover_lines = [q.strip() for q in parts[1:] if q.strip()]
            elif '\n\n' in voiceover_content:
                voiceover_lines = [q.strip() for q in voiceover_content.split('\n\n') if q.strip()]
            elif '---' in voiceover_content:
                voiceover_lines = [q.strip() for q in voiceover_content.split('---') if q.strip()]
            else:
                voiceover_lines = [line.strip() for line in voiceover_content.split('\n') if line.strip()]

            # Clean voiceover lines
            voiceover_lines = [re.sub(r'^\d+\.\s*', '', line).strip() for line in voiceover_lines if line.strip()]

            if len(voiceover_lines) != len(subtitle_lines):
                print(f"[WARNING] Warning: Subtitle file has {len(subtitle_lines)} lines, Voiceover file has {len(voiceover_lines)} lines")
                print(f"  → Will use minimum count: {min(len(subtitle_lines), len(voiceover_lines))}")
        else:
            print(f"[OK] Using Quotes.txt for both subtitle and voiceover")
            voiceover_lines = subtitle_lines  # Use same text for both

        # Pair subtitle and voiceover lines
        processed_quotes = []
        min_count = min(len(subtitle_lines), len(voiceover_lines)) if voiceover_lines else len(subtitle_lines)

        for i in range(min_count):
            subtitle_text = subtitle_lines[i]
            voiceover_text = voiceover_lines[i] if voiceover_lines else subtitle_text

            processed_quotes.append({
                'subtitle': subtitle_text,
                'voiceover': voiceover_text
            })

        print(f"[OK] Loaded {len(processed_quotes)} quotes")

        if processed_quotes:
            print(f"\nFirst 3 quotes:")
            for i, quote_data in enumerate(processed_quotes[:3], 1):
                subtitle_preview = quote_data['subtitle'][:80] + "..." if len(quote_data['subtitle']) > 80 else quote_data['subtitle']
                print(f"  {i}. Subtitle: {subtitle_preview}")
                if quote_data['subtitle'] != quote_data['voiceover']:
                    voiceover_preview = quote_data['voiceover'][:80] + "..." if len(quote_data['voiceover']) > 80 else quote_data['voiceover']
                    print(f"     Voiceover: {voiceover_preview}")

        return processed_quotes

    def get_video_files(self, sort_by: str = 'created') -> List[Path]:
        """Get video files from folder"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}

        if not self.video_folder.exists():
            print(f"✗ Video folder not found: {self.video_folder}")
            return []

        videos = [f for f in self.video_folder.iterdir()
                 if f.suffix.lower() in video_extensions and f.is_file()]

        if sort_by == 'created':
            videos = sorted(videos, key=lambda x: x.stat().st_ctime)
            print(f"[OK] Found {len(videos)} videos (sorted by creation date)")
        elif sort_by == 'modified':
            videos = sorted(videos, key=lambda x: x.stat().st_mtime)
            print(f"[OK] Found {len(videos)} videos (sorted by modification date)")
        else:
            videos = sorted(videos)
            print(f"[OK] Found {len(videos)} videos (sorted alphabetically)")

        if videos:
            print(f"\nFirst 5 videos:")
            for i, video in enumerate(videos[:5], 1):
                print(f"  {i}. {video.name}")

        return videos

    def generate_hashtags(self, quote: str) -> List[str]:
        """Generate relevant hashtags from quote"""
        quote_lower = quote.lower()

        hashtag_map = {
            'success': '#Success', 'motivation': '#Motivation', 'inspire': '#Inspiration',
            'life': '#Life', 'love': '#Love', 'happy': '#Happiness', 'dream': '#Dreams',
            'work': '#Work', 'business': '#Business', 'money': '#Money', 'goal': '#Goals',
            'achieve': '#Achievement', 'believe': '#Believe', 'hope': '#Hope',
            'strength': '#Strength', 'courage': '#Courage', 'change': '#Change',
            'wisdom': '#Wisdom', 'mindset': '#Mindset', 'grow': '#Growth',
            'leader': '#Leadership', 'hustle': '#Hustle', 'focus': '#Focus',
            'passion': '#Passion', 'gratitude': '#Gratitude', 'positive': '#Positivity'
        }

        found = []
        for keyword, hashtag in hashtag_map.items():
            if keyword in quote_lower and hashtag not in found:
                found.append(hashtag)
                if len(found) == 2:
                    break

        if len(found) < 2:
            defaults = ['#Motivation', '#Quotes', '#Inspiration', '#Wisdom']
            for tag in defaults:
                if tag not in found:
                    found.append(tag)
                    if len(found) == 2:
                        break

        return found[:2]

    def sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """Convert text to valid filename"""
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > max_length - 4:
            text = text[:max_length - 4]
        return text

    def create_filename(self, quote: str, hashtags: List[str]) -> str:
        """Create filename from quote and hashtags"""
        filename_text = f"{quote} {' '.join(hashtags)}"
        filename = self.sanitize_filename(filename_text, max_length=96)
        return filename + ".mp4"

    def create_text_overlay_image(self, video_width, video_height, title_text, main_text, cta_text, cta_emojis):
        """Create text overlay with Title + Quote + CTA format (with colorful CTA emojis)"""
        img_width = video_width
        temp_img = Image.new('RGBA', (img_width, 1000), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # Load separate fonts for Title, Quote, and CTA
        try:
            # Title font
            title_font_size = self.settings.get('title_font_size', 45)
            title_font_file = self.settings.get('title_font_file', 'arialbd.ttf')
            if not Path(title_font_file).exists():
                title_font_file = str(Path(r"C:\Windows\Fonts") / Path(title_font_file).name)
            title_font = ImageFont.truetype(title_font_file, title_font_size)

            # Quote font
            quote_font_size = self.settings.get('quote_font_size', 35)
            quote_font_file = self.settings.get('quote_font_file', 'ANTQUAB.TTF')
            if not Path(quote_font_file).exists():
                quote_font_file = str(Path(r"C:\Windows\Fonts") / Path(quote_font_file).name)
            quote_font = ImageFont.truetype(quote_font_file, quote_font_size)

            # CTA font
            cta_font_size = self.settings.get('cta_font_size', 43)
            cta_font_file = self.settings.get('cta_font_file', 'ariali.ttf')
            if not Path(cta_font_file).exists():
                cta_font_file = str(Path(r"C:\Windows\Fonts") / Path(cta_font_file).name)
            cta_font = ImageFont.truetype(cta_font_file, cta_font_size)

            # Emoji font
            emoji_font_path = str(Path(r"C:\Windows\Fonts") / 'seguiemj.ttf')
            emoji_font = ImageFont.truetype(emoji_font_path, int(cta_font_size * 1.2))

        except Exception as e:
            print(f"[WARNING] Font loading error: {e}")
            title_font = ImageFont.load_default()
            quote_font = title_font
            cta_font = title_font
            emoji_font = title_font

        max_text_width = int(img_width * (self.settings['bubble_width'] / 100))
        words = main_text.split()
        lines = []
        current_line = []

        # Wrap text using quote font
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=quote_font)
            if bbox[2] - bbox[0] <= max_text_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))

        main_text_wrapped = '\n'.join(lines)

        sections = []

        # Add title section (if exists and enabled)
        if self.settings.get('title_enabled', True) and title_text:
            sections.append((title_text, title_font, False, 'title', None))

        # Add main quote section (if exists and enabled)
        if self.settings.get('quote_enabled', True) and main_text_wrapped:
            sections.append((main_text_wrapped, quote_font, True, 'main', None))

        # Add CTA section with emojis (if exists and enabled)
        if self.settings.get('cta_enabled', True) and cta_text:
            sections.append((cta_text, cta_font, False, 'cta', cta_emojis))

        section_boxes = []
        for text, font, is_multiline, section_type, emojis in sections:
            if is_multiline:
                bbox = temp_draw.multiline_textbbox((0, 0), text, font=font, align='center')
            else:
                bbox = temp_draw.textbbox((0, 0), text, font=font)

            # For CTA with emojis, measure combined width (text + emojis)
            total_width = bbox[2] - bbox[0]
            if emojis:
                emoji_str = ' '.join(emojis)
                emoji_bbox = temp_draw.textbbox((0, 0), emoji_str, font=emoji_font)
                emoji_width = emoji_bbox[2] - emoji_bbox[0]
                total_width += emoji_width + 20  # Add spacing between text and emojis

            section_boxes.append({
                'text': text,
                'font': font,
                'is_multiline': is_multiline,
                'type': section_type,
                'emojis': emojis,
                'width': total_width,
                'height': bbox[3] - bbox[1]
            })

        total_height = sum(box['height'] for box in section_boxes)
        total_height += (len(section_boxes) - 1) * self.settings['section_spacing']
        total_height += self.settings['padding_vertical'] * 2
        total_height += len(section_boxes) * self.settings['inner_padding'] * 2

        box_height = int(total_height + 100)
        box_width = img_width

        extra_margin = 0
        if self.settings.get('drop_shadow', False):
            extra_margin = self.settings.get('shadow_offset', 6) * 2

        img = Image.new('RGBA', (box_width + extra_margin, box_height + extra_margin), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Get separate background colors for Title, Quote, and CTA
        title_bg_rgb = self.hex_to_rgb(self.settings.get('title_bg_color', '#ffffff'))
        title_bg_alpha = int(255 * (self.settings.get('title_bg_opacity', 92) / 100))
        title_bg = title_bg_rgb + (title_bg_alpha,)

        quote_bg_rgb = self.hex_to_rgb(self.settings.get('quote_bg_color', '#ffffff'))
        quote_bg_alpha = int(255 * (self.settings.get('quote_bg_opacity', 92) / 100))
        quote_bg = quote_bg_rgb + (quote_bg_alpha,)

        cta_bg_rgb = self.hex_to_rgb(self.settings.get('cta_bg_color', '#00ff40'))
        cta_bg_alpha = int(255 * (self.settings.get('cta_bg_opacity', 100) / 100))
        cta_bg = cta_bg_rgb + (cta_bg_alpha,)

        if self.settings['position'] == 'top':
            current_y = self.settings['padding_vertical']
        elif self.settings['position'] == 'center':
            current_y = (box_height - total_height) // 2
        else:
            current_y = box_height - total_height - self.settings['padding_vertical']

        for i, box_info in enumerate(section_boxes):
            text = box_info['text']
            font = box_info['font']
            is_multiline = box_info['is_multiline']
            section_type = box_info['type']
            section_emojis = box_info.get('emojis', None)

            is_cta = (section_type == 'cta')
            is_title = (section_type == 'title')
            is_quote = (section_type == 'main')

            # Use separate background and text colors for each section
            if is_title:
                current_bg = title_bg
                current_text_color = self.hex_to_rgb(self.settings.get('title_text_color', '#000000'))
            elif is_cta:
                current_bg = cta_bg
                current_text_color = self.hex_to_rgb(self.settings.get('cta_text_color', '#000000'))
            else:  # Quote
                current_bg = quote_bg
                current_text_color = self.hex_to_rgb(self.settings.get('quote_text_color', '#000000'))

            bubble_width = box_info['width'] + (self.settings['padding_horizontal'] * 2)
            bubble_height = box_info['height'] + (self.settings['inner_padding'] * 2)
            bubble_x = (box_width - bubble_width) // 2

            draw.rounded_rectangle(
                [(bubble_x, current_y), (bubble_x + bubble_width, current_y + bubble_height)],
                radius=self.settings['corner_radius'],
                fill=current_bg
            )

            if is_multiline:
                text_x = bubble_x + (bubble_width // 2)
                text_y = current_y + self.settings['inner_padding']
                draw.multiline_text(
                    (text_x, text_y),
                    text,
                    font=font,
                    fill=current_text_color,
                    align='center',
                    anchor='ma'
                )
            else:
                # For CTA with emojis, draw text first, then emojis with embedded_color
                if section_emojis:
                    # Measure text and emoji widths to position them side by side
                    text_bbox = temp_draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]

                    emoji_str = ' '.join(section_emojis)
                    emoji_bbox = temp_draw.textbbox((0, 0), emoji_str, font=emoji_font)
                    emoji_width = emoji_bbox[2] - emoji_bbox[0]

                    spacing = 10
                    total_content_width = text_width + spacing + emoji_width

                    # Draw text (left side)
                    text_x = bubble_x + (bubble_width - total_content_width) // 2
                    text_y = current_y + (bubble_height // 2)
                    draw.text(
                        (text_x, text_y),
                        text,
                        font=font,
                        fill=current_text_color,
                        anchor='lm'
                    )

                    # Draw emojis with embedded_color (right side, colorful!)
                    emoji_x = text_x + text_width + spacing
                    emoji_y = text_y
                    try:
                        draw.text(
                            (emoji_x, emoji_y),
                            emoji_str,
                            font=emoji_font,
                            embedded_color=True,  # COLORFUL EMOJIS!
                            anchor='lm'
                        )
                    except TypeError:
                        # Fallback for older Pillow versions
                        draw.text((emoji_x, emoji_y), emoji_str, font=emoji_font, anchor='lm')
                else:
                    # No emojis, just centered text
                    text_x = bubble_x + (bubble_width // 2)
                    text_y = current_y + (bubble_height // 2)
                    draw.text(
                        (text_x, text_y),
                        text,
                        font=font,
                        fill=current_text_color,
                        anchor='mm'
                    )

            current_y += bubble_height + self.settings['section_spacing']

        if self.settings.get('drop_shadow', False):
            img = TextEffects.create_shadow_image(
                img,
                offset=self.settings.get('shadow_offset', 6),
                blur=self.settings.get('shadow_blur', 12)
            )

        if self.settings.get('text_glow', False):
            glow_rgb = self.hex_to_rgb(self.settings.get('glow_color', '#ffffff'))
            img = TextEffects.create_glow_image(
                img,
                glow_color=glow_rgb,
                intensity=self.settings.get('glow_intensity', 8)
            )

        if self.settings.get('neon_glow', False):
            neon_rgb = self.hex_to_rgb(self.settings.get('neon_color', '#00ff88'))
            img = TextEffects.create_neon_glow(img, neon_color=neon_rgb)

        if self.settings.get('gradient_overlay', False):
            img = TextEffects.apply_gradient_overlay(
                img,
                gradient_type=self.settings.get('gradient_type', 'top_to_bottom'),
                intensity=self.settings.get('gradient_intensity', 0.3)
            )

        return img

    def add_quote_to_video(self, video_path: Path, quote: dict, video_index: int = 0) -> Tuple[Path, str]:
        """
        Add quote overlay with advanced effects.

        Args:
            video_path: Path to video file
            quote: Dictionary with 'subtitle' and 'voiceover' keys
                   - subtitle: Text shown in captions/overlay (short)
                   - voiceover: Text spoken in TTS (can include explanations)
            video_index: Index of current video

        Returns:
            Tuple of (output_path, output_filename)
        """
        # Extract subtitle and voiceover text
        # Support both dict format and legacy string format for backward compatibility
        if isinstance(quote, dict):
            subtitle_text = quote['subtitle']
            voiceover_text = quote['voiceover']
        else:
            # Backward compatible: treat as single string
            subtitle_text = quote
            voiceover_text = quote

        print(f"\n{'='*70}")
        print(f"Processing: {video_path.name}")
        print(f"Subtitle: {subtitle_text[:80]}...")
        if subtitle_text != voiceover_text:
            print(f"Voiceover: {voiceover_text[:80]}...")

        # Use subtitle text for hashtags and filename (visual elements)
        hashtags = self.generate_hashtags(subtitle_text)
        print(f"Hashtags: {', '.join(hashtags)}")

        output_filename = self.create_filename(subtitle_text, hashtags)
        print(f"Output: {output_filename}")

        video = VideoFileClip(str(video_path))

        # Apply chromatic aberration if enabled (apply to base video first)
        if self.settings.get('chromatic_aberration', False):
            try:
                intensity = int(self.settings.get('chromatic_intensity', 5))
                direction = self.settings.get('chromatic_direction', 'horizontal')

                print(f"\n[CHROMATIC] Applying RGB glitch effect...")
                print(f"[CHROMATIC] Intensity: {intensity}px, Direction: {direction}")

                def apply_chromatic(get_frame, t):
                    frame = get_frame(t)

                    # Ensure intensity is an integer for array slicing
                    shift = int(intensity)

                    # Separate RGB channels
                    r_channel = frame[:, :, 0].copy()
                    g_channel = frame[:, :, 1].copy()
                    b_channel = frame[:, :, 2].copy()

                    # Create shifted channels
                    h, w = frame.shape[:2]

                    if direction == 'horizontal' or direction == 'both':
                        # Shift red left, blue right
                        r_shifted = np.zeros_like(r_channel)
                        b_shifted = np.zeros_like(b_channel)

                        if shift < w and shift > 0:
                            r_shifted[:, shift:] = r_channel[:, :-shift]
                            b_shifted[:, :-shift] = b_channel[:, shift:]
                        else:
                            r_shifted = r_channel
                            b_shifted = b_channel

                        r_channel = r_shifted
                        b_channel = b_shifted

                    if direction == 'vertical' or direction == 'both':
                        # Shift red up, blue down
                        r_shifted = np.zeros_like(r_channel)
                        b_shifted = np.zeros_like(b_channel)

                        if shift < h and shift > 0:
                            r_shifted[shift:, :] = r_channel[:-shift, :]
                            b_shifted[:-shift, :] = b_channel[shift:, :]
                        else:
                            r_shifted = r_channel
                            b_shifted = b_channel

                        r_channel = r_shifted
                        b_channel = b_shifted

                    # Recombine channels
                    result = frame.copy()
                    result[:, :, 0] = r_channel
                    result[:, :, 2] = b_channel

                    return result

                video = video.transform(lambda gf, t: apply_chromatic(gf, t))
                print(f"[OK] Applied chromatic aberration ({direction}, {intensity}px offset)")
            except Exception as e:
                print(f"[WARNING] Chromatic aberration failed: {e}")
                import traceback
                traceback.print_exc()

        # Apply platform preset if enabled
        if self.settings.get('enable_platform_preset', False):
            platform = self.settings.get('platform_preset', 'none')
            if platform != 'none':
                print(f"\n[PLATFORM] Applying {platform} preset...")

                # Platform dimensions
                platform_dims = {
                    'instagram_reels': (1080, 1920),  # 9:16
                    'tiktok': (1080, 1920),           # 9:16
                    'youtube_shorts': (1080, 1920),   # 9:16
                    'youtube': (1920, 1080),          # 16:9
                    'facebook': (1080, 1080),         # 1:1
                }

                if platform in platform_dims:
                    target_w, target_h = platform_dims[platform]
                    target_aspect = target_w / target_h
                    current_aspect = video.w / video.h

                    crop_mode = self.settings.get('crop_mode', 'center')

                    print(f"[PLATFORM] Current: {video.w}x{video.h} ({current_aspect:.2f})")
                    print(f"[PLATFORM] Target: {target_w}x{target_h} ({target_aspect:.2f})")
                    print(f"[PLATFORM] Crop mode: {crop_mode}")

                    # Calculate scaling and cropping
                    if abs(current_aspect - target_aspect) > 0.01:  # Need to crop
                        if current_aspect > target_aspect:
                            # Video is wider - crop width
                            new_h = video.h
                            new_w = int(new_h * target_aspect)

                            if crop_mode == 'center':
                                x1 = (video.w - new_w) // 2
                            elif crop_mode == 'left':
                                x1 = 0
                            elif crop_mode == 'right':
                                x1 = video.w - new_w
                            else:  # smart or others default to center
                                x1 = (video.w - new_w) // 2

                            y1 = 0
                            x2 = x1 + new_w
                            y2 = video.h

                            video = video.crop(x1=x1, y1=y1, x2=x2, y2=y2)
                            print(f"[PLATFORM] Cropped width: {x1},{y1} to {x2},{y2}")
                        else:
                            # Video is taller - crop height
                            new_w = video.w
                            new_h = int(new_w / target_aspect)

                            if crop_mode == 'center':
                                y1 = (video.h - new_h) // 2
                            elif crop_mode == 'top':
                                y1 = 0
                            elif crop_mode == 'bottom':
                                y1 = video.h - new_h
                            else:  # smart or others default to center
                                y1 = (video.h - new_h) // 2

                            x1 = 0
                            x2 = video.w
                            y2 = y1 + new_h

                            video = video.crop(x1=x1, y1=y1, x2=x2, y2=y2)
                            print(f"[PLATFORM] Cropped height: {x1},{y1} to {x2},{y2}")

                    # Resize to target dimensions
                    video = video.resize((target_w, target_h))
                    print(f"[PLATFORM] Resized to: {target_w}x{target_h}")
                    print(f"[OK] Platform formatting complete!")

        emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+')

        # Parse subtitle text for visual display (Title + Quote + CTA format)
        # Expected format:
        # Line 1: Title (e.g., "When Marriage Gets Wild Fast")
        # Line 2-N: Main quote text
        # Last line: CTA with emojis (e.g., "👉 Prove You Relate! 😭")

        lines = subtitle_text.strip().split('\n')
        title_text = ""
        main_text = ""
        cta_text = ""
        cta_emojis = []

        if len(lines) >= 3:
            # Multi-line format: Title + Quote + CTA
            title_text = lines[0].strip()
            main_text = '\n'.join(lines[1:-1]).strip()
            last_line = lines[-1].strip()

            # Extract emojis from CTA line (preserve them for colorful display)
            cta_emojis_found = emoji_pattern.findall(last_line)
            cta_text_without_emojis = emoji_pattern.sub(' ', last_line).strip()

            # CTA is the last line (with emojis preserved separately)
            cta_text = cta_text_without_emojis
            cta_emojis = cta_emojis_found

        elif len(lines) == 2:
            # Two lines: Could be Title+Quote or Quote+CTA
            # Check if last line looks like CTA (short, has emojis)
            last_line = lines[-1].strip()
            last_line_emojis = emoji_pattern.findall(last_line)
            last_line_clean = emoji_pattern.sub(' ', last_line).strip()

            if last_line_emojis and len(last_line_clean.split()) < 10:
                # It's a CTA
                main_text = lines[0].strip()
                cta_text = last_line_clean
                cta_emojis = last_line_emojis
            else:
                # It's Title + Quote
                title_text = lines[0].strip()
                main_text = lines[1].strip()
        else:
            # Single line - treat as main text
            main_text = subtitle_text.strip()

        # Remove emojis from title and main text for clean display
        if title_text:
            title_text = emoji_pattern.sub(' ', title_text).strip()
        if main_text:
            main_text = emoji_pattern.sub(' ', main_text).strip()

        print(f"Title: {title_text[:50] if title_text else '(none)'}...")
        print(f"Main: {main_text[:60]}...")
        print(f"CTA: {cta_text}")
        print(f"CTA Emojis: {cta_emojis}")

        # Create static text overlay (quote bubble with Title + Quote + CTA format)
        # This is SEPARATE from word-by-word captions and both can be shown together
        img = self.create_text_overlay_image(video.w, video.h, title_text, main_text, cta_text, cta_emojis)
        img_array = np.array(img).copy()

        txt_clip = set_duration(ImageClip(img_array), video.duration)

        if self.settings.get('text_fade_in', False):
            fade_duration = self.settings.get('text_fade_duration', 0.4)
            if FadeIn:
                txt_clip = txt_clip.with_effects([FadeIn(fade_duration)])
            else:
                try:
                    txt_clip = txt_clip.fadein(fade_duration)
                except AttributeError:
                    pass  # Skip fade if not available

        if self.settings.get('text_bounce', False):
            bounce_intensity = self.settings.get('text_bounce_intensity', 1.15)
            def bounce_scale(t):
                if t < 0.6:
                    # Bounce in with overshoot
                    progress = t / 0.6
                    if progress < 0.5:
                        # Scale up quickly
                        scale = progress * 2 * bounce_intensity
                    else:
                        # Bounce back to normal
                        overshoot = (progress - 0.5) * 2
                        scale = bounce_intensity - (bounce_intensity - 1.0) * overshoot
                    return max(0.1, scale)
                return 1.0

            try:
                txt_clip = txt_clip.resize(lambda t: bounce_scale(t))
            except:
                pass

        elif self.settings.get('text_glitch', False):
            # Glitch effect: quick position shifts and opacity flicker
            def glitch_effect(get_frame, t):
                frame = get_frame(t)
                if t < 0.5:
                    # Random glitch during first 0.5s
                    if int(t * 30) % 3 == 0:  # Glitch every 3 frames
                        # Shift frame slightly
                        shift_x = np.random.randint(-10, 10)
                        shift_y = np.random.randint(-5, 5)
                        if shift_x > 0:
                            frame = np.roll(frame, shift_x, axis=1)
                        if shift_y > 0:
                            frame = np.roll(frame, shift_y, axis=0)
                return frame

            try:
                txt_clip = txt_clip.transform(glitch_effect)
            except:
                pass

        elif self.settings.get('text_slide_up', False):
            slide_distance = self.settings.get('text_slide_distance', 50)
            def slide_position(t):
                if t < 0.5:
                    offset = slide_distance * (1 - t / 0.5)
                    return ('center', video.h - txt_clip.h - offset) if self.settings['position'] == 'bottom' else ('center', offset)
                else:
                    if self.settings['position'] == 'top':
                        return ('center', 0)
                    elif self.settings['position'] == 'center':
                        return ('center', 'center')
                    else:
                        return ('center', video.h - txt_clip.h)
            txt_clip = set_position(txt_clip, slide_position)

        if not any([
            self.settings.get('text_bounce', False),
            self.settings.get('text_glitch', False),
            self.settings.get('text_slide_up', False)
        ]):
            if self.settings['position'] == 'top':
                txt_clip = set_position(txt_clip, ('center', 0))
            elif self.settings['position'] == 'center':
                txt_clip = set_position(txt_clip, ('center', 'center'))
            else:
                txt_clip = set_position(txt_clip, ('center', video.h - txt_clip.h))

        print(f"[OK] Static text overlay created at position: {self.settings['position']}")

        if self.settings.get('video_zoom', False):
            zoom_scale = self.settings.get('zoom_scale', 1.08)
            def zoom_effect(get_frame, t):
                frame = get_frame(t)
                progress = t / video.duration
                current_scale = 1 + (zoom_scale - 1) * progress
                h, w = frame.shape[:2]
                new_h, new_w = int(h * current_scale), int(w * current_scale)
                from PIL import Image as PILImage
                pil_frame = PILImage.fromarray(frame)
                pil_frame = pil_frame.resize((new_w, new_h), PILImage.LANCZOS)
                crop_x = (new_w - w) // 2
                crop_y = (new_h - h) // 2
                pil_frame = pil_frame.crop((crop_x, crop_y, crop_x + w, crop_y + h))
                return np.array(pil_frame).copy()
            try:
                video = video.transform(zoom_effect)
            except AttributeError:
                video = video.fl(zoom_effect)

        if self.settings.get('color_grade', 'none') != 'none':
            grade_type = self.settings.get('color_grade', 'warm')
            try:
                video = video.image_transform(lambda frame: VideoEffects.apply_color_grade(frame, grade_type))
            except AttributeError:
                video = video.fl_image(lambda frame: VideoEffects.apply_color_grade(frame, grade_type))

        if self.settings.get('vignette', False):
            intensity = self.settings.get('vignette_intensity', 0.4)
            try:
                video = video.image_transform(lambda frame: VideoEffects.apply_vignette(frame, intensity))
            except AttributeError:
                video = video.fl_image(lambda frame: VideoEffects.apply_vignette(frame, intensity))

        if self.settings.get('background_dim', False):
            intensity = self.settings.get('dim_intensity', 0.25)
            try:
                video = video.image_transform(lambda frame: VideoEffects.apply_background_dim(frame, intensity))
            except AttributeError:
                video = video.fl_image(lambda frame: VideoEffects.apply_background_dim(frame, intensity))

        if self.settings.get('film_grain', False):
            intensity = self.settings.get('grain_intensity', 0.15)
            try:
                video = video.image_transform(lambda frame: VideoEffects.apply_film_grain(frame, intensity))
            except AttributeError:
                video = video.fl_image(lambda frame: VideoEffects.apply_film_grain(frame, intensity))

        if self.settings.get('gradient_overlay', False):
            gradient_type = self.settings.get('gradient_type', 'top_to_bottom')
            intensity = self.settings.get('gradient_intensity', 0.3)
            try:
                video = video.image_transform(lambda frame: VideoEffects.apply_gradient_overlay(frame, gradient_type, intensity))
            except AttributeError:
                video = video.fl_image(lambda frame: VideoEffects.apply_gradient_overlay(frame, gradient_type, intensity))

        # Apply selective blur for watermark/logo hiding
        if self.settings.get('blur_watermark_enabled', False):
            print("  → Applying selective blur to hide watermark...")
            # Pass settings to the blur function
            VideoEffects.apply_selective_blur.settings = self.settings
            try:
                video = video.with_fps(video.fps).transform(VideoEffects.apply_selective_blur)
            except AttributeError:
                video = video.with_fps(video.fps).fl(VideoEffects.apply_selective_blur)


        # ========== FIX: Check TTS duration FIRST and loop video if needed ==========
        # This prevents frame reading errors when TTS audio is longer than source video
        target_duration = video.duration
        original_video_duration = video.duration

        if self.settings.get('use_tts_voiceover', False) and TTS_AVAILABLE:
            # Pre-calculate TTS duration to know if we need to loop the video
            # We'll generate TTS properly later, but need to estimate duration now
            tts_speed = self.settings.get('tts_speed', 130)
            # Estimate: ~150 WPM at default speed, adjust for user speed setting
            word_count = len(voiceover_text.split())
            estimated_tts_duration = (word_count / 150) * 60 * (150 / tts_speed)

            if estimated_tts_duration > video.duration:
                target_duration = estimated_tts_duration * 1.1  # Add 10% buffer
                print(f"[INFO] TTS will be ~{estimated_tts_duration:.1f}s, video is {video.duration:.1f}s - will loop video")

        # Loop video if target duration exceeds source video
        if target_duration > video.duration:
            try:
                loops_needed = int(np.ceil(target_duration / video.duration))
                print(f"[OK] Looping video {loops_needed}x to match TTS duration ({target_duration:.1f}s)")

                # Use time-based looping that wraps around - this actually creates new frames
                # instead of referencing the original file beyond its duration
                original_duration = video.duration

                # ========== FIX: Remove audio before looping to avoid transformation issues ==========
                # The audio will be replaced by TTS/BGM anyway, so remove it to avoid errors
                # caused by nested audio transformations when trying to loop
                original_audio = video.audio
                video = video.without_audio()

                def loop_time(get_frame, t):
                    """Loop video by wrapping time back to start"""
                    looped_t = t % original_duration
                    return get_frame(looped_t)

                try:
                    # MoviePy 2.x
                    video = video.transform(loop_time)
                    video = video.with_duration(target_duration)
                except AttributeError:
                    # MoviePy 1.x
                    video = video.fl(loop_time)
                    video = video.set_duration(target_duration)

                # Update txt_clip duration to match
                txt_clip = set_duration(txt_clip, target_duration)

                print(f"[OK] Video looped to {target_duration:.1f}s (audio will be added from TTS/BGM)")

            except Exception as e:
                print(f"[WARNING] Could not loop video: {e}")
                import traceback
                traceback.print_exc()

        # Start with video and static text overlay
        layers = [video, txt_clip]
        print(f"DEBUG: txt_clip size={txt_clip.size}, position={txt_clip.pos if hasattr(txt_clip, 'pos') else 'N/A'}, duration={txt_clip.duration}")
        print(f"DEBUG: video size={video.size}, duration={video.duration}")

        # ========== FIX: Combine all particle effects into single layer for faster rendering ==========
        # This reduces compositing operations from N layers to 1 combined layer
        particle_effects_enabled = []
        if self.settings.get('add_glitter', False):
            particle_effects_enabled.append('glitter')
        if self.settings.get('add_stars', False):
            particle_effects_enabled.append('stars')
        if self.settings.get('add_hearts', False):
            particle_effects_enabled.append('hearts')
        if self.settings.get('add_confetti', False):
            particle_effects_enabled.append('confetti')

        if particle_effects_enabled:
            try:
                # Create combined particle effect for better performance
                combined_particles = ParticleEffects.create_combined(
                    video.w, video.h, video.duration, video.fps,
                    glitter=self.settings.get('add_glitter', False),
                    glitter_intensity=self.settings.get('glitter_intensity', 0.5),
                    stars=self.settings.get('add_stars', False),
                    hearts=self.settings.get('add_hearts', False),
                    confetti=self.settings.get('add_confetti', False)
                )
                layers.append(combined_particles)
                print(f"[OK] Added combined particle effects: {', '.join(particle_effects_enabled)}")
            except Exception as e:
                print(f"[WARNING] Combined particle effect failed, using individual effects: {e}")
                # Fallback to individual effects
                if self.settings.get('add_glitter', False):
                    try:
                        intensity = self.settings.get('glitter_intensity', 0.5)
                        glitter = ParticleEffects.create_glitter(
                            video.w, video.h, video.duration, video.fps, intensity
                        )
                        layers.append(glitter)
                        print(f"[OK] Added glitter effect (intensity: {intensity})")
                    except Exception as e2:
                        print(f"[WARNING] Glitter effect failed: {e2}")

                if self.settings.get('add_stars', False):
                    try:
                        stars = ParticleEffects.create_stars(
                            video.w, video.h, video.duration, video.fps
                        )
                        layers.append(stars)
                        print("[OK] Added falling stars effect")
                    except Exception as e2:
                        print(f"[WARNING] Stars effect failed: {e2}")

                if self.settings.get('add_hearts', False):
                    try:
                        hearts = ParticleEffects.create_hearts(
                            video.w, video.h, video.duration, video.fps
                        )
                        layers.append(hearts)
                        print("[OK] Added falling hearts effect")
                    except Exception as e2:
                        print(f"[WARNING] Hearts effect failed: {e2}")

                if self.settings.get('add_confetti', False):
                    try:
                        confetti = ParticleEffects.create_confetti(
                            video.w, video.h, video.duration, video.fps
                        )
                        layers.append(confetti)
                        print("[OK] Added confetti effect")
                    except Exception as e2:
                        print(f"[WARNING] Confetti effect failed: {e2}")

        print(f"DEBUG: Compositing {len(layers)} layers...")
        final_video = CompositeVideoClip(layers)
        print(f"DEBUG: Composite created - size={final_video.size}, duration={final_video.duration:.2f}s")

        # Audio processing
        voiceover_file = None
        word_timings = []

        # Debug: Check caption and TTS settings
        print(f"DEBUG: enable_captions={self.settings.get('enable_captions', False)}, use_tts_voiceover={self.settings.get('use_tts_voiceover', False)}, TTS_AVAILABLE={TTS_AVAILABLE}")

        # Option 1: Generate TTS voiceover from text
        if self.settings.get('use_tts_voiceover', False) and TTS_AVAILABLE:
            tts_folder = self.output_folder / "tts_voiceovers"
            tts_folder.mkdir(exist_ok=True)

            tts_filename = f"tts_{video_index + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            tts_path = tts_folder / tts_filename

            # Generate TTS from the voiceover text (can include explanations)
            success, word_timings = TTSGenerator.generate_voiceover(voiceover_text, tts_path, self.settings)
            print(f"  → TTS generated from voiceover text ({len(voiceover_text)} chars)")
            if success:
                voiceover_file = tts_path
                print(f"[OK] Using TTS voiceover: {tts_filename}")

                # Fix placeholder timing values if needed
                if word_timings and word_timings[0]['offset'] < 100:  # Placeholder detection
                    try:
                        # Get actual audio duration
                        tts_audio = AudioFileClip(str(tts_path))
                        total_duration = tts_audio.duration
                        tts_audio.close()

                        # ========== FIX: Use character-weighted timing for better sync ==========
                        # Longer words take longer to say, so weight by character count
                        # This provides much better caption synchronization with TTS

                        word_count = len(word_timings)

                        # Calculate character count for each word (minimum 1 char)
                        word_lengths = []
                        for w in word_timings:
                            # Use character count, but weight short words slightly higher
                            # (words like "I", "a" still take some time to say)
                            char_count = len(w['word'])
                            # Minimum effective length of 2 chars for very short words
                            effective_length = max(2, char_count)
                            word_lengths.append(effective_length)

                        total_chars = sum(word_lengths)
                        if total_chars == 0:
                            total_chars = 1

                        # Distribute duration proportionally by character length
                        current_time = 0.0
                        for i, word_info in enumerate(word_timings):
                            word_info['offset'] = current_time
                            # Duration proportional to word length
                            word_duration = (word_lengths[i] / total_chars) * total_duration
                            word_info['duration'] = word_duration
                            current_time += word_duration

                        print(f"[OK] Calculated character-weighted timing: {len(word_timings)} words, {total_duration:.2f}s total")
                    except Exception as e:
                        print(f"[WARNING] Could not calculate word timing: {e}")

                # Save word timings for caption generation
                if word_timings:
                    timing_file = tts_path.with_suffix('.json')
                    with open(timing_file, 'w') as f:
                        json.dump(word_timings, f, indent=2)
                    print(f"[OK] Saved {len(word_timings)} word timings")

        # Option 2: Use pre-recorded voiceover files
        elif self.settings.get('add_voiceover', False) and self.voiceover_files:
            if video_index < len(self.voiceover_files):
                voiceover_file = self.voiceover_files[video_index]
                print(f"[OK] Using voiceover {video_index + 1}: {voiceover_file.name}")
            else:
                print(f"[WARNING] No voiceover file for video index {video_index + 1}")

        # Select BGM (random if multiple files)
        bgm_file = None
        if self.settings.get('add_custom_bgm', False) and self.bgm_files:
            if len(self.bgm_files) == 1:
                bgm_file = self.bgm_files[0]
            else:
                import random
                bgm_file = random.choice(self.bgm_files)
                print(f"🎵 Random BGM selected: {bgm_file.name}")

        final_audio = AudioProcessor.mix_audio_tracks(video, self.settings, voiceover_file, bgm_file)

        if final_audio:
            final_video = set_audio(final_video, final_audio)
        elif self.settings.get('mute_original_audio', False):
            final_video = final_video.without_audio()
            print("[OK] Original audio muted")

        # Add synchronized captions if enabled (either regular OR highlighted style)
        if self.settings.get('enable_captions', False) or self.settings.get('caption_highlight_enabled', False):
            try:
                caption_clips = []

                # IMPORTANT: Captions display subtitle_text (short), but sync with voiceover audio
                # We need to create timing for subtitle words based on voiceover duration
                if voiceover_file and voiceover_file.exists():
                    print(f"Adding synchronized captions for subtitle text...")
                    try:
                        tts_audio = AudioFileClip(str(voiceover_file))
                        audio_duration = tts_audio.duration
                        tts_audio.close()

                        # Use subtitle_text for captions (short heading)
                        # Timing is estimated based on voiceover duration
                        # Check if highlighted captions are enabled (CapCut style)
                        if self.settings.get('caption_highlight_enabled', False):
                            caption_clips = CaptionRenderer.create_highlighted_word_captions(
                                subtitle_text,
                                audio_duration,
                                video.w,
                                video.h,
                                self.settings
                            )
                        else:
                            caption_clips = CaptionRenderer.create_estimated_captions(
                                subtitle_text,
                                audio_duration,
                                video.w,
                                video.h,
                                self.settings
                            )
                        print(f"  → Captions show: {subtitle_text[:60]}...")
                        print(f"  → Synced to {audio_duration:.2f}s voiceover")
                    except Exception as e:
                        print(f"[WARNING] Could not get TTS audio duration: {e}")
                elif word_timings:
                    # If we have word timings but they're for voiceover_text,
                    # we still need to use subtitle_text for display
                    print(f"[WARNING] Word timings from voiceover don't match subtitle - using estimated timing")
                    # Try to estimate timing
                    if voiceover_file and voiceover_file.exists():
                        try:
                            tts_audio = AudioFileClip(str(voiceover_file))
                            audio_duration = tts_audio.duration
                            tts_audio.close()

                            # Check if highlighted captions are enabled (CapCut style)
                            if self.settings.get('caption_highlight_enabled', False):
                                caption_clips = CaptionRenderer.create_highlighted_word_captions(
                                    subtitle_text,
                                    audio_duration,
                                    video.w,
                                    video.h,
                                    self.settings
                                )
                            else:
                                caption_clips = CaptionRenderer.create_estimated_captions(
                                    subtitle_text,
                                    audio_duration,
                                    video.w,
                                    video.h,
                                    self.settings
                                )
                        except Exception as e:
                            print(f"[WARNING] Could not create captions: {e}")

                if caption_clips:
                    print(f"Compositing {len(caption_clips)} caption clips with video...")
                    # Composite video with captions
                    all_clips = [final_video] + caption_clips
                    final_video = CompositeVideoClip(all_clips)
                    print(f"[OK] Added {len(caption_clips)} caption segments")
                else:
                    print("[WARNING] No caption clips were created")

            except Exception as e:
                print(f"[WARNING] Caption rendering failed: {e}")
                import traceback
                traceback.print_exc()

        # Apply transitions if enabled
        print("\n[VIDEO] Applying transitions and effects...")

        # 1. Fade transitions
        if self.settings.get('transition_fade_in', False) or self.settings.get('transition_fade_out', False):
            try:
                fade_in_duration = self.settings.get('transition_fade_in_duration', 0.5) if self.settings.get('transition_fade_in', False) else 0
                fade_out_duration = self.settings.get('transition_fade_out_duration', 0.5) if self.settings.get('transition_fade_out', False) else 0

                if fade_in_duration > 0 or fade_out_duration > 0:
                    final_video = TransitionEffects.apply_fade_transition(final_video, fade_in_duration, fade_out_duration)
                    print(f"[OK] Applied fade transitions (in: {fade_in_duration}s, out: {fade_out_duration}s)")
            except Exception as e:
                print(f"[WARNING] Fade transition failed: {e}")

        # 2. Zoom transitions
        if self.settings.get('transition_zoom_in', False):
            try:
                duration = self.settings.get('transition_zoom_in_duration', 1.0)
                scale = self.settings.get('transition_zoom_scale', 1.3)
                final_video = TransitionEffects.create_zoom_transition(final_video, zoom_in=True, duration=duration, zoom_scale=scale)
                print(f"[OK] Applied zoom-in transition ({duration}s, scale: {scale})")
            except Exception as e:
                print(f"[WARNING] Zoom-in transition failed: {e}")

        if self.settings.get('transition_zoom_out', False):
            try:
                duration = self.settings.get('transition_zoom_out_duration', 1.0)
                scale = self.settings.get('transition_zoom_scale', 1.3)
                final_video = TransitionEffects.create_zoom_transition(final_video, zoom_in=False, duration=duration, zoom_scale=scale)
                print(f"[OK] Applied zoom-out transition ({duration}s, scale: {scale})")
            except Exception as e:
                print(f"[WARNING] Zoom-out transition failed: {e}")

        # 3. Blur transitions
        if self.settings.get('transition_blur_in', False):
            try:
                duration = self.settings.get('transition_blur_duration', 0.5)
                max_blur = self.settings.get('transition_blur_amount', 15)
                final_video = TransitionEffects.create_blur_transition(final_video, blur_in=True, duration=duration, max_blur=max_blur)
                print(f"[OK] Applied blur-in transition ({duration}s, blur: {max_blur})")
            except Exception as e:
                print(f"[WARNING] Blur-in transition failed: {e}")

        if self.settings.get('transition_blur_out', False):
            try:
                duration = self.settings.get('transition_blur_duration', 0.5)
                max_blur = self.settings.get('transition_blur_amount', 15)
                final_video = TransitionEffects.create_blur_transition(final_video, blur_in=False, duration=duration, max_blur=max_blur)
                print(f"[OK] Applied blur-out transition ({duration}s, blur: {max_blur})")
            except Exception as e:
                print(f"[WARNING] Blur-out transition failed: {e}")

        # 4. Slide transitions
        if self.settings.get('transition_slide_in', False):
            try:
                direction = self.settings.get('transition_slide_direction', 'left')
                duration = self.settings.get('transition_slide_duration', 0.8)
                final_video = TransitionEffects.create_slide_transition(final_video, direction=direction, in_transition=True, duration=duration)
                print(f"[OK] Applied slide-in transition (from {direction}, {duration}s)")
            except Exception as e:
                print(f"[WARNING] Slide-in transition failed: {e}")

        if self.settings.get('transition_slide_out', False):
            try:
                direction = self.settings.get('transition_slide_direction', 'left')
                duration = self.settings.get('transition_slide_duration', 0.8)
                final_video = TransitionEffects.create_slide_transition(final_video, direction=direction, in_transition=False, duration=duration)
                print(f"[OK] Applied slide-out transition (to {direction}, {duration}s)")
            except Exception as e:
                print(f"[WARNING] Slide-out transition failed: {e}")

        # 5. Wipe transitions
        if self.settings.get('transition_wipe_in', False):
            try:
                direction = self.settings.get('transition_wipe_direction', 'right')
                duration = self.settings.get('transition_wipe_duration', 0.8)
                final_video = TransitionEffects.create_wipe_transition(final_video, direction=direction, in_transition=True, duration=duration)
                print(f"[OK] Applied wipe-in transition ({direction}, {duration}s)")
            except Exception as e:
                print(f"[WARNING] Wipe-in transition failed: {e}")

        if self.settings.get('transition_wipe_out', False):
            try:
                direction = self.settings.get('transition_wipe_direction', 'right')
                duration = self.settings.get('transition_wipe_duration', 0.8)
                final_video = TransitionEffects.create_wipe_transition(final_video, direction=direction, in_transition=False, duration=duration)
                print(f"[OK] Applied wipe-out transition ({direction}, {duration}s)")
            except Exception as e:
                print(f"[WARNING] Wipe-out transition failed: {e}")

        # 6. Glitch transitions
        if self.settings.get('transition_glitch_start', False):
            try:
                duration = self.settings.get('transition_glitch_duration', 0.5)
                intensity = self.settings.get('transition_glitch_intensity', 0.5)
                final_video = TransitionEffects.create_glitch_transition(final_video, glitch_start=True, duration=duration, intensity=intensity)
                print(f"[OK] Applied glitch start transition ({duration}s, intensity: {intensity})")
            except Exception as e:
                print(f"[WARNING] Glitch start transition failed: {e}")

        if self.settings.get('transition_glitch_end', False):
            try:
                duration = self.settings.get('transition_glitch_duration', 0.5)
                intensity = self.settings.get('transition_glitch_intensity', 0.5)
                final_video = TransitionEffects.create_glitch_transition(final_video, glitch_start=False, duration=duration, intensity=intensity)
                print(f"[OK] Applied glitch end transition ({duration}s, intensity: {intensity})")
            except Exception as e:
                print(f"[WARNING] Glitch end transition failed: {e}")

        # 7. Cinematic bars
        if self.settings.get('transition_cinematic_bars', False):
            try:
                duration = self.settings.get('transition_bars_duration', 0.8)
                bar_height = self.settings.get('transition_bars_height', 10)
                final_video = TransitionEffects.create_cinematic_bars(final_video, fade_in=True, duration=duration, bar_height_percent=bar_height)
                print(f"[OK] Applied cinematic bars ({bar_height}% height)")
            except Exception as e:
                print(f"[WARNING] Cinematic bars failed: {e}")

        # 8. Light leaks and lens effects
        light_leak_layers = []

        if self.settings.get('light_leak_enabled', False):
            try:
                color = self.settings.get('light_leak_color', 'warm')
                intensity = self.settings.get('light_leak_intensity', 0.6)
                start_time = self.settings.get('light_leak_start_time', 0.0)
                leak_duration = self.settings.get('light_leak_duration', 3.0)
                direction = self.settings.get('light_leak_direction', 'top_right')
                repeat_enabled = self.settings.get('light_leak_repeat_enabled', False)
                repeat_interval = self.settings.get('light_leak_repeat_interval', 8.0)

                if repeat_enabled:
                    # Create multiple light leaks at intervals
                    current_time = start_time
                    count = 0
                    while current_time < final_video.duration:
                        light_leak = LightLeaksEffects.create_light_leak(
                            video.w, video.h, final_video.duration, video.fps,
                            color=color, intensity=intensity, start_time=current_time,
                            leak_duration=leak_duration, direction=direction
                        )
                        light_leak_layers.append(light_leak)
                        current_time += repeat_interval
                        count += 1
                    print(f"[OK] Added {count} repeated light leaks every {repeat_interval}s")
                else:
                    light_leak = LightLeaksEffects.create_light_leak(
                        video.w, video.h, final_video.duration, video.fps,
                        color=color, intensity=intensity, start_time=start_time,
                        leak_duration=leak_duration, direction=direction
                    )
                    light_leak_layers.append(light_leak)
                    print(f"[OK] Added light leak from {start_time}s for {leak_duration}s")
            except Exception as e:
                print(f"[WARNING] Light leak failed: {e}")

        if self.settings.get('lens_flare_enabled', False):
            try:
                intensity = self.settings.get('lens_flare_intensity', 0.5)
                start_time = self.settings.get('lens_flare_start_time', 1.0)
                flare_duration = self.settings.get('lens_flare_duration', 2.0)
                position = self.settings.get('lens_flare_position', 'center')

                repeat_enabled = self.settings.get('lens_flare_repeat_enabled', False)
                repeat_interval = self.settings.get('lens_flare_repeat_interval', 5.0)

                if repeat_enabled:
                    current_time = start_time
                    count = 0
                    while current_time < final_video.duration:
                        lens_flare = LightLeaksEffects.create_lens_flare(
                            video.w, video.h, final_video.duration, video.fps,
                            intensity=intensity, start_time=current_time,
                            flare_duration=flare_duration, position=position
                        )
                        light_leak_layers.append(lens_flare)
                        current_time += repeat_interval
                        count += 1
                    print(f"[OK] Added {count} repeated lens flares every {repeat_interval}s")
                else:
                    lens_flare = LightLeaksEffects.create_lens_flare(
                        video.w, video.h, final_video.duration, video.fps,
                        intensity=intensity, start_time=start_time,
                        flare_duration=flare_duration, position=position
                    )
                    light_leak_layers.append(lens_flare)
                    print(f"[OK] Added lens flare from {start_time}s for {flare_duration}s")
            except Exception as e:
                print(f"[WARNING] Lens flare failed: {e}")

        if self.settings.get('film_burn_enabled', False):
            try:
                start_time = self.settings.get('film_burn_start_time', 0.0)
                burn_duration = self.settings.get('film_burn_duration', 1.5)

                repeat_enabled = self.settings.get('film_burn_repeat_enabled', False)
                repeat_interval = self.settings.get('film_burn_repeat_interval', 10.0)

                if repeat_enabled:
                    current_time = start_time
                    count = 0
                    while current_time < final_video.duration:
                        film_burn = LightLeaksEffects.create_film_burn(
                            video.w, video.h, final_video.duration, video.fps,
                            start_time=current_time, burn_duration=burn_duration
                        )
                        light_leak_layers.append(film_burn)
                        current_time += repeat_interval
                        count += 1
                    print(f"[OK] Added {count} repeated film burns every {repeat_interval}s")
                else:
                    film_burn = LightLeaksEffects.create_film_burn(
                        video.w, video.h, final_video.duration, video.fps,
                        start_time=start_time, burn_duration=burn_duration
                    )
                    light_leak_layers.append(film_burn)
                    print(f"[OK] Added film burn from {start_time}s for {burn_duration}s")
            except Exception as e:
                print(f"[WARNING] Film burn failed: {e}")

        # Composite light leaks if any were added
        if light_leak_layers:
            try:
                all_layers = [final_video] + light_leak_layers
                final_video = CompositeVideoClip(all_layers)
                print(f"[OK] Composited {len(light_leak_layers)} light leak effects")
            except Exception as e:
                print(f"[WARNING] Light leak compositing failed: {e}")

        # Add watermark if enabled
        if self.settings.get('watermark_enabled', False):
            try:
                watermark_path = self.settings.get('watermark_image_path', '')
                if watermark_path and Path(watermark_path).exists():
                    # ImageClip already imported at module level
                    # Load watermark image
                    watermark = ImageClip(watermark_path)

                    # Get settings
                    position = self.settings.get('watermark_position', 'bottom-right')
                    opacity = self.settings.get('watermark_opacity', 70) / 100.0  # Convert to 0-1
                    scale = self.settings.get('watermark_scale', 0.15)  # Size relative to video width
                    margin_x = self.settings.get('watermark_margin_x', 20)
                    margin_y = self.settings.get('watermark_margin_y', 20)

                    # Resize watermark to scale relative to video width
                    new_width = int(video.w * scale)
                    watermark = watermark.resize(width=new_width)

                    # Set opacity
                    watermark = watermark.set_opacity(opacity)

                    # Calculate position
                    if position == 'top-left':
                        pos = (margin_x, margin_y)
                    elif position == 'top-right':
                        pos = (video.w - watermark.w - margin_x, margin_y)
                    elif position == 'bottom-left':
                        pos = (margin_x, video.h - watermark.h - margin_y)
                    elif position == 'bottom-right':
                        pos = (video.w - watermark.w - margin_x, video.h - watermark.h - margin_y)
                    elif position == 'center':
                        pos = ((video.w - watermark.w) / 2, (video.h - watermark.h) / 2)
                    else:
                        pos = (video.w - watermark.w - margin_x, video.h - watermark.h - margin_y)  # Default to bottom-right

                    # Set position and duration
                    watermark = watermark.set_position(pos).set_duration(final_video.duration)

                    # Composite watermark onto video
                    final_video = CompositeVideoClip([final_video, watermark])
                    print(f"[OK] Added watermark at {position} (opacity: {int(opacity*100)}%, scale: {int(scale*100)}%)")
                else:
                    print(f"[WARNING] Watermark enabled but image not found: {watermark_path}")
            except Exception as e:
                print(f"[WARNING] Watermark overlay failed: {e}")
                import traceback
                traceback.print_exc()

        # Add progress bar if enabled
        if self.settings.get('progress_bar', False):
            try:
                bar_height = self.settings.get('progress_bar_height', 5)
                bar_color_hex = self.settings.get('progress_color', '#00ff40')
                bar_position = self.settings.get('progress_bar_position', 'bottom')

                # Convert hex color to RGB
                bar_color = self.hex_to_rgb(bar_color_hex)

                # Create progress bar function
                def create_progress_bar(t):
                    # Calculate progress (0 to 1)
                    progress = t / final_video.duration

                    # Create bar image
                    bar_img = Image.new('RGB', (video.w, bar_height), (0, 0, 0))

                    # Draw progress portion
                    if progress > 0:
                        bar_width = int(video.w * progress)
                        for y in range(bar_height):
                            for x in range(bar_width):
                                bar_img.putpixel((x, y), bar_color)

                    return np.array(bar_img)

                # Create bar clip with time-varying width using VideoClip
                try:
                    from moviepy import VideoClip
                except ImportError:
                    from moviepy.editor import VideoClip

                bar_clip = VideoClip(create_progress_bar, duration=final_video.duration)
                try:
                    bar_clip = bar_clip.with_fps(video.fps)
                except:
                    bar_clip = bar_clip.set_fps(video.fps)

                # Position bar
                if bar_position == 'top':
                    try:
                        bar_clip = bar_clip.with_position((0, 0))
                    except:
                        bar_clip = bar_clip.set_position((0, 0))
                else:  # bottom
                    try:
                        bar_clip = bar_clip.with_position((0, video.h - bar_height))
                    except:
                        bar_clip = bar_clip.set_position((0, video.h - bar_height))

                # Composite onto video
                final_video = CompositeVideoClip([final_video, bar_clip])
                print(f"[OK] Added progress bar ({bar_position}, {bar_height}px, {bar_color_hex})")
            except Exception as e:
                print(f"[WARNING] Progress bar overlay failed: {e}")
                import traceback
                traceback.print_exc()

        # Add CTA overlay if enabled
        if self.settings.get('cta_overlay_enabled', False):
            try:
                cta_text = self.settings.get('cta_overlay_text', 'Follow for more! 👉')
                position = self.settings.get('cta_overlay_position', 'bottom-center')
                animation = self.settings.get('cta_overlay_animation', 'bounce')
                start_time = self.settings.get('cta_overlay_start_time', 3.0)
                duration = self.settings.get('cta_overlay_duration', 3.0)

                print(f"\n[CTA] Adding call-to-action overlay...")
                print(f"[CTA] Text: {cta_text}")
                print(f"[CTA] Position: {position}, Animation: {animation}")
                print(f"[CTA] Timing: {start_time}s - {start_time + duration}s")

                # Create CTA text image
                from PIL import ImageFont, ImageDraw

                # Use a large bold font
                try:
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 60)
                except:
                    font = ImageFont.load_default()

                # Calculate text size
                temp_img = Image.new('RGBA', (1, 1))
                draw = ImageDraw.Draw(temp_img)
                bbox = draw.textbbox((0, 0), cta_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Add padding
                padding = 30
                img_width = text_width + padding * 2
                img_height = text_height + padding * 2

                # Create text image with background
                cta_img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(cta_img)

                # Draw rounded rectangle background
                bg_color = (220, 38, 38, 230)  # Red with transparency
                draw.rounded_rectangle([(0, 0), (img_width, img_height)], radius=20, fill=bg_color)

                # Draw text
                draw.text((padding, padding), cta_text, font=font, fill=(255, 255, 255, 255))

                # Convert to array
                cta_array = np.array(cta_img)

                # Calculate position
                if position == 'top-left':
                    pos_x, pos_y = 30, 30
                elif position == 'top-center':
                    pos_x = (video.w - img_width) // 2
                    pos_y = 30
                elif position == 'top-right':
                    pos_x = video.w - img_width - 30
                    pos_y = 30
                elif position == 'bottom-left':
                    pos_x = 30
                    pos_y = video.h - img_height - 30
                elif position == 'bottom-center':
                    pos_x = (video.w - img_width) // 2
                    pos_y = video.h - img_height - 30
                else:  # bottom-right
                    pos_x = video.w - img_width - 30
                    pos_y = video.h - img_height - 30

                # Create text clip
                cta_clip = ImageClip(cta_array).with_duration(duration)
                cta_clip = cta_clip.with_start(start_time).with_position((pos_x, pos_y))

                # Apply animation
                if animation == 'bounce':
                    # Bounce in animation
                    def bounce_effect(t):
                        if t < 0.5:
                            # Bounce in
                            scale = 0.5 + 0.5 * (1 - (1 - t/0.5) ** 2)
                            return scale
                        else:
                            return 1.0

                    try:
                        cta_clip = cta_clip.resized(bounce_effect)
                    except:
                        cta_clip = cta_clip.resize(bounce_effect)

                elif animation == 'pulse':
                    # Pulsing animation
                    def pulse_effect(t):
                        return 1.0 + 0.1 * np.sin(t * 3 * np.pi)

                    try:
                        cta_clip = cta_clip.resized(pulse_effect)
                    except:
                        cta_clip = cta_clip.resize(pulse_effect)

                elif animation == 'slide-in':
                    # Slide in from bottom
                    def slide_pos(t):
                        if t < 0.5:
                            offset = int((1 - t/0.5) * 100)
                            return (pos_x, pos_y + offset)
                        return (pos_x, pos_y)

                    cta_clip = cta_clip.with_position(slide_pos)

                elif animation == 'fade-in':
                    # Fade in
                    def fade_opacity(t):
                        if t < 0.5:
                            return t / 0.5
                        return 1.0

                    cta_clip = cta_clip.with_opacity(fade_opacity)

                # Composite CTA onto video
                final_video = CompositeVideoClip([final_video, cta_clip])
                print(f"[OK] Added CTA overlay ({animation} animation, {duration}s duration)")
            except Exception as e:
                print(f"[WARNING] CTA overlay failed: {e}")
                import traceback
                traceback.print_exc()

        # Add particle effects
        particle_layers = []

        if self.settings.get('add_glitter', False):
            try:
                intensity = self.settings.get('glitter_intensity', 0.5)
                glitter = ParticleEffects.create_glitter(
                    video.w, video.h, final_video.duration, video.fps, intensity=intensity
                )
                particle_layers.append(glitter)
                print(f"[OK] Added glitter particles (intensity: {intensity})")
            except Exception as e:
                print(f"[WARNING] Glitter effect failed: {e}")

        if self.settings.get('add_stars', False):
            try:
                stars = ParticleEffects.create_stars(
                    video.w, video.h, final_video.duration, video.fps
                )
                particle_layers.append(stars)
                print(f"[OK] Added floating stars")
            except Exception as e:
                print(f"[WARNING] Stars effect failed: {e}")

        if self.settings.get('add_hearts', False):
            try:
                hearts = ParticleEffects.create_hearts(
                    video.w, video.h, final_video.duration, video.fps
                )
                particle_layers.append(hearts)
                print(f"[OK] Added floating hearts")
            except Exception as e:
                print(f"[WARNING] Hearts effect failed: {e}")

        if self.settings.get('add_confetti', False):
            try:
                confetti = ParticleEffects.create_confetti(
                    video.w, video.h, final_video.duration, video.fps
                )
                particle_layers.append(confetti)
                print(f"[OK] Added confetti particles")
            except Exception as e:
                print(f"[WARNING] Confetti effect failed: {e}")

        # Composite particle effects if any were added
        if particle_layers:
            try:
                all_layers = [final_video] + particle_layers
                final_video = CompositeVideoClip(all_layers)
                print(f"[OK] Composited {len(particle_layers)} particle effect(s)")
            except Exception as e:
                print(f"[WARNING] Particle compositing failed: {e}")

        output_path = self.output_folder / output_filename
        counter = 1
        original_output_path = output_path
        while output_path.exists():
            stem = original_output_path.stem
            output_path = self.output_folder / f"{stem}_{counter}.mp4"
            counter += 1

        print(f"Rendering with effects to: {output_path.name}")
        print(f"Video details: size={final_video.size}, duration={final_video.duration:.2f}s, fps={video.fps}")

        try:
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=video.fps,
                preset='medium',
                threads=4,
                logger='bar'  # Show progress bar
            )
            print(f"[OK] Rendering complete!")
        except Exception as e:
            print(f"✗ Rendering failed: {e}")
            import traceback
            traceback.print_exc()
            raise

        video.close()
        if txt_clip is not None:
            txt_clip.close()
        final_video.close()

        print(f"[OK] Saved: {output_path.name}")
        print(f"{'='*70}")

        return output_path, output_filename

    def process_single_video(self, video_path: Path, video_index: int = 0) -> dict:
        """
        Process a single video with quote overlay

        Args:
            video_path: Path to video file
            video_index: Index used to select corresponding quote

        Returns:
            Dictionary with processing result (status, output_file, etc.)
        """
        try:
            # Read quotes
            quotes = self.read_quotes()

            if not quotes:
                raise Exception("No quotes found in quotes file")

            # Get quote at index (cycle through quotes if more videos than quotes)
            quote_index = video_index % len(quotes)
            quote = quotes[quote_index]

            print(f"\n[OK] Processing video {video_index + 1}")
            print(f"[OK] Using quote {quote_index + 1}/{len(quotes)}")

            # Process the video
            output_path, filename = self.add_quote_to_video(video_path, quote, video_index=video_index)

            # Store subtitle and voiceover separately in log
            if isinstance(quote, dict):
                quote_log = {
                    'subtitle': quote['subtitle'],
                    'voiceover': quote['voiceover']
                }
            else:
                quote_log = quote

            # Log the result
            result = {
                'index': video_index,
                'original_video': video_path.name,
                'quote': quote_log,
                'output_file': filename,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }

            self.processing_log['processed_count'] += 1
            self.processing_log['processed_videos'].append(result)
            self._save_log()

            print(f"✓ Successfully processed: {filename}")

            return result

        except Exception as e:
            error_result = {
                'index': video_index,
                'original_video': video_path.name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            print(f"✗ Error processing video: {str(e)}")
            raise  # Re-raise so GUI can handle it

    def process_all(self, start_from: int = 0, sort_by: str = 'created', skip_processed: bool = False):
        """Process all videos with enhanced effects"""
        videos = self.get_video_files(sort_by=sort_by)
        quotes = self.read_quotes()

        if not videos:
            print("✗ No videos found!")
            return

        if not quotes:
            print("✗ No quotes found!")
            return

        # Filter out already processed videos if skip_processed is True
        if skip_processed:
            processed_videos = {entry['original_video'] for entry in self.processing_log.get('processed_videos', [])}
            original_count = len(videos)
            videos = [v for v in videos if v.name not in processed_videos]
            if original_count != len(videos):
                print(f"[OK] Skipped {original_count - len(videos)} already processed videos")
                print(f"[OK] Remaining videos to process: {len(videos)}")

        num_to_process = min(len(videos), len(quotes))

        if start_from >= num_to_process:
            print(f"✗ start_from ({start_from}) >= available pairs ({num_to_process})")
            return

        print(f"\n{'='*70}")
        print(f"ENHANCED BATCH PROCESSING")
        print(f"{'='*70}")
        print(f"Settings: overlay_settings.json")
        print(f"Effects enabled:")
        if self.settings.get('text_fade_in'): print("  [OK] Text fade-in")
        if self.settings.get('text_glow'): print("  [OK] Text glow")
        if self.settings.get('vignette'): print("  [OK] Vignette")
        if self.settings.get('video_zoom'): print("  [OK] Video zoom")
        if self.settings.get('drop_shadow'): print("  [OK] Drop shadow")
        if self.settings.get('color_grade', 'none') != 'none':
            print(f"  [OK] Color grade: {self.settings['color_grade']}")
        print(f"Videos: {len(videos)}")
        print(f"Quotes: {len(quotes)}")
        print(f"Processing: {num_to_process - start_from} video(s)")
        print(f"{'='*70}\n")

        results = []
        for i in range(start_from, num_to_process):
            video_path = videos[i]
            quote = quotes[i]

            print(f"\nProcessing {i + 1}/{num_to_process}")

            try:
                output_path, filename = self.add_quote_to_video(video_path, quote, video_index=i)

                # Store subtitle and voiceover separately in log
                if isinstance(quote, dict):
                    quote_log = {
                        'subtitle': quote['subtitle'],
                        'voiceover': quote['voiceover']
                    }
                else:
                    quote_log = quote

                result = {
                    'index': i,
                    'original_video': video_path.name,
                    'quote': quote_log,
                    'output_file': filename,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }
                results.append(result)

                self.processing_log['processed_count'] += 1
                self.processing_log['processed_videos'].append(result)
                self._save_log()

            except Exception as e:
                print(f"✗ Error: {str(e)}")
                result = {
                    'index': i,
                    'original_video': video_path.name,
                    'quote': quote,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)
                continue

        print(f"\n{'='*70}")
        print(f"PROCESSING COMPLETE!")
        print(f"{'='*70}")
        success_count = sum(1 for r in results if r['status'] == 'success')
        print(f"Success: {success_count}/{len(results)}")
        print(f"Output: {self.output_folder}")
        print(f"{'='*70}\n")

        return results


if __name__ == "__main__":
    print("Enhanced Video Quote Automation")
    print("="*70)

    automation = VideoQuoteAutomation()

    # Set skip_processed=True to avoid reprocessing the same videos
    # Set skip_processed=False to reprocess all videos (overwrite existing outputs)
    automation.process_all(
        start_from=0,
        sort_by='created',
        skip_processed=True  # Skip already processed videos
    )

    print("\n[OK] All done! Check FinalVideos folder.")
