"""
EthicalDRM - Ethical Digital Rights Management Kit for Indie Creators

Version: 1.0
Author: Ramij Raj
License: MIT
Status: Beta
Project Codename: EthicalDRM
"""

__version__ = "1.0.0"
__author__ = "Ramij Raj"
__license__ = "MIT"

from .video.watermark import Watermarker
from .leakbot.scanner import LeakScanner
from .recorder.detect import ScreenRecorderDetector
from .api.app import create_app

__all__ = ['Watermarker', 'LeakScanner', 'ScreenRecorderDetector', 'create_app']