import tkinter as tk
import threading
import time
import ctypes
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import sys
import os
import winreg

class CapsLockNotifier:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # 去掉窗口边框
        self.root.attributes("-topmost", True)  # 置顶
        self.root.geometry(f"150x50+0+100")  # 屏幕左侧显示
        self.label = tk.Label(self.root, text="", font=("微软雅黑", 18), bg="yellow")
        self.label.pack(fill=tk.BOTH, expand=True)
        self.root.withdraw()  # 初始隐藏
        self.is_showing = False
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

    def show(self, text):
        self.label.config(text=text)
        self.root.deiconify()
        self.is_showing = True
        self.root.after(1000, self.hide)  # 1秒后自动隐藏

    def hide(self):
        self.root.withdraw()
        self.is_showing = False

    def run(self):
        self.root.mainloop()

    def setup_tray(self):
        # 兼容PyInstaller打包后的路径
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "capslock.ico")
        image = Image.open(icon_path)
        menu = (
            item(
                '开机启动',
                self.toggle_autostart,
                checked=lambda item: self.is_autostart_enabled()
            ),
            item('退出', self.quit_app)
        )
        self.icon = pystray.Icon("capslock_notifier", image, "CapsLock Notifier", menu)
        self.icon.run()

    def get_autostart_path(self):
        return r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_autostart_enabled(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.get_autostart_path(), 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, "CapsLockNotifier")
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            return value == f'"{exe_path}" "{script_path}"'
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)

    def toggle_autostart(self, icon, item):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.get_autostart_path(), 0, winreg.KEY_ALL_ACCESS)
        exe_path = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        if self.is_autostart_enabled():
            try:
                winreg.DeleteValue(key, "CapsLockNotifier")
            except FileNotFoundError:
                pass
        else:
            winreg.SetValueEx(key, "CapsLockNotifier", 0, winreg.REG_SZ, f'"{exe_path}" "{script_path}"')
        winreg.CloseKey(key)

    def quit_app(self, icon, item):
        icon.stop()
        self.root.quit()
        os._exit(0)

def monitor_capslock(notifier):
    # Use Windows API to get CapsLock state
    def get_capslock_state():
        # 0x14 is the virtual-key code for CapsLock
        return bool(ctypes.WinDLL("User32.dll").GetKeyState(0x14) & 1)

    last_state = get_capslock_state()
    while True:
        current_state = get_capslock_state()
        if current_state != last_state:
            if current_state:
                notifier.show("capslock 开")
            else:
                notifier.show("capslock 关")
            last_state = current_state
        time.sleep(0.1)

if __name__ == "__main__":
    notifier = CapsLockNotifier()
    t = threading.Thread(target=monitor_capslock, args=(notifier,), daemon=True)
    t.start()
    notifier.run()
