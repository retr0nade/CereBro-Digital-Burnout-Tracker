import platform
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Windows-only MVP implementation
# TODO: Future cross-platform support for macOS and Linux
if platform.system() == 'Windows':
    import win32gui, win32process, psutil
    
    def get_foreground_app():
        """Get the foreground application name and window title (Windows only)"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return "unknown", ""
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Validate process ID
            if pid is None or pid <= 0:
                logger.warning(f"Invalid process ID: {pid}")
                return "unknown", win32gui.GetWindowText(hwnd)
            
            try:
                proc = psutil.Process(pid)
                return proc.name(), win32gui.GetWindowText(hwnd)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"Error accessing process {pid}: {e}")
                return "unknown", win32gui.GetWindowText(hwnd)
            except ValueError as e:
                logger.warning(f"Invalid process ID {pid}: {e}")
                return "unknown", win32gui.GetWindowText(hwnd)
                
        except Exception as e:
            logger.error(f"Error getting foreground app: {e}")
            return "unknown", ""
# else:
#     # Non-Windows platforms not supported in MVP
#     # TODO: Implement macOS support using NSWorkspace/Quartz
#     # TODO: Implement Linux support using X11/Wayland
#     def get_foreground_app():
#         """Placeholder for non-Windows platforms (not supported in MVP)"""
#         logger.warning(f"get_foreground_app() not implemented for {platform.system()}")
#         return "unknown", ""
