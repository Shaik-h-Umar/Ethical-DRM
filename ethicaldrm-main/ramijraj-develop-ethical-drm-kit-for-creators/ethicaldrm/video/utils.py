"""
Video utility functions for EthicalDRM.

Provides helper functions for video processing, format conversion,
and metadata extraction.
"""

import cv2
import ffmpeg
import numpy as np
import os
import hashlib
from typing import Dict, Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


class VideoUtils:
    """Utility class for video processing operations."""
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, any]:
        """
        Extract comprehensive video information.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")
            
            info = {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'codec': int(cap.get(cv2.CAP_PROP_FOURCC)),
                'file_size': os.path.getsize(video_path),
                'file_path': video_path
            }
            
            cap.release()
            
            # Add file hash for integrity checking
            info['file_hash'] = VideoUtils.calculate_file_hash(video_path)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return {}
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calculate file hash for integrity verification.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash: {str(e)}")
            return ""
    
    @staticmethod
    def extract_frames(video_path: str, output_dir: str, 
                      frame_interval: int = 30) -> List[str]:
        """
        Extract frames from video at specified intervals.
        
        Args:
            video_path: Path to input video
            output_dir: Directory to save frames
            frame_interval: Extract every N frames
            
        Returns:
            List of extracted frame paths
        """
        extracted_frames = []
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            cap = cv2.VideoCapture(video_path)
            
            frame_count = 0
            saved_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    frame_path = os.path.join(output_dir, f"frame_{saved_count:06d}.jpg")
                    cv2.imwrite(frame_path, frame)
                    extracted_frames.append(frame_path)
                    saved_count += 1
                
                frame_count += 1
            
            cap.release()
            logger.info(f"Extracted {len(extracted_frames)} frames")
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
        
        return extracted_frames
    
    @staticmethod
    def convert_video_format(input_path: str, output_path: str, 
                            output_format: str = 'mp4') -> bool:
        """
        Convert video to different format using ffmpeg.
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            output_format: Target format
            
        Returns:
            True if conversion successful
        """
        try:
            (
                ffmpeg
                .input(input_path)
                .output(output_path, format=output_format, vcodec='libx264', acodec='aac')
                .overwrite_output()
                .run(quiet=True)
            )
            logger.info(f"Video converted: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Video conversion failed: {str(e)}")
            return False
    
    @staticmethod
    def create_video_thumbnail(video_path: str, output_path: str, 
                              timestamp: float = 1.0) -> bool:
        """
        Create thumbnail from video at specified timestamp.
        
        Args:
            video_path: Path to video
            output_path: Path to save thumbnail
            timestamp: Time in seconds to capture thumbnail
            
        Returns:
            True if thumbnail created successfully
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Set position to timestamp
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(output_path, frame)
                cap.release()
                return True
            
            cap.release()
            return False
            
        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            return False
    
    @staticmethod
    def calculate_perceptual_hash(video_path: str, frame_count: int = 10) -> str:
        """
        Calculate perceptual hash for video content.
        
        Args:
            video_path: Path to video
            frame_count: Number of frames to sample
            
        Returns:
            Perceptual hash string
        """
        try:
            import imagehash
            from PIL import Image
            
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            hashes = []
            
            for i in range(frame_count):
                frame_pos = (i * total_frames) // frame_count
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                
                ret, frame = cap.read()
                if ret:
                    # Convert to PIL Image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Calculate perceptual hash
                    phash = imagehash.phash(pil_image)
                    hashes.append(str(phash))
            
            cap.release()
            
            # Combine hashes
            combined_hash = hashlib.sha256(''.join(hashes).encode()).hexdigest()
            return combined_hash[:32]  # Return first 32 characters
            
        except Exception as e:
            logger.error(f"Perceptual hash calculation failed: {str(e)}")
            return ""
    
    @staticmethod
    def compress_video(input_path: str, output_path: str, 
                      quality: str = 'medium') -> bool:
        """
        Compress video with specified quality settings.
        
        Args:
            input_path: Path to input video
            output_path: Path to compressed output
            quality: Compression quality ('low', 'medium', 'high')
            
        Returns:
            True if compression successful
        """
        quality_settings = {
            'low': {'crf': 28, 'preset': 'fast'},
            'medium': {'crf': 23, 'preset': 'medium'},
            'high': {'crf': 18, 'preset': 'slow'}
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    vcodec='libx264',
                    crf=settings['crf'],
                    preset=settings['preset'],
                    acodec='aac',
                    audio_bitrate='128k'
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            logger.info(f"Video compressed: {quality} quality")
            return True
            
        except Exception as e:
            logger.error(f"Video compression failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_video_file(video_path: str) -> Dict[str, bool]:
        """
        Validate video file integrity and readability.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'file_exists': False,
            'is_readable': False,
            'has_video_stream': False,
            'has_audio_stream': False,
            'is_corrupted': False
        }
        
        try:
            result['file_exists'] = os.path.exists(video_path)
            
            if result['file_exists']:
                cap = cv2.VideoCapture(video_path)
                result['is_readable'] = cap.isOpened()
                
                if result['is_readable']:
                    # Check if we can read at least one frame
                    ret, frame = cap.read()
                    result['has_video_stream'] = ret and frame is not None
                    
                    # Basic corruption check
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    result['is_corrupted'] = (frame_count <= 0 or fps <= 0)
                
                cap.release()
                
        except Exception as e:
            logger.error(f"Video validation failed: {str(e)}")
            result['is_corrupted'] = True
        
        return result