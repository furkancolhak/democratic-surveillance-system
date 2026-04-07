#!/usr/bin/env python3
"""
Model Manager CLI
Manage violence detection models
"""

import sys
import os
from model_adapter import ModelRegistry, ModelAdapter
from tabulate import tabulate


def list_models():
    """List all available models"""
    registry = ModelRegistry()
    models = registry.list_models()
    
    if not models:
        print("No models found.")
        print("\nTo add a model:")
        print("  1. Create directory: models/<model_id>/")
        print("  2. Add config.json and model file")
        print("  3. Run: python model_manager.py register <model_id>")
        return
    
    # Prepare table data
    table_data = []
    for model in models:
        status = "✅ ACTIVE" if model['active'] else ""
        table_data.append([
            model['model_id'],
            model['name'],
            model['version'],
            model['format'],
            status
        ])
    
    print("\n📦 Available Models:\n")
    print(tabulate(table_data, headers=['Model ID', 'Name', 'Version', 'Format', 'Status'], tablefmt='grid'))
    print()


def show_model_info(model_id: str):
    """Show detailed model information"""
    try:
        registry = ModelRegistry()
        model_dir = os.path.join(registry.models_dir, model_id)
        
        if not os.path.exists(model_dir):
            print(f"❌ Model not found: {model_id}")
            return
        
        adapter = ModelAdapter(model_dir)
        info = adapter.get_info()
        
        print(f"\n📋 Model Information: {model_id}\n")
        print(f"Name:              {info['name']}")
        print(f"Version:           {info['version']}")
        print(f"Format:            {info['format']}")
        print(f"Classes:           {', '.join(info['classes'])}")
        print(f"Sequence Length:   {info['sequence_length']} frames")
        print(f"Threshold:         {info['threshold']}")
        
        if 'metadata' in info and info['metadata']:
            print(f"\nMetadata:")
            for key, value in info['metadata'].items():
                print(f"  {key:15} {value}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")


def set_active_model(model_id: str):
    """Set active model"""
    try:
        registry = ModelRegistry()
        registry.set_active_model(model_id)
        print(f"✅ Active model set to: {model_id}")
        print("\nRestart the detection system to use the new model.")
    except Exception as e:
        print(f"❌ Error: {e}")


def validate_model(model_id: str):
    """Validate model configuration"""
    try:
        registry = ModelRegistry()
        model_dir = os.path.join(registry.models_dir, model_id)
        
        if not os.path.exists(model_dir):
            print(f"❌ Model directory not found: {model_dir}")
            return False
        
        print(f"\n🔍 Validating model: {model_id}\n")
        
        # Check config.json
        config_path = os.path.join(model_dir, 'config.json')
        if not os.path.exists(config_path):
            print("❌ config.json not found")
            return False
        print("✅ config.json found")
        
        # Load adapter (validates config)
        try:
            adapter = ModelAdapter(model_dir)
            print("✅ Configuration valid")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return False
        
        # Check model file
        model_path = os.path.join(model_dir, adapter.config['path'])
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {adapter.config['path']}")
            return False
        print(f"✅ Model file found: {adapter.config['path']}")
        
        # Check custom preprocessor (if specified)
        if adapter.config.get('custom_preprocessor'):
            preprocessor_path = os.path.join(model_dir, adapter.config['custom_preprocessor'])
            if not os.path.exists(preprocessor_path):
                print(f"⚠️  Custom preprocessor not found: {adapter.config['custom_preprocessor']}")
                print("   Will use default preprocessor")
            else:
                print(f"✅ Custom preprocessor found: {adapter.config['custom_preprocessor']}")
        
        print("\n✅ Model validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


def test_model(model_id: str):
    """Test model with dummy data"""
    try:
        import numpy as np
        
        registry = ModelRegistry()
        model_dir = os.path.join(registry.models_dir, model_id)
        
        print(f"\n🧪 Testing model: {model_id}\n")
        
        # Load model
        adapter = ModelAdapter(model_dir)
        info = adapter.get_info()
        
        print(f"Model: {info['name']}")
        print(f"Sequence length: {info['sequence_length']}")
        
        # Create dummy frames
        print("\nGenerating dummy frames...")
        dummy_frames = []
        for i in range(info['sequence_length']):
            # Create random frame (simulating webcam input)
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            dummy_frames.append(frame)
        
        # Predict
        print("Running inference...")
        predicted_class, confidence = adapter.predict(dummy_frames)
        
        print(f"\n✅ Test successful!")
        print(f"   Predicted: {predicted_class}")
        print(f"   Confidence: {confidence:.4f}")
        print(f"   Threshold: {info['threshold']}")
        
        if adapter.is_positive_detection(predicted_class, confidence):
            print(f"   Result: ⚠️  Positive detection (above threshold)")
        else:
            print(f"   Result: ✅ Negative detection (below threshold)")
        
        print()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def print_usage():
    """Print usage information"""
    print("""
Model Manager - Manage violence detection models

Usage:
    python model_manager.py <command> [arguments]

Commands:
    list                    List all available models
    info <model_id>         Show detailed model information
    active <model_id>       Set active model
    validate <model_id>     Validate model configuration
    test <model_id>         Test model with dummy data
    help                    Show this help message

Examples:
    python model_manager.py list
    python model_manager.py info violence_detection_v2
    python model_manager.py active violence_detection_v2
    python model_manager.py validate custom_model
    python model_manager.py test violence_detection_v2

Model Structure:
    models/
    └── <model_id>/
        ├── config.json         (required)
        ├── model.keras         (required - or other format)
        ├── preprocessor.py     (optional - custom preprocessing)
        └── README.md           (optional - documentation)

For more information, see: models/custom_example/
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_models()
    
    elif command == 'info':
        if len(sys.argv) < 3:
            print("❌ Usage: python model_manager.py info <model_id>")
            return
        show_model_info(sys.argv[2])
    
    elif command == 'active':
        if len(sys.argv) < 3:
            print("❌ Usage: python model_manager.py active <model_id>")
            return
        set_active_model(sys.argv[2])
    
    elif command == 'validate':
        if len(sys.argv) < 3:
            print("❌ Usage: python model_manager.py validate <model_id>")
            return
        validate_model(sys.argv[2])
    
    elif command == 'test':
        if len(sys.argv) < 3:
            print("❌ Usage: python model_manager.py test <model_id>")
            return
        test_model(sys.argv[2])
    
    elif command == 'help':
        print_usage()
    
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    main()
