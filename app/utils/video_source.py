"""
Modular Video Source System
Supports webcam, RTSP/IP cameras, and video files
"""

import cv2
from abc import ABC, abstractmethod
from typing import Tuple, Optional
import os


class VideoSource(ABC):
    """Abstract base class for video sources"""
    
    def __init__(self):
        self.capture = None
        self.is_opened = False
        
    @abstractmethod
    def open(self) -> bool:
        """Open video source"""
        pass
    
    @abstractmethod
    def read(self) -> Tuple[bool, Optional[any]]:
        """Read frame from source"""
        pass
    
    def release(self):
        """Release video source"""
        if self.capture is not None:
            self.capture.release()
            self.is_opened = False
    
    def get_fps(self) -> float:
        """Get FPS of video source"""
        if self.capture is not None:
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            return fps if fps > 0 else 30.0
        return 30.0
    
    def get_frame_size(self) -> Tuple[int, int]:
        """Get frame width and height"""
        if self.capture is not None:
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height
        return 640, 480
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class WebcamSource(VideoSource):
    """Webcam video source for local testing"""
    
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        
    def open(self) -> bool:
        """Open webcam"""
        self.capture = cv2.VideoCapture(self.camera_index)
        self.is_opened = self.capture.isOpened()
        return self.is_opened
    
    def read(self) -> Tuple[bool, Optional[any]]:
        """Read frame from webcam"""
        if self.capture is not None:
            return self.capture.read()
        return False, None
    
    def __str__(self):
        return f"Webcam (index: {self.camera_index})"


class RTSPSource(VideoSource):
    """RTSP/IP Camera source for CCTV integration"""
    
    def __init__(self, rtsp_url: str, username: str = None, password: str = None):
        super().__init__()
        
        # Build RTSP URL with credentials if provided
        if username and password:
            # Format: rtsp://username:password@ip:port/path
            if "://" in rtsp_url:
                protocol, rest = rtsp_url.split("://", 1)
                self.rtsp_url = f"{protocol}://{username}:{password}@{rest}"
            else:
                self.rtsp_url = f"rtsp://{username}:{password}@{rtsp_url}"
        else:
            self.rtsp_url = rtsp_url
            
    def open(self) -> bool:
        """Open RTSP stream"""
        self.capture = cv2.VideoCapture(self.rtsp_url)
        
        # RTSP streams may need buffer settings
        if self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            
        self.is_opened = self.capture.isOpened()
        return self.is_opened
    
    def read(self) -> Tuple[bool, Optional[any]]:
        """Read frame from RTSP stream"""
        if self.capture is not None:
            return self.capture.read()
        return False, None
    
    def __str__(self):
        # Hide credentials in string representation
        url = self.rtsp_url
        if "@" in url:
            protocol, rest = url.split("://", 1)
            rest = rest.split("@", 1)[1]
            url = f"{protocol}://***:***@{rest}"
        return f"RTSP Stream ({url})"


class FileSource(VideoSource):
    """Video file source for testing with recorded videos"""
    
    def __init__(self, file_path: str, loop: bool = False):
        super().__init__()
        self.file_path = file_path
        self.loop = loop
        
    def open(self) -> bool:
        """Open video file"""
        if not os.path.exists(self.file_path):
            print(f"❌ Video file not found: {self.file_path}")
            return False
            
        self.capture = cv2.VideoCapture(self.file_path)
        self.is_opened = self.capture.isOpened()
        return self.is_opened
    
    def read(self) -> Tuple[bool, Optional[any]]:
        """Read frame from video file"""
        if self.capture is not None:
            ok, frame = self.capture.read()
            
            # Loop video if enabled and reached end
            if not ok and self.loop:
                self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self.capture.read()
                
            return ok, frame
        return False, None
    
    def __str__(self):
        return f"Video File ({os.path.basename(self.file_path)})"


def create_video_source(source_type: str, **kwargs) -> VideoSource:
    """
    Factory function to create video source
    
    Args:
        source_type: Type of source ('webcam', 'rtsp', 'file')
        **kwargs: Source-specific parameters
        
    Returns:
        VideoSource instance
        
    Examples:
        # Webcam
        source = create_video_source('webcam', camera_index=0)
        
        # RTSP
        source = create_video_source('rtsp', 
                                     rtsp_url='rtsp://192.168.1.100:554/stream',
                                     username='admin',
                                     password='password')
        
        # File
        source = create_video_source('file', 
                                     file_path='test_video.mp4',
                                     loop=True)
    """
    source_type = source_type.lower()
    
    if source_type == 'webcam':
        return WebcamSource(camera_index=kwargs.get('camera_index', 0))
    
    elif source_type == 'rtsp':
        return RTSPSource(
            rtsp_url=kwargs['rtsp_url'],
            username=kwargs.get('username'),
            password=kwargs.get('password')
        )
    
    elif source_type == 'file':
        return FileSource(
            file_path=kwargs['file_path'],
            loop=kwargs.get('loop', False)
        )
    
    else:
        raise ValueError(f"Unknown source type: {source_type}. "
                        f"Use 'webcam', 'rtsp', or 'file'")
