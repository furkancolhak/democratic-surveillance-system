# 🤖 Model Deployment Guide

## Overview

The system supports **multiple model formats** with **flexible preprocessing**. Deploy any violence detection model without changing code!

---

## 🎯 Supported Features

### Model Formats
- ✅ **Keras/TensorFlow** (.keras, .h5)
- ✅ **ONNX** (.onnx)
- ✅ **PyTorch** (.pt, .pth)
- ✅ **TensorFlow SavedModel** (directory)

### Preprocessing
- ✅ **Config-based** - Simple YAML/JSON configuration
- ✅ **Custom Python** - Full control with custom preprocessor
- ✅ **Auto-detection** - Automatic format detection

---

## 📁 Model Structure

```
models/
├── model_registry.json          # Active model selection
│
├── violence_detection_v2/       # Example: Default model
│   ├── config.json              # Model configuration
│   ├── model.keras              # Model file
│   └── README.md                # Documentation
│
└── custom_example/              # Example: Custom preprocessing
    ├── config.json
    ├── model.keras
    ├── preprocessor.py          # Custom preprocessing logic
    └── README.md
```

---

## 🚀 Quick Start

### 1. Deploy New Model

```bash
# Create model directory
mkdir -p models/my_model

# Add your model file
cp /path/to/model.keras models/my_model/

# Create config.json (see template below)
nano models/my_model/config.json

# Validate model
python model_manager.py validate my_model

# Set as active
python model_manager.py active my_model

# Restart detection
docker-compose restart app
```

### 2. Use Model

```bash
# Use active model
python secure_webcam_detector.py

# Or specify model
python secure_webcam_detector.py my_model
```

---

## 📝 Configuration Template

### Basic Config (config.json)

```json
{
  "model_id": "my_model",
  "name": "My Violence Detection Model",
  "version": "1.0.0",
  "format": "keras",
  "path": "model.keras",
  
  "input": {
    "type": "video_sequence",
    "shape": [16, 64, 64, 3],
    "preprocessing": {
      "resize": [64, 64],
      "normalization": "0-1",
      "color_space": "RGB",
      "sequence_length": 16
    }
  },
  
  "output": {
    "type": "classification",
    "classes": ["NonViolence", "Violence"],
    "threshold": 0.5
  },
  
  "custom_preprocessor": null,
  
  "metadata": {
    "author": "Your Name",
    "description": "Model description",
    "training_date": "2025-01-01",
    "accuracy": 0.95
  }
}
```

### Config Fields Explained

| Field | Required | Description |
|-------|----------|-------------|
| `model_id` | ✅ | Unique identifier |
| `name` | ✅ | Human-readable name |
| `version` | ✅ | Model version |
| `format` | ✅ | `keras`, `onnx`, `pytorch`, `tensorflow_savedmodel` |
| `path` | ✅ | Relative path to model file |
| `input.shape` | ✅ | Input tensor shape `[seq_len, height, width, channels]` |
| `input.preprocessing.resize` | ✅ | Target size `[height, width]` |
| `input.preprocessing.normalization` | ✅ | `0-1`, `-1-1`, or `imagenet` |
| `input.preprocessing.color_space` | ✅ | `RGB`, `BGR`, or `GRAY` |
| `input.preprocessing.sequence_length` | ✅ | Number of frames |
| `output.classes` | ✅ | List of class names |
| `output.threshold` | ✅ | Confidence threshold (0.0-1.0) |
| `custom_preprocessor` | ❌ | Path to custom preprocessor (optional) |
| `metadata` | ❌ | Additional information (optional) |

---

## 🎨 Preprocessing Options

### Option 1: Config-Based (Simple)

Use built-in preprocessing via config:

```json
"preprocessing": {
  "resize": [64, 64],
  "normalization": "0-1",
  "color_space": "RGB",
  "sequence_length": 16
}
```

**Normalization types:**
- `0-1`: Divide by 255
- `-1-1`: Scale to [-1, 1]
- `imagenet`: ImageNet mean/std normalization

**Color spaces:**
- `RGB`: Convert BGR → RGB
- `BGR`: Keep as BGR
- `GRAY`: Convert to grayscale

---

### Option 2: Custom Preprocessor (Advanced)

For complex preprocessing, create `preprocessor.py`:

```python
import numpy as np
import cv2
from typing import List

class CustomPreprocessor:
    def __init__(self, config: dict):
        self.config = config
        # Your initialization
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Process single frame"""
        # Your preprocessing logic
        return processed_frame
    
    def preprocess_sequence(self, frames: List[np.ndarray]) -> np.ndarray:
        """Process sequence of frames"""
        processed = [self.preprocess(f) for f in frames]
        return np.array(processed)
```

Then update config:
```json
"custom_preprocessor": "preprocessor.py"
```

**Example use cases:**
- CLAHE for contrast enhancement
- Gaussian blur for noise reduction
- Custom normalization
- Temporal smoothing
- Data augmentation

See `models/custom_example/preprocessor.py` for full example.

---

## 🔧 Model Management CLI

### List Models
```bash
python model_manager.py list
```

Output:
```
📦 Available Models:

+------------------------+---------------------------+---------+--------+----------+
| Model ID               | Name                      | Version | Format | Status   |
+========================+===========================+=========+========+==========+
| violence_detection_v2  | Violence Detection v2     | 2.0.0   | keras  | ✅ ACTIVE|
| custom_example         | Custom Model              | 1.0.0   | keras  |          |
+------------------------+---------------------------+---------+--------+----------+
```

### Show Model Info
```bash
python model_manager.py info violence_detection_v2
```

### Set Active Model
```bash
python model_manager.py active my_model
```

### Validate Model
```bash
python model_manager.py validate my_model
```

Checks:
- ✅ config.json exists and valid
- ✅ Model file exists
- ✅ Custom preprocessor exists (if specified)
- ✅ Configuration is loadable

### Test Model
```bash
python model_manager.py test my_model
```

Runs inference with dummy data to verify model works.

---

## 📊 Model Format Examples

### Keras Model
```json
{
  "format": "keras",
  "path": "model.keras"
}
```

### ONNX Model
```json
{
  "format": "onnx",
  "path": "model.onnx"
}
```

### PyTorch Model
```json
{
  "format": "pytorch",
  "path": "model.pt"
}
```

### TensorFlow SavedModel
```json
{
  "format": "tensorflow_savedmodel",
  "path": "saved_model/"
}
```

---

## 🎯 Real-World Examples

### Example 1: Simple Keras Model

```bash
# 1. Create directory
mkdir -p models/simple_violence_model

# 2. Copy model
cp my_model.keras models/simple_violence_model/model.keras

# 3. Create config
cat > models/simple_violence_model/config.json << 'EOF'
{
  "model_id": "simple_violence_model",
  "name": "Simple Violence Detector",
  "version": "1.0.0",
  "format": "keras",
  "path": "model.keras",
  "input": {
    "type": "video_sequence",
    "shape": [16, 64, 64, 3],
    "preprocessing": {
      "resize": [64, 64],
      "normalization": "0-1",
      "color_space": "RGB",
      "sequence_length": 16
    }
  },
  "output": {
    "type": "classification",
    "classes": ["Safe", "Violence"],
    "threshold": 0.6
  },
  "custom_preprocessor": null
}
EOF

# 4. Validate
python model_manager.py validate simple_violence_model

# 5. Activate
python model_manager.py active simple_violence_model
```

---

### Example 2: ONNX Model with Custom Preprocessing

```bash
# 1. Create directory
mkdir -p models/onnx_violence_model

# 2. Copy model
cp my_model.onnx models/onnx_violence_model/model.onnx

# 3. Create custom preprocessor
cat > models/onnx_violence_model/preprocessor.py << 'EOF'
import numpy as np
import cv2

class CustomPreprocessor:
    def __init__(self, config):
        self.config = config
        self.size = tuple(config['input']['preprocessing']['resize'])
    
    def preprocess(self, frame):
        # Resize
        resized = cv2.resize(frame, self.size)
        # Convert to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # Normalize
        normalized = rgb.astype(np.float32) / 255.0
        return normalized
    
    def preprocess_sequence(self, frames):
        return np.array([self.preprocess(f) for f in frames])
EOF

# 4. Create config
cat > models/onnx_violence_model/config.json << 'EOF'
{
  "model_id": "onnx_violence_model",
  "name": "ONNX Violence Detector",
  "version": "1.0.0",
  "format": "onnx",
  "path": "model.onnx",
  "input": {
    "type": "video_sequence",
    "shape": [20, 128, 128, 3],
    "preprocessing": {
      "resize": [128, 128],
      "normalization": "0-1",
      "color_space": "RGB",
      "sequence_length": 20
    }
  },
  "output": {
    "type": "classification",
    "classes": ["Normal", "Violent"],
    "threshold": 0.7
  },
  "custom_preprocessor": "preprocessor.py"
}
EOF

# 5. Validate and activate
python model_manager.py validate onnx_violence_model
python model_manager.py active onnx_violence_model
```

---

## 🔄 Switching Models

### During Development
```bash
# Switch to model A
python model_manager.py active model_a
python secure_webcam_detector.py

# Switch to model B
python model_manager.py active model_b
python secure_webcam_detector.py
```

### In Production (Docker)
```bash
# Update active model
docker-compose exec app python model_manager.py active new_model

# Restart detection
docker-compose restart app
```

---

## 🐛 Troubleshooting

### Model Not Loading
```bash
# Check model exists
ls -la models/my_model/

# Validate configuration
python model_manager.py validate my_model

# Check logs
docker-compose logs app
```

### Preprocessing Errors
```bash
# Test with dummy data
python model_manager.py test my_model

# Check custom preprocessor
python -c "from models.my_model.preprocessor import CustomPreprocessor; print('OK')"
```

### Wrong Predictions
- Check `threshold` in config
- Verify `normalization` matches training
- Ensure `color_space` is correct (RGB vs BGR)
- Test with known samples

---

## 📚 Best Practices

### 1. Model Organization
```
models/
└── my_model_v1/
    ├── config.json          # Configuration
    ├── model.keras          # Model file
    ├── preprocessor.py      # Custom preprocessing (optional)
    ├── README.md            # Documentation
    └── test_samples/        # Test images/videos
```

### 2. Version Control
- Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
- Keep old versions for rollback
- Document changes in README.md

### 3. Testing
```bash
# Always validate before deploying
python model_manager.py validate my_model

# Test with dummy data
python model_manager.py test my_model

# Test with real data
python secure_webcam_detector.py my_model
```

### 4. Documentation
Include in README.md:
- Model architecture
- Training details
- Preprocessing requirements
- Performance metrics
- Known limitations

---

## 🎓 Advanced Topics

### Multi-Model Ensemble
Deploy multiple models and combine predictions:

```python
from model_adapter import load_model

model1 = load_model("model_a")
model2 = load_model("model_b")

pred1, conf1 = model1.predict(frames)
pred2, conf2 = model2.predict(frames)

# Ensemble logic
final_pred = "Violence" if (conf1 + conf2) / 2 > 0.6 else "NonViolence"
```

### A/B Testing
Run two models simultaneously:

```bash
# Terminal 1
python secure_webcam_detector.py model_a

# Terminal 2
python secure_webcam_detector.py model_b
```

### Model Monitoring
Track model performance:
- Log predictions to database
- Monitor confidence scores
- Track false positives/negatives
- Set up alerts for low confidence

---

## 📞 Support

### Documentation
- `models/violence_detection_v2/README.md` - Default model
- `models/custom_example/README.md` - Custom preprocessing example

### Commands
```bash
# List all models
python model_manager.py list

# Get help
python model_manager.py help

# Validate model
python model_manager.py validate <model_id>
```

---

## ✅ Checklist for New Model

- [ ] Create model directory: `models/<model_id>/`
- [ ] Add model file (`.keras`, `.onnx`, etc.)
- [ ] Create `config.json` with all required fields
- [ ] Add `README.md` with documentation
- [ ] Create custom `preprocessor.py` (if needed)
- [ ] Validate: `python model_manager.py validate <model_id>`
- [ ] Test: `python model_manager.py test <model_id>`
- [ ] Activate: `python model_manager.py active <model_id>`
- [ ] Test with webcam: `python secure_webcam_detector.py`
- [ ] Document performance and limitations

---

**System Version:** 2.0
**Last Updated:** 2025-04-08
**Status:** ✅ Production Ready
