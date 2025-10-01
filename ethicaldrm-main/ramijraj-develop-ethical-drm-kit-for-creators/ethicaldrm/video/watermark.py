# PASTE THIS ENTIRE CODE BLOCK INTO watermark.py

import cv2
from PIL import Image
import numpy as np
import os
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Watermarker:
    """Invisible video watermarking for user identification and leak detection."""
    
    def __init__(self, user_id: str, method: str = "lsb", strength: float = 0.1):
        self.user_id = user_id
        self.method = method
        self.strength = strength
        self.watermark_signature = self._generate_signature()
        
    def _generate_signature(self) -> str:
        """Generate unique signature for the user."""
        combined = f"{self.user_id}_{self.method}_{self.strength}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _embed_lsb_watermark(self, frame: np.ndarray, watermark_data: str) -> np.ndarray:
        """Embed watermark using LSB encoding in the blue channel."""
        height, width = frame.shape[:2]
        watermark_binary = ''.join(format(ord(char), '08b') for char in watermark_data)
        watermark_binary += '1111111111111110'  # End marker
        
        watermarked_frame = frame.copy()
        data_index = 0
        
        for y in range(height):
            for x in range(width):
                if data_index < len(watermark_binary):
                    pixel = watermarked_frame[y, x]
                    blue_channel = pixel[0]
                    blue_channel = (blue_channel & 0xFE) | int(watermark_binary[data_index])
                    watermarked_frame[y, x, 0] = blue_channel
                    data_index += 1
                else:
                    break
            if data_index >= len(watermark_binary):
                break
        return watermarked_frame

    def _embed_motion_blur_watermark(self, frame: np.ndarray) -> np.ndarray:
        """Embed subtle motion blur pattern based on user signature."""
        watermarked_frame = frame.copy().astype(np.float32)
        height, width = frame.shape[:2]
        pattern_seed = int(self.watermark_signature[:8], 16)
        np.random.seed(pattern_seed)
        kernel_size = 3
        angle = (pattern_seed % 180) * np.pi / 180
        kernel = np.zeros((kernel_size, kernel_size))
        for i in range(kernel_size):
            x = int(i * np.cos(angle))
            y = int(i * np.sin(angle))
            if 0 <= x < kernel_size and 0 <= y < kernel_size:
                kernel[x, y] = 1
        kernel = kernel / np.sum(kernel) if np.sum(kernel) > 0 else kernel
        region_size = 16
        for y in range(0, height - region_size, region_size * 4):
            for x in range(0, width - region_size, region_size * 4):
                if (x + y + pattern_seed) % 8 == 0:
                    region = watermarked_frame[y:y+region_size, x:x+region_size]
                    blurred_region = cv2.filter2D(region, -1, kernel)
                    alpha = self.strength * 0.1
                    watermarked_frame[y:y+region_size, x:x+region_size] = (alpha * blurred_region + (1 - alpha) * region)
        return watermarked_frame.astype(np.uint8)

    def _extract_lsb_watermark(self, frame: np.ndarray) -> Optional[Dict[str, str]]:
        """Extract LSB watermark from frame."""
        height, width = frame.shape[:2]
        binary_data = ""
        for y in range(height):
            for x in range(width):
                blue_channel = frame[y, x, 0]
                binary_data += str(blue_channel & 1)
                if binary_data.endswith('1111111111111110'):
                    binary_data = binary_data[:-16]

                    print(f"[Extract] Raw binary found: {binary_data}")
                    try:
                        text_data = ""
                        for i in range(0, len(binary_data), 8):
                            byte = binary_data[i:i+8]
                            if len(byte) == 8:
                                text_data += chr(int(byte, 2))
                                print(f"[Extract] Decoded text: '{text_data}'")
                        parts = text_data.split(':')
                        
                        if len(parts) == 3:
                           signature = parts[1]
                           frame_num = parts[2]
                           if len(signature) == 16 and frame_num.isdigit():
                               return {'user_id': parts[0], 'signature': signature, 'frame_number': frame_num}
                        else:
                             pass

                    except:
                        pass
                    return None
        return None
    
    # In watermark.py, replace the entire 'embed' function with this:

    # In watermark.py, replace the entire 'embed' function with this:
     # (And make sure "from PIL import Image" is at the top of the file)

    def embed(self, input_path: str, output_path: str, frame_interval: int = 30) -> Dict[str, Any]:
        """
        Embeds a watermark in either a video or an image file.
        """
        try:
          file_extension = os.path.splitext(input_path)[1].lower()
          image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']

          # --- IMAGE HANDLING LOGIC (Now using Pillow to save) ---
          if file_extension in image_extensions:
             logger.info(f"Processing as an image file: {input_path}")
            
             frame = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
             if frame is None:
                raise ValueError(f"Could not read the image file: {input_path}")
            
             if len(frame.shape) > 2 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
             watermark_data = f"{self.user_id}:{self.watermark_signature}:0"
             watermarked_frame = self._embed_lsb_watermark(frame, watermark_data)
            
             # --- FIX IS HERE: Save using Pillow ---
             # Convert color from OpenCV's BGR format to Pillow's standard RGB format
             rgb_frame = cv2.cvtColor(watermarked_frame, cv2.COLOR_BGR2RGB)
             pil_image = Image.fromarray(rgb_frame)
             pil_image.save(output_path)
             # --- END FIX ---
            
             file_size = os.path.getsize(output_path)
             return {
                'success': True, 'user_id': self.user_id, 'signature': self.watermark_signature,
                'total_frames': 1, 'watermarked_frames': 1, 'file_size': file_size
            }

          # --- VIDEO HANDLING LOGIC (Stays the same) ---
          else:
             logger.info(f"Processing as a video file: {input_path}")
             cap = cv2.VideoCapture(input_path)
             if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {input_path}")
             
             fps = cap.get(cv2.CAP_PROP_FPS)
             width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
             height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
             fourcc = cv2.VideoWriter_fourcc(*'FFV1')
             out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
             frame_count = 0
             watermarked_frames = 0
             while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % frame_interval == 0:
                    watermark_data = f"{self.user_id}:{self.watermark_signature}:{frame_count}"
                    watermarked_frame = self._embed_lsb_watermark(frame, watermark_data)
                    out.write(watermarked_frame)
                    watermarked_frames += 1
                else:
                    out.write(frame)
                frame_count += 1
            
                cap.release()
                out.release()
                file_size = os.path.getsize(output_path)
                return {
                   'success': True, 'user_id': self.user_id, 'signature': self.watermark_signature,
                   'total_frames': frame_count, 'watermarked_frames': watermarked_frames,
                   'file_size': file_size
                }  
            
        except Exception as e:
            logger.error(f"Watermarking failed: {str(e)}")
            print(f"Watermarking failed: {str(e)}")
            return {'success': False, 'error': str(e), 'user_id': self.user_id}
    
    def extract_watermark(self, video_path: str, method: str = None) -> Optional[Dict[str, str]]:
        """Extract watermark information from video."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            extraction_method = method or self.method
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if extraction_method == "lsb":
                    extracted = self._extract_lsb_watermark(frame)
                    if extracted and extracted.get('user_id'):
                        cap.release()
                        return extracted
            cap.release()
            return None
        except Exception as e:
            logger.error(f"Watermark extraction failed: {str(e)}")
            return None

    def verify_integrity(self, video_path: str) -> Dict[str, Any]:
        """Verify video integrity and watermark presence."""
        result = {'file_exists': os.path.exists(video_path), 'watermark_found': False, 'user_verified': False, 'integrity_score': 0.0}
        if not result['file_exists']:
            return result
        watermark_data = self.extract_watermark(video_path)
        if watermark_data:
            result['watermark_found'] = True
            result['user_verified'] = watermark_data.get('user_id') == self.user_id
            if result['user_verified']:
                result['integrity_score'] = 1.0
            else:
                result['integrity_score'] = 0.5
        return result