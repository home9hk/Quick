"""
速成輸入法 - Windows 鍵盤鉤子模組
Global Keyboard Hook for Windows

使用 Windows API (ctypes) 實作全域鍵盤攔截：
- SetWindowsHookExW  安裝低階鍵盤鉤子
- UnhookWindowsHookEx  解除鉤子
- CallNextHookEx  傳遞給下一個鉤子
- SendInput  模擬鍵盤輸入（插入選中的中文字）

在非 Windows 平台上提供模擬實作供開發測試用。
"""

import sys
import threading
import queue

# Virtual key codes
VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12      # Alt
VK_CAPITAL = 0x14
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21     # Page Up
VK_NEXT = 0x22      # Page Down
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_DELETE = 0x2E

# WH_KEYBOARD_LL = 13
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

# 虛擬按鍵碼到按鍵名稱的映射
VK_TO_NAME = {
    VK_BACK: 'backspace',
    VK_TAB: 'tab',
    VK_RETURN: 'return',
    VK_ESCAPE: 'escape',
    VK_SPACE: 'space',
    VK_PRIOR: 'prior',
    VK_NEXT: 'next',
    VK_LEFT: 'left',
    VK_UP: 'up',
    VK_RIGHT: 'right',
    VK_DOWN: 'down',
    VK_DELETE: 'delete',
}

# 字母鍵 A-Z 的虛擬碼是 0x41 - 0x5A
# 數字鍵 0-9 的虛擬碼是 0x30 - 0x39


def _is_windows():
    return sys.platform == 'win32'


if _is_windows():
    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # 定義 KBDLLHOOKSTRUCT
    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ('vkCode', ctypes.wintypes.DWORD),
            ('scanCode', ctypes.wintypes.DWORD),
            ('flags', ctypes.wintypes.DWORD),
            ('time', ctypes.wintypes.DWORD),
            ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
        ]

    # 定義 INPUT 結構 (用於 SendInput)
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ('dx', ctypes.c_long),
            ('dy', ctypes.c_long),
            ('mouseData', ctypes.wintypes.DWORD),
            ('dwFlags', ctypes.wintypes.DWORD),
            ('time', ctypes.wintypes.DWORD),
            ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ('wVk', ctypes.wintypes.WORD),
            ('wScan', ctypes.wintypes.WORD),
            ('dwFlags', ctypes.wintypes.DWORD),
            ('time', ctypes.wintypes.DWORD),
            ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ('uMsg', ctypes.wintypes.DWORD),
            ('wParamL', ctypes.wintypes.WORD),
            ('wParamH', ctypes.wintypes.WORD),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [
            ('mi', MOUSEINPUT),
            ('ki', KEYBDINPUT),
            ('hi', HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ('type', ctypes.wintypes.DWORD),
            ('union', INPUT_UNION),
        ]

    INPUT_KEYBOARD = 1
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP = 0x0002

    # Hook callback type
    HOOKPROC = ctypes.CFUNCTYPE(
        ctypes.c_long,
        ctypes.c_int,
        ctypes.wintypes.WPARAM,
        ctypes.wintypes.LPARAM,
    )


class KeyboardHook:
    """
    Windows 全域鍵盤鉤子

    在背景執行緒中安裝鍵盤鉤子，攔截按鍵事件。
    當速成模式啟用時，攔截字母和數字鍵，透過回調通知主程式。
    """

    def __init__(self, callback):
        """
        Args:
            callback: 按鍵回調函式 callback(key_name) -> bool
                      返回 True 表示攔截此按鍵，False 表示放行
        """
        self._callback = callback
        self._hook = None
        self._thread = None
        self._running = False
        self._hook_proc = None  # 防止被垃圾回收
        self._ctrl_pressed = False
        # 用於標記由 SendInput 發出的按鍵，避免重複攔截
        self._sending = False

    def start(self):
        """啟動鍵盤鉤子"""
        if not _is_windows():
            print("[KeyboardHook] 非 Windows 平台，使用模擬模式")
            return

        self._running = True
        self._thread = threading.Thread(target=self._hook_thread, daemon=True)
        self._thread.start()

    def stop(self):
        """停止鍵盤鉤子"""
        self._running = False
        if _is_windows() and self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def _hook_thread(self):
        """鉤子執行緒 - 安裝鉤子並運行消息泵"""
        if not _is_windows():
            return

        def hook_callback(nCode, wParam, lParam):
            if nCode < 0:
                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

            # 如果正在發送模擬按鍵，不攔截
            if self._sending:
                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = kb.vkCode

                # 追蹤 Ctrl 鍵狀態
                if vk == VK_CONTROL:
                    self._ctrl_pressed = True
                    return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

                # Ctrl+Space 切換輸入法
                if vk == VK_SPACE and self._ctrl_pressed:
                    try:
                        if self._callback('toggle'):
                            return 1  # 攔截
                    except Exception:
                        pass
                    return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

                # 轉換按鍵碼
                key_name = self._vk_to_name(vk)
                if key_name:
                    try:
                        if self._callback(key_name):
                            return 1  # 攔截此按鍵
                    except Exception:
                        pass

            # 追蹤按鍵釋放
            if wParam in (0x0101, 0x0105):  # WM_KEYUP, WM_SYSKEYUP
                kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if kb.vkCode == VK_CONTROL:
                    self._ctrl_pressed = False

            return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

        # 保存引用防止被回收
        self._hook_proc = HOOKPROC(hook_callback)

        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            kernel32.GetModuleHandleW(None),
            0,
        )

        if not self._hook:
            print("[KeyboardHook] 安裝鍵盤鉤子失敗")
            return

        # 消息泵
        msg = ctypes.wintypes.MSG()
        while self._running:
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result in (0, -1):
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None

    def _vk_to_name(self, vk):
        """將虛擬按鍵碼轉為按鍵名稱"""
        # 特殊鍵
        if vk in VK_TO_NAME:
            return VK_TO_NAME[vk]
        # 字母鍵 A-Z
        if 0x41 <= vk <= 0x5A:
            return chr(vk).lower()
        # 數字鍵 0-9
        if 0x30 <= 0x39:
            if 0x30 <= vk <= 0x39:
                return chr(vk)
        # 句號 (OEM_PERIOD)
        if vk == 0xBE:
            return '.'
        # 逗號 (OEM_COMMA)
        if vk == 0xBC:
            return ','
        return None

    def send_unicode_char(self, char):
        """
        使用 SendInput 發送 Unicode 字元到當前焦點視窗
        """
        if not _is_windows():
            print(f"[SendInput 模擬] 發送字元: {char}")
            return

        self._sending = True
        try:
            inputs = []
            for ch in char:
                code = ord(ch)
                # Key down
                ki_down = KEYBDINPUT(
                    wVk=0,
                    wScan=code,
                    dwFlags=KEYEVENTF_UNICODE,
                    time=0,
                    dwExtraInfo=None,
                )
                inp_down = INPUT(type=INPUT_KEYBOARD)
                inp_down.union.ki = ki_down
                inputs.append(inp_down)

                # Key up
                ki_up = KEYBDINPUT(
                    wVk=0,
                    wScan=code,
                    dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                    time=0,
                    dwExtraInfo=None,
                )
                inp_up = INPUT(type=INPUT_KEYBOARD)
                inp_up.union.ki = ki_up
                inputs.append(inp_up)

            n = len(inputs)
            arr = (INPUT * n)(*inputs)
            user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
        finally:
            self._sending = False

    def send_backspace(self, count=1):
        """發送退格鍵（用於刪除已輸入的英文字母）"""
        if not _is_windows():
            return

        self._sending = True
        try:
            inputs = []
            for _ in range(count):
                ki_down = KEYBDINPUT(
                    wVk=VK_BACK, wScan=0, dwFlags=0, time=0, dwExtraInfo=None,
                )
                inp_down = INPUT(type=INPUT_KEYBOARD)
                inp_down.union.ki = ki_down
                inputs.append(inp_down)

                ki_up = KEYBDINPUT(
                    wVk=VK_BACK, wScan=0,
                    dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None,
                )
                inp_up = INPUT(type=INPUT_KEYBOARD)
                inp_up.union.ki = ki_up
                inputs.append(inp_up)

            n = len(inputs)
            arr = (INPUT * n)(*inputs)
            user32.SendInput(n, ctypes.byref(arr), ctypes.sizeof(INPUT))
        finally:
            self._sending = False


class MockKeyboardHook:
    """
    模擬鍵盤鉤子 - 用於非 Windows 平台開發和測試
    接收來自 tkinter 視窗的鍵盤事件
    """

    def __init__(self, callback):
        self._callback = callback
        self._sending = False

    def start(self):
        pass

    def stop(self):
        pass

    def bind_to_window(self, window):
        """綁定到 tkinter 視窗以接收按鍵事件"""
        window.bind('<KeyPress>', self._on_key_press)

    def _on_key_press(self, event):
        if self._sending:
            return

        key = event.keysym.lower()

        # Ctrl+Space
        if event.state & 0x4 and key == 'space':
            self._callback('toggle')
            return 'break'

        result = self._callback(key)
        if result:
            return 'break'

    def send_unicode_char(self, char):
        print(f"[Mock SendInput] 發送字元: {char}")

    def send_backspace(self, count=1):
        print(f"[Mock SendInput] 發送退格 x{count}")


def create_keyboard_hook(callback):
    """
    工廠函式：根據平台建立對應的鍵盤鉤子

    Args:
        callback: 按鍵回調函式

    Returns:
        KeyboardHook 或 MockKeyboardHook 實例
    """
    if _is_windows():
        return KeyboardHook(callback)
    else:
        return MockKeyboardHook(callback)
