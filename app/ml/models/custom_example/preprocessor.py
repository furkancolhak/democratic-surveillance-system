"""
Example Custom Preprocessor
Shows how to implement custom preprocessing logic
"""

import numpy as np
import cv2
from typing import List


class CustomPreprocessor:
    """
    Custom preprocessor example
    
    This shows how to implement custom preprocessing logic
    that goes beyond the default config-based preprocessing.
    """
    
    def __init__(self, config: dict):
        """
        Initialize custom preprocessor
        
        Args:
            config: Model configuration dictionary
        """
        self.config = config
        self.preprocessing_config = config['input']['preprocessing']
        self.resize = tuple(self.preprocessing_config['resize'])
        
        # Custom parameters (not in default preprocessor)
        self.apply_clahe = True  # Contrast Limited Adaptive Histogram Equalization
        self.apply_gaussian_blur = True
        self.blur_kernel = (3, 3)
        
        # ImageNet normalization
        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess single frame with custom logic
        
        Args:
            frame: Input frame (BGR format from OpenCV)
            
        Returns:
            Preprocessed frame
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize
        resized = cv2.resize(frame_rgb, self.resize)
        
        # Apply CLAHE for better contrast (optional)
        if self.apply_clahe:
            # Convert to LAB color space
            lab = cv2.cvtColor(resized, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge back
            lab = cv2.merge([l, a, b])
            resized = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        
        # Apply Gaussian blur for noise reduction (optional)
        if self.apply_gaussian_blur:
            resized = cv2.GaussianBlur(resized, self.blur_kernel, 0)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Apply ImageNet normalization
        normalized = (normalized - self.mean) / self.std
        
        return normalized
    
    def preprocess_sequence(self, frames: List[np.ndarray]) -> np.ndarray:
        """
        Preprocess sequence of frames
        
        Args:
            frames: List of input frames
            
        Returns:
            Preprocessed sequence as numpy array
        """
        processed_frames = []
        
        for frame in frames:
            processed = self.preprocess(frame)
            processed_frames.append(processed)
        
        # Stack frames
        sequence = np.array(processed_frames)
        
        # Optional: Apply temporal smoothing
        # This can help reduce jitter in predictions
        if len(processed_frames) > 1:
            # Simple moving average across temporal dimension
            kernel_size = 3
            if len(processed_frames) >= kernel_size:
                from scipy.ndimage import uniform_filter1d
                sequence = uniform_filter1d(sequence, size=kernel_size, axis=0)
        
        return sequence
