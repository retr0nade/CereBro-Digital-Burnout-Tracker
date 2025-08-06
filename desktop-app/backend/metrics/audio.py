import platform
import time

def get_audio_level():
    """
    Get current audio input level (microphone).
    Returns a value between 0-100 representing audio activity.
    """
    try:
        if platform.system() == 'Windows':
            # Windows audio monitoring would require additional libraries
            # For now, return a placeholder implementation
            return 0
        else:
            # TODO: Implement for Mac/Linux
            return 0
    except Exception as e:
        print(f"Audio monitoring error: {e}")
        return 0

def is_audio_active(threshold=10):
    """
    Check if audio input is above threshold.
    """
    return get_audio_level() > threshold
