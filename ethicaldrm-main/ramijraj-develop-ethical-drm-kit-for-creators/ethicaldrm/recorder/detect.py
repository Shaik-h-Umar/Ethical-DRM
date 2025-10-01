"""
Screen Recording Detection Module for EthicalDRM

Detects common screen recording software and provides options to
alert users or temporarily disable playback for content protection.
"""

import psutil
import os
import platform
import subprocess
import logging
import time
from typing import List, Dict, Optional, Callable
import threading

logger = logging.getLogger(__name__)


class ScreenRecorderDetector:
    """
    Detects and manages screen recording software for content protection.
    
    Features:
    - Cross-platform detection (Windows, macOS, Linux)
    - Real-time monitoring
    - Configurable response actions
    - Support for custom recorder signatures
    """
    
    # Known screen recording software signatures
    KNOWN_RECORDERS = {
        'windows': [
            'obs64.exe', 'obs32.exe', 'obs.exe',
            'bandicam.exe', 'bdcam.exe',
            'camtasia.exe', 'camrec.exe',
            'snagit32.exe', 'snagiteditor.exe',
            'fraps.exe',
            'xsplit.core.exe', 'xsplit.broadcaster.exe',
            'action.exe',  # Action! screen recorder
            'screencastify.exe',
            'loom.exe',
            'nvidia-share.exe',  # NVIDIA GeForce Experience
            'amd-software.exe',  # AMD Software
            'game-bar-presence-writer.exe',  # Windows Game Bar
        ],
        'macos': [
            'obs', 'OBS',
            'QuickTime Player',
            'ScreenSearch',
            'Camtasia 2',
            'ScreenFlow',
            'Kap',
            'CleanMyMac X Menu',
            'CleanMaster- Remove Junk Files',
            'Loom',
            'Snagit 2021',
            'CleanMyMac X',
        ],
        'linux': [
            'obs', 'obs-studio',
            'recordmydesktop',
            'gtk-recordmydesktop',
            'qt-recordmydesktop',
            'ffmpeg',
            'avconv',
            'vlc',
            'simplescreenrecorder',
            'vokoscreen',
            'kazam',
            'byzanz-record',
            'xvidcap',
        ]
    }
    
    def __init__(self, 
                 check_interval: float = 2.0,
                 on_detection: Optional[Callable] = None,
                 strict_mode: bool = False):
        """
        Initialize screen recorder detector.
        
        Args:
            check_interval: Seconds between detection checks
            on_detection: Callback function when recorder detected
            strict_mode: If True, includes broader process detection
        """
        self.check_interval = check_interval
        self.on_detection = on_detection
        self.strict_mode = strict_mode
        self.monitoring = False
        self.monitor_thread = None
        self.detected_recorders = []
        
        # Platform-specific setup
        self.platform = platform.system().lower()
        if self.platform == 'darwin':
            self.platform = 'macos'
        elif self.platform not in ['windows', 'linux', 'macos']:
            self.platform = 'linux'  # Default fallback
            
        self.known_processes = self.KNOWN_RECORDERS.get(self.platform, [])
        
    def detect_recording_software(self) -> List[Dict[str, any]]:
        """
        Scan for active screen recording software.
        
        Returns:
            List of detected recording processes with details
        """
        detected = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower() if proc_info['name'] else ''
                    
                    # Check against known recorder processes
                    for known_recorder in self.known_processes:
                        if known_recorder.lower() in proc_name:
                            detected.append({
                                'name': proc_info['name'],
                                'pid': proc_info['pid'],
                                'exe': proc_info['exe'],
                                'cmdline': proc_info['cmdline'],
                                'recorder_type': known_recorder,
                                'severity': 'high'
                            })
                            
                    # Strict mode: additional heuristic checks
                    if self.strict_mode:
                        detected.extend(self._heuristic_detection(proc_info))
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.error(f"Error during recorder detection: {str(e)}")
            
        # Remove duplicates based on PID
        unique_detected = []
        seen_pids = set()
        for detection in detected:
            if detection['pid'] not in seen_pids:
                unique_detected.append(detection)
                seen_pids.add(detection['pid'])
                
        return unique_detected
    
    def _heuristic_detection(self, proc_info: Dict) -> List[Dict[str, any]]:
        """
        Additional heuristic-based detection for suspicious processes.
        
        Args:
            proc_info: Process information dictionary
            
        Returns:
            List of potential recording processes
        """
        detected = []
        proc_name = proc_info['name'].lower() if proc_info['name'] else ''
        cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
        
        # Heuristic patterns
        suspicious_patterns = [
            'record', 'capture', 'screen', 'desktop',
            'stream', 'broadcast', 'video',
            'ffmpeg', 'gstreamer', 'x264'
        ]
        
        recording_args = [
            '-f gdigrab',  # FFmpeg Windows screen capture
            '-f x11grab',  # FFmpeg X11 screen capture
            '-f avfoundation',  # FFmpeg macOS screen capture
            'screen-capture',
            'desktop-recording',
            '--record',
            '--capture'
        ]
        
        # Check process name patterns
        for pattern in suspicious_patterns:
            if pattern in proc_name and len(proc_name) > 3:  # Avoid false positives
                detected.append({
                    'name': proc_info['name'],
                    'pid': proc_info['pid'],
                    'exe': proc_info['exe'],
                    'cmdline': proc_info['cmdline'],
                    'recorder_type': f'heuristic:{pattern}',
                    'severity': 'medium'
                })
                break
        
        # Check command line arguments
        for arg_pattern in recording_args:
            if arg_pattern in cmdline:
                detected.append({
                    'name': proc_info['name'],
                    'pid': proc_info['pid'],
                    'exe': proc_info['exe'],
                    'cmdline': proc_info['cmdline'],
                    'recorder_type': f'cmdline:{arg_pattern}',
                    'severity': 'high'
                })
                break
                
        return detected
    
    def start_monitoring(self) -> bool:
        """
        Start continuous monitoring for screen recorders.
        
        Returns:
            True if monitoring started successfully
        """
        if self.monitoring:
            logger.warning("Monitoring already active")
            return False
            
        try:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Screen recorder monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")
            self.monitoring = False
            return False
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("Screen recorder monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop running in separate thread."""
        while self.monitoring:
            try:
                detected = self.detect_recording_software()
                
                if detected:
                    self.detected_recorders = detected
                    logger.warning(f"Screen recorders detected: {len(detected)} processes")
                    
                    # Trigger callback if provided
                    if self.on_detection:
                        try:
                            self.on_detection(detected)
                        except Exception as e:
                            logger.error(f"Detection callback failed: {str(e)}")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {str(e)}")
                time.sleep(self.check_interval)
    
    def get_detection_status(self) -> Dict[str, any]:
        """
        Get current detection status and statistics.
        
        Returns:
            Status dictionary with detection information
        """
        return {
            'monitoring_active': self.monitoring,
            'platform': self.platform,
            'known_recorders_count': len(self.known_processes),
            'currently_detected': len(self.detected_recorders),
            'detected_processes': self.detected_recorders,
            'strict_mode': self.strict_mode,
            'check_interval': self.check_interval
        }
    
    def add_custom_recorder(self, process_name: str):
        """
        Add custom recorder process name to detection list.
        
        Args:
            process_name: Name of the recorder process to detect
        """
        if process_name not in self.known_processes:
            self.known_processes.append(process_name)
            logger.info(f"Added custom recorder: {process_name}")
    
    def whitelist_process(self, process_name: str):
        """
        Remove process from detection (whitelist it).
        
        Args:
            process_name: Name of process to whitelist
        """
        if process_name in self.known_processes:
            self.known_processes.remove(process_name)
            logger.info(f"Whitelisted process: {process_name}")
    
    def terminate_detected_recorders(self, confirm: bool = False) -> List[Dict[str, any]]:
        """
        Attempt to terminate detected recording processes.
        WARNING: This is aggressive and should be used carefully.
        
        Args:
            confirm: Must be True to actually terminate processes
            
        Returns:
            List of termination results
        """
        if not confirm:
            logger.warning("Process termination requires explicit confirmation")
            return []
            
        results = []
        detected = self.detect_recording_software()
        
        for recorder in detected:
            try:
                proc = psutil.Process(recorder['pid'])
                proc.terminate()
                
                # Wait for termination
                proc.wait(timeout=5)
                
                results.append({
                    'pid': recorder['pid'],
                    'name': recorder['name'],
                    'status': 'terminated',
                    'success': True
                })
                
                logger.info(f"Terminated recorder: {recorder['name']} (PID: {recorder['pid']})")
                
            except psutil.TimeoutExpired:
                # Force kill if terminate didn't work
                try:
                    proc.kill()
                    results.append({
                        'pid': recorder['pid'],
                        'name': recorder['name'],
                        'status': 'force_killed',
                        'success': True
                    })
                except Exception as e:
                    results.append({
                        'pid': recorder['pid'],
                        'name': recorder['name'],
                        'status': 'failed',
                        'success': False,
                        'error': str(e)
                    })
                    
            except Exception as e:
                results.append({
                    'pid': recorder['pid'],
                    'name': recorder['name'],
                    'status': 'failed',
                    'success': False,
                    'error': str(e)
                })
                
        return results
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """
        Get system information relevant to recording detection.
        
        Returns:
            System information dictionary
        """
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'total_memory': f"{psutil.virtual_memory().total // (1024**3)} GB",
            'cpu_count': psutil.cpu_count()
        }