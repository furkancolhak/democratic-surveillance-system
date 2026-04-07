"""
Secure Violence Detector with Modular Video Sources
Supports webcam, RTSP/IP cameras, and video files
Supports multiple models via Model Adapter
"""

import cv2
import numpy as np
from collections import deque
import os
from datetime import datetime
from dotenv import load_dotenv
from video_crypto import VideoCrypto
from secure_voting_system import SecureVotingSystem
from notification_service import NotificationService
from secure_member_auth import SecureMemberAuth
from database import db_manager
from model_adapter import load_model
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.video_source import create_video_source, VideoSource

# Load environment variables
load_dotenv()

# Disable TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Constants
RECORDING_DURATION = 10  # seconds
RECORDINGS_DIR = "violence_recordings"


def create_video_writer(frame, fps):
    """Create video writer for recording"""
    if not os.path.exists(RECORDINGS_DIR):
        os.makedirs(RECORDINGS_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = os.path.join(RECORDINGS_DIR, f"violence_detected_{timestamp}.mp4")
    
    height, width = frame.shape[:2]
    writer = cv2.VideoWriter(
        video_path,
        cv2.VideoWriter_fourcc(*'mp4v'),
        fps,
        (width, height)
    )
    return writer, video_path, timestamp


def process_recorded_video(video_path: str, timestamp: str):
    """Process recorded video: encrypt and start voting"""
    try:
        print(f"\n📹 Processing recorded video: {video_path}")
        
        # Initialize services
        voting_system = SecureVotingSystem()
        notification_service = NotificationService()
        member_auth = SecureMemberAuth()
        
        # Create voting session
        session_uuid = voting_system.create_voting_session(video_path, timestamp)
        print(f"✅ Voting session created: {session_uuid}")
        
        # Get active members
        active_members = member_auth.get_active_members()
        
        if not active_members:
            print("⚠️  No active members found. Cannot send notifications.")
            return
        
        # Get session details
        session_data = voting_system.get_session_by_id(session_uuid)
        
        # Send notifications to all members
        print(f"📧 Sending notifications to {len(active_members)} members...")
        
        # Convert members list to dict format for notification service
        members_dict = {member['email']: member for member in active_members}
        
        notification_service.send_incident_notification(
            session_id=str(session_uuid),
            members=members_dict,
            incident_time=timestamp,
            encrypted_shares={}  # Shares are in database, not sent via email
        )
        
        print(f"✅ Notifications sent successfully!")
        print(f"🔗 Voting session: {session_data['session_id']}")
        
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        import traceback
        traceback.print_exc()


def get_video_source_from_env() -> VideoSource:
    """
    Create video source from environment configuration
    
    Returns:
        VideoSource instance based on .env settings
    """
    source_type = os.getenv('VIDEO_SOURCE_TYPE', 'webcam').lower()
    
    if source_type == 'webcam':
        camera_index = int(os.getenv('WEBCAM_INDEX', '0'))
        return create_video_source('webcam', camera_index=camera_index)
    
    elif source_type == 'rtsp':
        rtsp_url = os.getenv('RTSP_URL')
        if not rtsp_url:
            raise ValueError("RTSP_URL not configured in .env")
        
        return create_video_source(
            'rtsp',
            rtsp_url=rtsp_url,
            username=os.getenv('RTSP_USERNAME'),
            password=os.getenv('RTSP_PASSWORD')
        )
    
    elif source_type == 'file':
        file_path = os.getenv('VIDEO_FILE_PATH')
        if not file_path:
            raise ValueError("VIDEO_FILE_PATH not configured in .env")
        
        loop = os.getenv('VIDEO_FILE_LOOP', 'false').lower() == 'true'
        return create_video_source('file', file_path=file_path, loop=loop)
    
    else:
        raise ValueError(f"Unknown VIDEO_SOURCE_TYPE: {source_type}")


def violence_detection(model_id: str = None, video_source: VideoSource = None):
    """
    Main violence detection loop with modular video source
    
    Args:
        model_id: Model ID to use (None = active model from registry)
        video_source: VideoSource instance (None = use .env config)
    """
    # Load model via adapter
    try:
        model_adapter = load_model(model_id)
        model_info = model_adapter.get_info()
        
        print(f"✅ Model loaded: {model_info['name']}")
        print(f"   Version: {model_info['version']}")
        print(f"   Format: {model_info['format']}")
        print(f"   Classes: {model_info['classes']}")
        print(f"   Threshold: {model_info['threshold']}")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Get model parameters
    sequence_length = model_adapter.sequence_length
    classes = model_adapter.classes
    
    # Create video source if not provided
    if video_source is None:
        try:
            video_source = get_video_source_from_env()
        except Exception as e:
            print(f"❌ Error creating video source: {e}")
            return
    
    # Open video source
    if not video_source.open():
        print(f"❌ Cannot open video source: {video_source}")
        return
    
    fps = video_source.get_fps()
    print(f"✅ Video source started: {video_source}")
    print(f"   FPS: {fps}")
    
    # Frame queue
    frames_queue = deque(maxlen=sequence_length)
    
    predicted_class_name = ''
    confidence = 0.0
    recording = False
    video_writer = None
    frames_recorded = 0
    frames_to_record = int(RECORDING_DURATION * fps)
    current_video_path = None
    current_timestamp = None
    
    print(f"\n🎥 Violence detection active (sequence length: {sequence_length})")
    print("Press 'q' to quit.\n")
    
    try:
        while True:
            # Read frame
            ok, frame = video_source.read()
            if not ok:
                print("⚠️  Failed to read frame")
                break
            
            # Copy frame for display
            display_frame = frame.copy()
            
            # Add frame to queue (no preprocessing here, adapter handles it)
            frames_queue.append(frame)
            
            # Predict when queue is full
            if len(frames_queue) == sequence_length:
                try:
                    # Convert deque to list for adapter
                    frames_list = list(frames_queue)
                    
                    # Predict using adapter
                    predicted_class_name, confidence = model_adapter.predict(frames_list)
                    
                    # Check if violence detected
                    is_violence = model_adapter.is_positive_detection(predicted_class_name, confidence)
                    
                    # Start recording if violence detected
                    if is_violence and not recording:
                        recording = True
                        frames_recorded = 0
                        video_writer, current_video_path, current_timestamp = create_video_writer(frame, fps)
                        print(f"🚨 Violence detected! Recording started: {current_video_path}")
                        
                except Exception as e:
                    print(f"⚠️  Prediction error: {e}")
                    continue
            
            # Record frame if recording
            if recording:
                video_writer.write(frame)
                frames_recorded += 1
                
                # Check if recording complete
                if frames_recorded >= frames_to_record:
                    recording = False
                    video_writer.release()
                    video_writer = None
                    print(f"✅ Recording complete: {frames_recorded} frames")
                    
                    # Process recorded video
                    if current_video_path and current_timestamp:
                        process_recorded_video(current_video_path, current_timestamp)
                        current_video_path = None
                        current_timestamp = None
            
            # Display status on frame
            if predicted_class_name:
                # Determine color based on prediction
                is_violence = model_adapter.is_positive_detection(predicted_class_name, confidence)
                
                if is_violence:
                    color = (0, 0, 255)  # Red
                    status = "🔴 RECORDING..." if recording else "🚨 VIOLENCE DETECTED"
                else:
                    color = (0, 255, 0)  # Green
                    status = "✅ Normal"
                
                # Display prediction
                cv2.putText(display_frame, f"{predicted_class_name}", 
                           (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                cv2.putText(display_frame, f"Confidence: {confidence:.2f}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                
                # Display recording status
                if recording:
                    cv2.putText(display_frame, status,
                               (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(display_frame, f"Frame: {frames_recorded}/{frames_to_record}",
                               (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display model and source info
            cv2.putText(display_frame, f"Model: {model_info['name'][:30]}", 
                       (10, display_frame.shape[0] - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f"Source: {str(video_source)[:40]}", 
                       (10, display_frame.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('Secure Violence Detection System', display_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n👋 Stopping detection...")
                break
    
    finally:
        # Cleanup
        if video_writer is not None:
            video_writer.release()
            print("✅ Video writer released")
        
        video_source.release()
        cv2.destroyAllWindows()
        print("✅ Video source released")


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🔒 Secure Surveillance System - Violence Detection")
    print("=" * 60)
    print("\nInitializing...")
    
    # Check database connection
    try:
        session = db_manager.get_session()
        session.execute('SELECT 1')
        session.close()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and configured correctly")
        exit(1)
    
    # Get model ID from command line (optional)
    model_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if model_id:
        print(f"\n📦 Using model: {model_id}")
    else:
        print("\n📦 Using active model from registry")
    
    # Display video source configuration
    source_type = os.getenv('VIDEO_SOURCE_TYPE', 'webcam')
    print(f"\n📹 Video source: {source_type.upper()}")
    
    # Start detection
    violence_detection(model_id)
