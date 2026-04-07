"""
Universal Model Adapter for Violence Detection
Supports multiple model formats with flexible preprocessing
"""

import os
import json
import importlib.util
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional, Any
from abc import ABC, abstractmethod


class PreprocessorBase(ABC):
    """Base class for custom preprocessors"""
    
    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess a single frame"""
        pass
    
    @abstractmethod
    def preprocess_sequence(self, frames: List[np.ndarray]) -> np.ndarray:
        """Preprocess a sequence of frames"""
        pass


class DefaultPreprocessor(PreprocessorBase):
    """Default preprocessor using config"""
    
    def __init__(self, config: Dict):
        self.config = config['input']['preprocessing']
        self.resize = tuple(self.config['resize'])
        self.normalization = self.config['normalization']
        self.color_space = self.config.get('color_space', 'RGB')
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess single frame"""
        # Resize
        processed = cv2.resize(frame, self.resize)
        
        # Color space conversion
        if self.color_space == 'RGB' and len(frame.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        elif self.color_space == 'GRAY':
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            processed = np.expand_dims(processed, axis=-1)
        
        # Normalization
        if self.normalization == '0-1':
            processed = processed.astype(np.float32) / 255.0
        elif self.normalization == '-1-1':
            processed = (processed.astype(np.float32) / 127.5) - 1.0
        elif self.normalization == 'imagenet':
            # ImageNet mean and std
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            processed = (processed.astype(np.float32) / 255.0 - mean) / std
        
        return processed
    
    def preprocess_sequence(self, frames: List[np.ndarray]) -> np.ndarray:
        """Preprocess sequence of frames"""
        processed_frames = [self.preprocess(frame) for frame in frames]
        return np.array(processed_frames)


class ModelLoader:
    """Load models in different formats"""
    
    @staticmethod
    def load_keras(path: str):
        """Load Keras/TensorFlow model"""
        import tensorflow as tf
        return tf.keras.models.load_model(path)
    
    @staticmethod
    def load_onnx(path: str):
        """Load ONNX model"""
        try:
            import onnxruntime as ort
            return ort.InferenceSession(path)
        except ImportError:
            raise ImportError("onnxruntime not installed. Install with: pip install onnxruntime")
    
    @staticmethod
    def load_pytorch(path: str):
        """Load PyTorch model"""
        try:
            import torch
            model = torch.load(path)
            model.eval()
            return model
        except ImportError:
            raise ImportError("torch not installed. Install with: pip install torch")
    
    @staticmethod
    def load_tensorflow_savedmodel(path: str):
        """Load TensorFlow SavedModel"""
        import tensorflow as tf
        return tf.saved_model.load(path)


class ModelAdapter:
    """Universal model adapter with flexible preprocessing"""
    
    def __init__(self, model_dir: str):
        """
        Initialize model adapter
        
        Args:
            model_dir: Directory containing model files and config.json
        """
        self.model_dir = model_dir
        self.config = self._load_config()
        self.model = self._load_model()
        self.preprocessor = self._load_preprocessor()
        
        # Extract config values
        self.sequence_length = self.config['input']['preprocessing'].get('sequence_length', 1)
        self.classes = self.config['output']['classes']
        self.threshold = self.config['output'].get('threshold', 0.5)
        self.model_format = self.config['format']
        
        print(f"✅ Model loaded: {self.config['name']}")
        print(f"   Format: {self.model_format}")
        print(f"   Classes: {self.classes}")
        print(f"   Sequence length: {self.sequence_length}")
    
    def _load_config(self) -> Dict:
        """Load model configuration"""
        config_path = os.path.join(self.model_dir, 'config.json')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['model_id', 'format', 'path', 'input', 'output']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in config: {field}")
        
        return config
    
    def _load_model(self):
        """Load model based on format"""
        model_path = os.path.join(self.model_dir, self.config['path'])
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        format_loaders = {
            'keras': ModelLoader.load_keras,
            'onnx': ModelLoader.load_onnx,
            'pytorch': ModelLoader.load_pytorch,
            'tensorflow_savedmodel': ModelLoader.load_tensorflow_savedmodel
        }
        
        model_format = self.config['format']
        
        if model_format not in format_loaders:
            raise ValueError(f"Unsupported model format: {model_format}")
        
        return format_loaders[model_format](model_path)
    
    def _load_preprocessor(self) -> PreprocessorBase:
        """Load preprocessor (custom or default)"""
        custom_preprocessor_path = self.config.get('custom_preprocessor')
        
        if custom_preprocessor_path:
            # Load custom preprocessor
            preprocessor_file = os.path.join(self.model_dir, custom_preprocessor_path)
            
            if not os.path.exists(preprocessor_file):
                print(f"⚠️  Custom preprocessor not found: {preprocessor_file}")
                print("   Using default preprocessor")
                return DefaultPreprocessor(self.config)
            
            # Dynamically import custom preprocessor
            spec = importlib.util.spec_from_file_location("custom_preprocessor", preprocessor_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Instantiate custom preprocessor
            return module.CustomPreprocessor(self.config)
        else:
            # Use default preprocessor
            return DefaultPreprocessor(self.config)
    
    def predict(self, frames: List[np.ndarray]) -> Tuple[str, float]:
        """
        Predict on a sequence of frames
        
        Args:
            frames: List of frames (numpy arrays)
            
        Returns:
            (predicted_class, confidence)
        """
        # Preprocess frames
        processed = self.preprocessor.preprocess_sequence(frames)
        
        # Add batch dimension
        processed = np.expand_dims(processed, axis=0)
        
        # Run inference based on model format
        if self.model_format == 'keras':
            predictions = self.model.predict(processed, verbose=0)[0]
        
        elif self.model_format == 'onnx':
            input_name = self.model.get_inputs()[0].name
            predictions = self.model.run(None, {input_name: processed.astype(np.float32)})[0][0]
        
        elif self.model_format == 'pytorch':
            import torch
            with torch.no_grad():
                tensor = torch.from_numpy(processed).float()
                predictions = self.model(tensor).numpy()[0]
        
        elif self.model_format == 'tensorflow_savedmodel':
            import tensorflow as tf
            predictions = self.model(tf.constant(processed, dtype=tf.float32)).numpy()[0]
        
        else:
            raise ValueError(f"Unsupported model format: {self.model_format}")
        
        # Get predicted class and confidence
        predicted_idx = np.argmax(predictions)
        confidence = float(predictions[predicted_idx])
        predicted_class = self.classes[predicted_idx]
        
        return predicted_class, confidence
    
    def is_positive_detection(self, predicted_class: str, confidence: float) -> bool:
        """Check if detection is positive (above threshold)"""
        # Assuming last class is the positive class (e.g., "Violence")
        positive_class = self.classes[-1]
        return predicted_class == positive_class and confidence >= self.threshold
    
    def get_info(self) -> Dict:
        """Get model information"""
        return {
            'model_id': self.config['model_id'],
            'name': self.config['name'],
            'version': self.config.get('version', 'unknown'),
            'format': self.model_format,
            'classes': self.classes,
            'sequence_length': self.sequence_length,
            'threshold': self.threshold,
            'metadata': self.config.get('metadata', {})
        }


class ModelRegistry:
    """Manage multiple models"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.registry_file = os.path.join(models_dir, "model_registry.json")
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load model registry"""
        if not os.path.exists(self.registry_file):
            # Create default registry
            default_registry = {
                "active_model": "violence_detection_v2",
                "models": {}
            }
            os.makedirs(self.models_dir, exist_ok=True)
            with open(self.registry_file, 'w') as f:
                json.dump(default_registry, f, indent=2)
            return default_registry
        
        with open(self.registry_file, 'r') as f:
            return json.load(f)
    
    def get_active_model(self) -> ModelAdapter:
        """Get the currently active model"""
        active_model_id = self.registry['active_model']
        model_dir = os.path.join(self.models_dir, active_model_id)
        
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Active model directory not found: {model_dir}")
        
        return ModelAdapter(model_dir)
    
    def set_active_model(self, model_id: str):
        """Set active model"""
        model_dir = os.path.join(self.models_dir, model_id)
        
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Model directory not found: {model_dir}")
        
        self.registry['active_model'] = model_id
        
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
        
        print(f"✅ Active model set to: {model_id}")
    
    def list_models(self) -> List[Dict]:
        """List all available models"""
        models = []
        
        if not os.path.exists(self.models_dir):
            return models
        
        for model_id in os.listdir(self.models_dir):
            model_dir = os.path.join(self.models_dir, model_id)
            
            if os.path.isdir(model_dir):
                config_path = os.path.join(model_dir, 'config.json')
                
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                        
                        models.append({
                            'model_id': model_id,
                            'name': config.get('name', model_id),
                            'version': config.get('version', 'unknown'),
                            'format': config.get('format', 'unknown'),
                            'active': model_id == self.registry['active_model']
                        })
                    except Exception as e:
                        print(f"⚠️  Error loading config for {model_id}: {e}")
        
        return models
    
    def register_model(self, model_id: str, model_dir: str):
        """Register a new model"""
        # Validate model directory
        config_path = os.path.join(model_dir, 'config.json')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found in: {model_dir}")
        
        # Copy or link model directory
        target_dir = os.path.join(self.models_dir, model_id)
        
        if os.path.exists(target_dir):
            raise ValueError(f"Model already registered: {model_id}")
        
        # Create symlink or copy
        import shutil
        shutil.copytree(model_dir, target_dir)
        
        print(f"✅ Model registered: {model_id}")


# Convenience function
def load_model(model_id: str = None) -> ModelAdapter:
    """
    Load a model by ID or get active model
    
    Args:
        model_id: Model ID to load (None = active model)
        
    Returns:
        ModelAdapter instance
    """
    registry = ModelRegistry()
    
    if model_id:
        model_dir = os.path.join(registry.models_dir, model_id)
        return ModelAdapter(model_dir)
    else:
        return registry.get_active_model()
