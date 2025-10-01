"""
Leak Detection Scanner for EthicalDRM

Uses perceptual hashing (pHash) and scene-matching to detect leaked content
across public forums, Telegram groups, torrents, and other platforms.
"""

import asyncio
import aiohttp
import requests
import hashlib
import imagehash
import cv2
import numpy as np
import os
import logging
import time
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from PIL import Image
import re
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import schedule
from tqdm import tqdm

logger = logging.getLogger(__name__)


class LeakScanner:
    """
    AI-powered leak detection system using perceptual hashing and content matching.
    
    Features:
    - Perceptual hash comparison for video/image content
    - Multi-platform scanning (Telegram, Reddit, YouTube, etc.)
    - Automated scheduling and monitoring
    - Leak traceback to original watermarks
    """
    
    def __init__(self, 
                 original_content_path: str,
                 similarity_threshold: float = 0.85,
                 scan_interval_hours: int = 24):
        """
        Initialize leak scanner with original content.
        
        Args:
            original_content_path: Path to original protected content
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            scan_interval_hours: Hours between automated scans
        """
        self.original_content_path = original_content_path
        self.similarity_threshold = similarity_threshold
        self.scan_interval_hours = scan_interval_hours
        
        # Generate reference hashes from original content
        self.reference_hashes = self._generate_reference_hashes()
        self.scan_results = []
        self.scanning_active = False
        
        # Platform configurations
        self.platforms = {
            'telegram': {'enabled': True, 'channels': []},
            'reddit': {'enabled': True, 'subreddits': []},
            'youtube': {'enabled': True, 'keywords': []},
            'torrent': {'enabled': True, 'sites': []},
            'generic_web': {'enabled': True, 'domains': []}
        }
        
    def _generate_reference_hashes(self) -> List[str]:
        """
        Generate perceptual hashes from original content for comparison.
        
        Returns:
            List of reference hash strings
        """
        hashes = []
        
        try:
            if not os.path.exists(self.original_content_path):
                logger.error(f"Original content not found: {self.original_content_path}")
                return hashes
            
            file_ext = Path(self.original_content_path).suffix.lower()
            
            if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                hashes = self._extract_video_hashes()
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                hashes = self._extract_image_hashes()
            else:
                logger.warning(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Failed to generate reference hashes: {str(e)}")
            
        logger.info(f"Generated {len(hashes)} reference hashes")
        return hashes
    
    def _extract_video_hashes(self, sample_frames: int = 20) -> List[str]:
        """Extract perceptual hashes from video frames."""
        hashes = []
        
        try:
            cap = cv2.VideoCapture(self.original_content_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample frames evenly throughout the video
            frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    # Convert to PIL Image for hashing
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    # Generate multiple hash types for robust comparison
                    phash = str(imagehash.phash(pil_image))
                    dhash = str(imagehash.dhash(pil_image))
                    ahash = str(imagehash.average_hash(pil_image))
                    
                    hashes.extend([phash, dhash, ahash])
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Video hash extraction failed: {str(e)}")
            
        return hashes
    
    def _extract_image_hashes(self) -> List[str]:
        """Extract perceptual hashes from image file."""
        hashes = []
        
        try:
            pil_image = Image.open(self.original_content_path)
            
            # Generate multiple hash types
            phash = str(imagehash.phash(pil_image))
            dhash = str(imagehash.dhash(pil_image))
            ahash = str(imagehash.average_hash(pil_image))
            whash = str(imagehash.whash(pil_image))
            
            hashes = [phash, dhash, ahash, whash]
            
        except Exception as e:
            logger.error(f"Image hash extraction failed: {str(e)}")
            
        return hashes
    
    def calculate_similarity(self, content_url: str, content_data: bytes = None) -> float:
        """
        Calculate similarity between original content and potential leak.
        
        Args:
            content_url: URL of content to compare
            content_data: Raw content data if available
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            if content_data:
                # Process raw data
                temp_path = f"/tmp/leak_check_{int(time.time())}.tmp"
                with open(temp_path, 'wb') as f:
                    f.write(content_data)
                suspect_hashes = self._generate_hashes_from_file(temp_path)
                os.remove(temp_path)
            else:
                # Download and process URL
                suspect_hashes = self._download_and_hash(content_url)
            
            if not suspect_hashes:
                return 0.0
            
            # Compare hashes
            max_similarity = 0.0
            
            for ref_hash in self.reference_hashes:
                for suspect_hash in suspect_hashes:
                    similarity = self._hash_similarity(ref_hash, suspect_hash)
                    max_similarity = max(max_similarity, similarity)
            
            return max_similarity
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two hashes."""
        try:
            # Convert to imagehash objects for comparison
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            
            # Calculate Hamming distance
            distance = h1 - h2
            
            # Convert to similarity score (0-1)
            max_distance = len(hash1) * 4  # 4 bits per hex character
            similarity = 1.0 - (distance / max_distance)
            
            return max(0.0, similarity)
            
        except Exception as e:
            logger.debug(f"Hash comparison failed: {str(e)}")
            return 0.0
    
    def _download_and_hash(self, url: str) -> List[str]:
        """Download content from URL and generate hashes."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(url, timeout=30, stream=True, headers=headers)
            response.raise_for_status()
            
            # Save to temporary file
            temp_path = f"/tmp/download_{int(time.time())}.tmp"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            hashes = self._generate_hashes_from_file(temp_path)
            os.remove(temp_path)
            
            return hashes
            
        except Exception as e:
            logger.error(f"Download and hash failed: {str(e)}")
            return []
    
    def _generate_hashes_from_file(self, file_path: str) -> List[str]:
        """Generate hashes from any supported file type."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                return self._extract_video_hashes_from_file(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                return self._extract_image_hashes_from_file(file_path)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Hash generation failed: {str(e)}")
            return []
    
    def _extract_video_hashes_from_file(self, file_path: str) -> List[str]:
        """Extract hashes from video file."""
        hashes = []
        
        try:
            cap = cv2.VideoCapture(file_path)
            
            # Sample a few frames
            for i in range(5):
                frame_pos = i * 30  # Every 30 frames
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    phash = str(imagehash.phash(pil_image))
                    hashes.append(phash)
            
            cap.release()
            
        except Exception as e:
            logger.error(f"Video hash extraction failed: {str(e)}")
            
        return hashes
    
    def _extract_image_hashes_from_file(self, file_path: str) -> List[str]:
        """Extract hashes from image file."""
        try:
            pil_image = Image.open(file_path)
            
            phash = str(imagehash.phash(pil_image))
            dhash = str(imagehash.dhash(pil_image))
            
            return [phash, dhash]
            
        except Exception as e:
            logger.error(f"Image hash extraction failed: {str(e)}")
            return []
    
    async def scan_telegram_groups(self, channels: List[str]) -> List[Dict[str, Any]]:
        """
        Scan Telegram channels/groups for leaked content.
        
        Args:
            channels: List of Telegram channel usernames or URLs
            
        Returns:
            List of potential leak detections
        """
        detections = []
        
        try:
            from telethon import TelegramClient
            
            # Note: Requires API credentials - implement as needed
            logger.info(f"Scanning {len(channels)} Telegram channels")
            
            # Mock implementation - replace with actual Telethon integration
            for channel in channels:
                detection = {
                    'platform': 'telegram',
                    'source': channel,
                    'content_type': 'video',
                    'similarity_score': 0.0,
                    'url': f"https://t.me/{channel}",
                    'timestamp': time.time(),
                    'status': 'detected'
                }
                
                # Actual implementation would:
                # 1. Connect to Telegram API
                # 2. Download recent media from channel
                # 3. Calculate similarity scores
                # 4. Return matches above threshold
                
                detections.append(detection)
                
        except Exception as e:
            logger.error(f"Telegram scanning failed: {str(e)}")
            
        return detections
    
    async def scan_reddit_posts(self, subreddits: List[str], keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scan Reddit posts for leaked content.
        
        Args:
            subreddits: List of subreddit names
            keywords: Optional keywords to filter posts
            
        Returns:
            List of potential leak detections
        """
        detections = []
        
        try:
            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/new.json"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={'User-Agent': 'EthicalDRM LeakBot 1.0'}) as response:
                        if response.status == 200:
                            data = await response.json()
                            posts = data.get('data', {}).get('children', [])
                            
                            for post in posts:
                                post_data = post.get('data', {})
                                
                                # Check for media content
                                if post_data.get('url') and any(ext in post_data['url'] for ext in ['.mp4', '.gif', '.jpg', '.png']):
                                    similarity = self.calculate_similarity(post_data['url'])
                                    
                                    if similarity >= self.similarity_threshold:
                                        detections.append({
                                            'platform': 'reddit',
                                            'source': f"r/{subreddit}",
                                            'title': post_data.get('title', ''),
                                            'url': post_data.get('url'),
                                            'permalink': f"https://reddit.com{post_data.get('permalink', '')}",
                                            'similarity_score': similarity,
                                            'timestamp': post_data.get('created_utc', 0),
                                            'author': post_data.get('author', ''),
                                            'status': 'detected'
                                        })
                                        
        except Exception as e:
            logger.error(f"Reddit scanning failed: {str(e)}")
            
        return detections
    
    async def scan_youtube_videos(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Scan YouTube for videos matching keywords.
        
        Args:
            keywords: Search keywords
            
        Returns:
            List of potential leak detections
        """
        detections = []
        
        try:
            # Note: Requires YouTube API key for full functionality
            for keyword in keywords:
                search_url = f"https://www.youtube.com/results?search_query={keyword}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Parse video IDs from HTML (simplified)
                            video_ids = re.findall(r'"videoId":"([^"]+)"', html)
                            
                            for video_id in video_ids[:10]:  # Limit to first 10
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                
                                # Note: Actual implementation would need to:
                                # 1. Download video thumbnail or extract frames
                                # 2. Calculate similarity
                                # 3. Return matches
                                
                                detection = {
                                    'platform': 'youtube',
                                    'source': 'search',
                                    'keyword': keyword,
                                    'video_id': video_id,
                                    'url': video_url,
                                    'similarity_score': 0.0,  # Would be calculated
                                    'timestamp': time.time(),
                                    'status': 'detected'
                                }
                                
                                detections.append(detection)
                                
        except Exception as e:
            logger.error(f"YouTube scanning failed: {str(e)}")
            
        return detections
    
    def scan_torrent_sites(self, sites: List[str], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Scan torrent sites for leaked content.
        
        Args:
            sites: List of torrent site URLs
            keywords: Search keywords
            
        Returns:
            List of potential leak detections
        """
        detections = []
        
        try:
            for site in sites:
                for keyword in keywords:
                    # Note: Be careful with torrent site scraping due to legal issues
                    # This is a simplified implementation
                    
                    search_url = f"{site}/search/{keyword}"
                    
                    try:
                        response = requests.get(search_url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Extract torrent links (site-specific)
                            for link in soup.find_all('a', href=True):
                                if 'magnet:' in link['href'] or '.torrent' in link['href']:
                                    detection = {
                                        'platform': 'torrent',
                                        'source': site,
                                        'keyword': keyword,
                                        'title': link.get_text().strip(),
                                        'url': link['href'],
                                        'similarity_score': 0.5,  # Would need actual comparison
                                        'timestamp': time.time(),
                                        'status': 'potential'
                                    }
                                    
                                    detections.append(detection)
                                    
                    except Exception as e:
                        logger.error(f"Error scanning {site}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Torrent scanning failed: {str(e)}")
            
        return detections
    
    def generate_takedown_notice(self, detection: Dict[str, Any]) -> str:
        """
        Generate DMCA takedown notice for detected leak.
        
        Args:
            detection: Leak detection result
            
        Returns:
            Formatted takedown notice text
        """
        notice_template = """
DMCA TAKEDOWN NOTICE

Date: {date}
Platform: {platform}
Infringing Content URL: {url}

I am the copyright owner of the content being infringed. The unauthorized 
distribution of my copyrighted material at the above URL constitutes 
copyright infringement.

Original Content: {original_content}
Detected Similarity: {similarity_score:.2%}

I request immediate removal of this infringing content.

Contact Information:
- EthicalDRM Automated System
- Similarity Detection Score: {similarity_score:.2%}
- Detection Timestamp: {timestamp}

This notice was generated automatically by EthicalDRM leak detection system.
"""
        
        return notice_template.format(
            date=time.strftime('%Y-%m-%d'),
            platform=detection.get('platform', 'Unknown'),
            url=detection.get('url', 'N/A'),
            original_content=self.original_content_path,
            similarity_score=detection.get('similarity_score', 0.0),
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(detection.get('timestamp', 0)))
        )
    
    def start_scheduled_scanning(self):
        """Start automated scheduled scanning."""
        schedule.every(self.scan_interval_hours).hours.do(self.run_full_scan)
        self.scanning_active = True
        logger.info(f"Scheduled scanning started (every {self.scan_interval_hours} hours)")
    
    def stop_scheduled_scanning(self):
        """Stop automated scheduled scanning."""
        schedule.clear()
        self.scanning_active = False
        logger.info("Scheduled scanning stopped")
    
    async def run_full_scan(self) -> Dict[str, Any]:
        """
        Run comprehensive scan across all enabled platforms.
        
        Returns:
            Scan results summary
        """
        scan_start_time = time.time()
        all_detections = []
        
        logger.info("Starting full leak scan")
        
        try:
            # Telegram scanning
            if self.platforms['telegram']['enabled']:
                telegram_results = await self.scan_telegram_groups(
                    self.platforms['telegram']['channels']
                )
                all_detections.extend(telegram_results)
            
            # Reddit scanning
            if self.platforms['reddit']['enabled']:
                reddit_results = await self.scan_reddit_posts(
                    self.platforms['reddit']['subreddits']
                )
                all_detections.extend(reddit_results)
            
            # YouTube scanning
            if self.platforms['youtube']['enabled']:
                youtube_results = await self.scan_youtube_videos(
                    self.platforms['youtube']['keywords']
                )
                all_detections.extend(youtube_results)
            
            # Torrent scanning
            if self.platforms['torrent']['enabled']:
                torrent_results = self.scan_torrent_sites(
                    self.platforms['torrent']['sites'],
                    self.platforms['youtube']['keywords']  # Reuse keywords
                )
                all_detections.extend(torrent_results)
            
            # Filter by similarity threshold
            filtered_detections = [
                d for d in all_detections 
                if d.get('similarity_score', 0) >= self.similarity_threshold
            ]
            
            scan_duration = time.time() - scan_start_time
            
            results = {
                'scan_timestamp': scan_start_time,
                'scan_duration': scan_duration,
                'total_detections': len(all_detections),
                'high_confidence_detections': len(filtered_detections),
                'detections': filtered_detections,
                'platforms_scanned': [p for p, config in self.platforms.items() if config['enabled']],
                'similarity_threshold': self.similarity_threshold
            }
            
            self.scan_results.append(results)
            
            logger.info(f"Scan completed: {len(filtered_detections)} potential leaks found")
            
            return results
            
        except Exception as e:
            logger.error(f"Full scan failed: {str(e)}")
            return {
                'error': str(e),
                'scan_timestamp': scan_start_time,
                'scan_duration': time.time() - scan_start_time
            }
    
    def get_scan_history(self) -> List[Dict[str, Any]]:
        """Get history of all scan results."""
        return self.scan_results
    
    def configure_platform(self, platform: str, config: Dict[str, Any]):
        """
        Configure platform-specific scanning parameters.
        
        Args:
            platform: Platform name ('telegram', 'reddit', etc.)
            config: Configuration dictionary
        """
        if platform in self.platforms:
            self.platforms[platform].update(config)
            logger.info(f"Updated {platform} configuration")
        else:
            logger.warning(f"Unknown platform: {platform}")
    
    def export_results(self, output_path: str, format: str = 'json'):
        """
        Export scan results to file.
        
        Args:
            output_path: Path to output file
            format: Export format ('json', 'csv')
        """
        try:
            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(self.scan_results, f, indent=2)
            elif format == 'csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Platform', 'URL', 'Similarity', 'Status'])
                    
                    for scan in self.scan_results:
                        for detection in scan.get('detections', []):
                            writer.writerow([
                                scan['scan_timestamp'],
                                detection.get('platform', ''),
                                detection.get('url', ''),
                                detection.get('similarity_score', 0),
                                detection.get('status', '')
                            ])
            
            logger.info(f"Results exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")