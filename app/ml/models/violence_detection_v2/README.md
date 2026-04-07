# Violence Detection Model v2

## Overview
MobileNet + BiLSTM architecture for real-time violence detection from video sequences.

## Model Details
- **Architecture:** MobileNet (feature extraction) + Bidirectional LSTM (temporal analysis)
- **Input:** 16 frames of 64x64 RGB images
- **Output:** Binary classification (NonViolence / Violence)
- **Framework:** TensorFlow/Keras
- **Accuracy:** 95%

## Preprocessing
1. Resize frames to 64x64
2. Convert BGR to RGB
3. Normalize to [0, 1] range
4. Stack 16 consecutive frames

## Usage

### With Model Adapter
```python
from model_adapter import load_model

# Load model
model = load_model("violence_detection_v2")

# Predict
frames = [...]  # List of 16 frames
predicted_class, confidence = model.predict(frames)

print(f"Prediction: {predicted_class} ({confidence:.2f})")
```

### Direct Usage
```python
import tensorflow as tf

model = tf.keras.models.load_model("model.keras")
predictions = model.predict(preprocessed_frames)
```

## Training Details
- **Dataset:** Custom violence detection dataset
- **Training Date:** 2024-01-15
- **Epochs:** 50
- **Batch Size:** 32
- **Optimizer:** Adam
- **Loss:** Categorical Crossentropy

## Performance
- **Accuracy:** 95%
- **Precision:** 0.94
- **Recall:** 0.96
- **F1-Score:** 0.95
- **Inference Time:** ~50ms per sequence (CPU)

## Requirements
- TensorFlow >= 2.13.0
- NumPy >= 1.24.0
- OpenCV >= 4.8.0

## Notes
- Model expects RGB input (not BGR)
- Sequence length must be exactly 16 frames
- Confidence threshold set to 0.5 (adjustable in config)
