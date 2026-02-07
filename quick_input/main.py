"""
速成輸入法 - 主程式
Quick Input Method for Windows - Main Application

使用方式：
    python -m quick_input.main

功能：
    - Ctrl+Space 切換中英文輸入模式
    - 輸入 1-2 個英文字母（速成碼）後顯示候選字
    - 數字鍵 1-9 或滑鼠點擊選字
    - Space 選取第一個候選字
    - PageUp / PageDown 翻頁
    - Escape 取消當前輸入
    - z + 符號鍵 輸入中文標點
    - 選字視窗可拖曳邊界調整大小
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import queue
import threading

from .engine import QuickEngine
from .candidate_window import CandidateWindow, StatusBar
from .keyboard_hook import create_keyboard_hook


class QuickInputApp:
    """速成輸入法主應用程式"""

    def __init__(self):
        self._engine = QuickEngine()
        self._event_queue = queue.Queue()

        # 建立 tkinter 根視窗（隱藏）
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.title('速成輸入法')

        # 設置應用程式圖示（如果有的話）
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            if os.path.exists(icon_path):
                self._root.iconbitmap(icon_path)
        except Exception:
            pass

        # 建立選字視窗（可拉伸）
        self._candidate_window = CandidateWindow(
            self._root,
            on_select=self._on_mouse_select,
            on_page=self._on_mouse_page,
        )

        # 建立狀態列
        self._status_bar = StatusBar(
            self._root,
            on_toggle=self._toggle_from_ui,
        )

        # 建立鍵盤鉤子
        self._hook = create_keyboard_hook(self._on_key_event)

        # 非 Windows 平台的測試模式：建立測試輸入視窗
        if sys.platform != 'win32':
            self._create_test_window()

        # 定期處理事件佇列
        self._root.after(50, self._process_queue)

    def _create_test_window(self):
        """建立測試用輸入視窗（非 Windows 平台）"""
        self._test_window = tk.Toplevel(self._root)
        self._test_window.title('速成輸入法 - 測試輸入區')
        self._test_window.geometry('500x300')

        info_label = tk.Label(
            self._test_window,
            text='（非 Windows 平台測試模式）\n'
                 '在此視窗中按鍵測試速成輸入法\n'
                 'Ctrl+Space 切換中英文',
            font=('Microsoft JhengHei', 10),
            justify=tk.LEFT,
            padx=10, pady=5,
        )
        info_label.pack(fill=tk.X)

        self._test_text = tk.Text(
            self._test_window,
            font=('Microsoft JhengHei', 14),
            wrap=tk.WORD,
        )
        self._test_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 綁定按鍵
        self._test_text.bind('<KeyPress>', self._on_test_key)
        self._test_window.protocol('WM_DELETE_WINDOW', self._quit)

    def _on_test_key(self, event):
        """測試視窗按鍵處理"""
        key = event.keysym.lower()

        # Ctrl+Space 切換
        if (event.state & 0x4) and key == 'space':
            self._toggle_from_ui()
            return 'break'

        if not self._engine.active:
            return  # 英文模式，正常輸入

        # 處理按鍵
        intercept = self._process_key(key)
        if intercept:
            return 'break'

    def _on_key_event(self, key_name):
        """
        鍵盤鉤子回調（在鉤子執行緒中被調用）
        透過事件佇列通知主執行緒
        返回 True 表示攔截此按鍵
        """
        if key_name == 'toggle':
            self._event_queue.put(('toggle', None))
            return True

        if not self._engine.active:
            return False

        # 需要攔截的按鍵
        should_intercept = False

        # 字母鍵 a-z
        if len(key_name) == 1 and key_name.isalpha():
            should_intercept = True
        # 數字鍵 1-9（有候選字時）
        elif key_name.isdigit() and key_name != '0' and self._engine.candidates:
            should_intercept = True
        # 功能鍵
        elif key_name in ('space', 'return', 'escape', 'backspace', 'prior', 'next'):
            if key_name == 'space' and not self._engine.input_buffer and not self._engine.candidates:
                should_intercept = False  # 沒有輸入時空白鍵正常放行
            elif key_name == 'return' and not self._engine.input_buffer:
                should_intercept = False
            else:
                should_intercept = True
        # 句號、逗號（有候選字時用於翻頁）
        elif key_name == '.' and self._engine.candidates:
            should_intercept = True

        if should_intercept:
            self._event_queue.put(('key', key_name))
        return should_intercept

    def _process_queue(self):
        """處理事件佇列（在主執行緒中）"""
        try:
            while True:
                event_type, data = self._event_queue.get_nowait()
                if event_type == 'toggle':
                    self._toggle_from_ui()
                elif event_type == 'key':
                    self._process_key(data)
                elif event_type == 'commit':
                    self._commit_char(data)
        except queue.Empty:
            pass
        finally:
            self._root.after(30, self._process_queue)

    def _toggle_from_ui(self):
        """從 UI 切換輸入模式"""
        is_active = self._engine.toggle()
        status = self._engine.get_status_text()
        self._status_bar.update_status(status)
        if not is_active:
            self._candidate_window.hide()

    def _process_key(self, key_name):
        """
        處理按鍵（在主執行緒中）
        返回 True 如果按鍵被處理
        """
        action, data = self._engine.handle_key(key_name)

        if action == 'candidates':
            self._update_candidate_display()
            return True

        elif action == 'commit':
            self._commit_char(data)
            self._candidate_window.hide()
            return True

        elif action == 'commit_and_continue':
            char, new_candidates = data
            self._commit_char(char)
            self._update_candidate_display()
            return True

        elif action == 'reset':
            self._candidate_window.hide()
            return True

        elif action == 'page':
            self._update_candidate_display()
            return True

        elif action == 'buffer':
            self._candidate_window.update_input_only(
                data, self._engine.get_status_text()
            )
            return True

        return False

    def _update_candidate_display(self):
        """更新候選字視窗顯示"""
        self._candidate_window.update_candidates(
            candidates=self._engine.page_candidates,
            page=self._engine.page,
            total_pages=self._engine.total_pages,
            input_display=self._engine.input_display,
            status_text=self._engine.get_status_text(),
        )

    def _commit_char(self, char):
        """確認輸入字元"""
        if sys.platform == 'win32':
            # Windows: 使用 SendInput 發送 Unicode 字元
            self._hook.send_unicode_char(char)
        else:
            # 測試模式：直接插入到測試文字框
            if hasattr(self, '_test_text'):
                self._test_text.insert(tk.INSERT, char)

    def _on_mouse_select(self, index):
        """處理滑鼠點擊選字"""
        char = self._engine.select_candidate(index)
        if char:
            self._commit_char(char)
            self._candidate_window.hide()

    def _on_mouse_page(self, direction):
        """處理滑鼠翻頁"""
        if direction == 'next':
            self._engine.handle_key('next')
        else:
            self._engine.handle_key('prior')
        self._update_candidate_display()

    def _quit(self):
        """退出程式"""
        self._hook.stop()
        self._candidate_window.destroy()
        self._status_bar.destroy()
        self._root.quit()
        self._root.destroy()

    def run(self):
        """啟動應用程式"""
        print("=" * 50)
        print("  速成輸入法 Quick Input Method v1.0")
        print("=" * 50)
        print()
        print("  Ctrl+Space  切換中/英文模式")
        print("  a-y         輸入速成碼（首碼+尾碼）")
        print("  1-9         選擇候選字")
        print("  Space       選擇第一個候選字")
        print("  PgUp/PgDn   翻頁")
        print("  Escape      取消輸入")
        print("  z+符號      中文標點符號")
        print()
        print("  選字視窗可以用滑鼠拖曳邊界來調整大小")
        print()

        if sys.platform != 'win32':
            print("  [測試模式] 非 Windows 平台，在測試視窗中操作")
            print()

        # 啟動鍵盤鉤子
        self._hook.start()

        # 啟動 tkinter 主迴圈
        try:
            self._root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self._hook.stop()


def main():
    app = QuickInputApp()
    app.run()


if __name__ == '__main__':
    main()
