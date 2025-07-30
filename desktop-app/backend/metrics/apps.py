import platform
if platform.system() == 'Windows':
    import win32gui, win32process, psutil
    def get_foreground_app():
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name(), win32gui.GetWindowText(hwnd)
else:
    def get_foreground_app():
        # TODO: Add Mac/Linux support
        return "unknown", ""
