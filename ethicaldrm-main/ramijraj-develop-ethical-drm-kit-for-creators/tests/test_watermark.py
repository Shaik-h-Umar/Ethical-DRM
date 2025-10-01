"""
Test suite for EthicalDRM watermarking functionality.
"""

import unittest
import tempfile
import os
import numpy as np
import cv2
import time
from ethicaldrm.video.watermark import Watermarker


class TestWatermarker(unittest.TestCase):
    """Test cases for the Watermarker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_user_id = "test_user_123"
        self.watermarker = Watermarker(
            user_id=self.test_user_id,
            method="lsb",
            strength=0.1
        )
        
        # Create a simple test video
        self.test_video_path = tempfile.mktemp(suffix='.mp4')
        self.output_video_path = tempfile.mktemp(suffix='.mp4')
        self._create_test_video()
    
    def tearDown(self):
        """Clean up test fixtures."""
        for path in [self.test_video_path, self.output_video_path]:
            if os.path.exists(path):
                os.remove(path)
    
    def _create_test_video(self):
        """Create a simple test video for testing."""
        # --- CHANGE #1: Use .avi for the file extension ---
        self.test_video_path = tempfile.mktemp(suffix='.avi')
        self.output_video_path = tempfile.mktemp(suffix='.avi')

       # --- CHANGE #2: Use 'FFV1' for a lossless codec ---
        fourcc = cv2.VideoWriter_fourcc(*'FFV1') 
        out = cv2.VideoWriter(self.test_video_path, fourcc, 30.0, (640, 480))

        for i in range(5):
            frame = np.ones((480, 640, 3), dtype=np.uint8) * (i * 50 % 255)
            out.write(frame)

        out.release()
        time.sleep(1)
    
    def test_watermarker_initialization(self):
        """Test watermarker initialization."""
        self.assertEqual(self.watermarker.user_id, self.test_user_id)
        self.assertEqual(self.watermarker.method, "lsb")
        self.assertEqual(self.watermarker.strength, 0.1)
        self.assertIsNotNone(self.watermarker.watermark_signature)
        self.assertEqual(len(self.watermarker.watermark_signature), 16)
    
    def test_signature_generation(self):
        """Test watermark signature generation."""
        # Different users should have different signatures
        watermarker2 = Watermarker("different_user", "lsb", 0.1)
        self.assertNotEqual(
            self.watermarker.watermark_signature,
            watermarker2.watermark_signature
        )
        
        # Same parameters should generate same signature
        watermarker3 = Watermarker(self.test_user_id, "lsb", 0.1)
        self.assertEqual(
            self.watermarker.watermark_signature,
            watermarker3.watermark_signature
        )
    
    def test_lsb_watermark_embedding(self):
        """Test LSB watermark embedding in frames."""
        # Create a test frame
        frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        watermark_data = "test:signature:123"
        
        # Embed watermark
        watermarked_frame = self.watermarker._embed_lsb_watermark(frame, watermark_data)
        
        # Frame should be modified but similar
        self.assertEqual(watermarked_frame.shape, frame.shape)
        self.assertFalse(np.array_equal(frame, watermarked_frame))
        
        # Changes should be minimal (only LSB changes)
        diff = np.abs(frame.astype(int) - watermarked_frame.astype(int))
        self.assertTrue(np.all(diff <= 1))  # Maximum change of 1 per pixel
    
    def test_watermark_extraction(self):
        """Test watermark extraction from frames."""
        # Create a test frame
        frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        watermark_data = f"{self.test_user_id}:signature:0"
        
        # Embed and then extract
        watermarked_frame = self.watermarker._embed_lsb_watermark(frame, watermark_data)
        extracted = self.watermarker._extract_lsb_watermark(watermarked_frame)
        
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted['user_id'], self.test_user_id)
        self.assertIn('signature', extracted)
    
    def test_video_watermark_embed(self):
        """Test video watermarking process."""
        result = self.watermarker.embed(
            self.test_video_path,
            self.output_video_path,
            frame_interval=1  # Watermark every frame for testing
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['user_id'], self.test_user_id)
        self.assertGreater(result['total_frames'], 0)
        self.assertGreater(result['watermarked_frames'], 0)
        self.assertTrue(os.path.exists(self.output_video_path))
    
    def test_watermark_verification(self):
        """Test watermark verification."""
        # First embed a watermark
        embed_result = self.watermarker.embed(
            self.test_video_path,
            self.output_video_path,
            frame_interval=1
        )
        self.assertTrue(embed_result['success'])
        
        # Then verify it
        verification = self.watermarker.verify_integrity(self.output_video_path)
        
        self.assertTrue(verification['file_exists'])
        self.assertTrue(verification['watermark_found'])
        self.assertTrue(verification['user_verified'])
        self.assertEqual(verification['integrity_score'], 1.0)
    
    def test_invalid_video_handling(self):
        """Test handling of invalid video files."""
        invalid_path = "nonexistent_video.mp4"
        
        result = self.watermarker.embed(invalid_path, self.output_video_path)
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_motion_blur_watermark(self):
        """Test motion blur watermarking method."""
        motion_watermarker = Watermarker(
            user_id=self.test_user_id,
            method="motion_blur",
            strength=0.1
        )
        
        # Create a test frame
        frame = np.random.randint(0, 256, (200, 200, 3), dtype=np.uint8)
        
        # Apply motion blur watermark
        watermarked_frame = motion_watermarker._embed_motion_blur_watermark(frame)
        
        self.assertEqual(watermarked_frame.shape, frame.shape)
        self.assertEqual(watermarked_frame.dtype, frame.dtype)
        # Motion blur should create subtle differences
        self.assertFalse(np.array_equal(frame, watermarked_frame))



class TestWatermarkIntegration(unittest.TestCase):
    """Integration tests for watermarking workflow."""
    
    def test_complete_watermark_workflow(self):
        """Test complete watermark workflow from embed to verify."""
        user_id = "integration_test_user"
        
        # --- CHANGE #3: Use .avi for the file extensions ---
        test_video = tempfile.mktemp(suffix='.avi')
        output_video = tempfile.mktemp(suffix='.avi')
        
        try:
            # Create simple test video
            fourcc = cv2.VideoWriter_fourcc(*'FFV1')
            out = cv2.VideoWriter(test_video, fourcc, 30.0, (320, 240))
            
            for i in range(10):
                frame = np.random.randint(0, 256, (240, 320, 3), dtype=np.uint8)
                out.write(frame)
            
            out.release()
            time.sleep(1)
            
            # Step 1: Embed watermark
            watermarker = Watermarker(user_id, "lsb", 0.1)
            embed_result = watermarker.embed(test_video, output_video)
            
            self.assertTrue(embed_result['success'])
            
            # Step 2: Extract watermark
            extracted = watermarker.extract_watermark(output_video)
            self.assertIsNotNone(extracted)
            self.assertEqual(extracted['user_id'], user_id)
            
            # Step 3: Verify with correct user
            verification = watermarker.verify_integrity(output_video)
            self.assertTrue(verification['user_verified'])
            
            # Step 4: Verify with wrong user fails
            wrong_watermarker = Watermarker("wrong_user", "lsb", 0.1)
            wrong_verification = wrong_watermarker.verify_integrity(output_video)
            self.assertFalse(wrong_verification['user_verified'])
            
        finally:
            # Cleanup
            for path in [test_video, output_video]:
                if os.path.exists(path):
                    os.remove(path)


if __name__ == '__main__':
    unittest.main()