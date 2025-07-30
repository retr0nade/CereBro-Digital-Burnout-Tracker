import platform
if platform.system() == 'Windows':
    import ctypes
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    def get_idle_seconds():
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return millis // 1000
        return 0
else:
    def get_idle_seconds():
        # TODO: MacOS/Linux idle detection
        return 0
