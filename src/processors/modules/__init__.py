"""
Modules package for brochure processor
"""

from .file_debugger import FileDebugger
from .ocr_extractor import OCRExtractorModule
from .metadata_generator import MetadataGenerator
from .promo_manager import PromoManager
from .video_creator import VideoCreator
from .utils import Utils

__all__ = [
    'FileDebugger',
    'OCRExtractorModule',
    'MetadataGenerator',
    'PromoManager',
    'VideoCreator',
    'Utils'
]
