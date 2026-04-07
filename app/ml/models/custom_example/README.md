# Custom Violence Detection Model - Example

## Overview
This is an example showing how to create a custom model with custom preprocessing logic.

## Custom Preprocessing Features
1. **CLAHE (Contrast Limited Adaptive Histogram Equalization)**
   - Improves contrast in low-light conditions
   - Applied to L channel in LAB color space

2. **Gaussian Blur**
   - Reduces noise
   - Kernel size: 3x3

3. **ImageNet Normalization**
   - Mean: [0.485, 0.456, 0.406]
   - Std: [0.229, 0.224, 0.225]

4. **Temporal Smoothing**
   - Moving average across frames
   - Reduces prediction jitter

## How to Use Custom Preprocessing

### 1. Create `preprocessor.py`
```python
class CustomPreprocessor:
    def __init__(self, config: dict):
        # Initialize with config
        pass
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        # Process single frame
        pass
    
    def preprocess_sequence(self, frames: List[np.ndarray]) -> np.ndarray:
        # Process sequence
        pass
```

### 2. Update `config.json`
```json
{
  "custom_preprocessor": "preprocessor.py",
  ...
}
```

### 3. Use with Model Adapter
```python
from model_adapter import load_model

model = load_model("custom_example")
predicted_class, confidence = model.predict(frames)
```

## When to Use Custom Preprocessing

Use custom preprocessing when:
- Default preprocessing is insufficient
- You need domain-specific transformations
- Your model requires special input format
- You want to apply advanced techniques (CLAHE, denoising, etc.)

## Model Specifications
- **Input:** 20 frames of 128x128 RGB images
- **Output:** Binary classification (Safe / Violent)
- **Threshold:** 0.7
- **Framework:** TensorFlow/Keras

## Notes
- This is an example model (no actual model.keras file)
- Copy this structure to create your own custom models
- Custom preprocessor is optional - use only if needed
