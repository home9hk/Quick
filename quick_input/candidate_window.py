"""
速成輸入法 - 可拉伸選字視窗
Resizable Candidate Selection Window

特點：
- 視窗邊界可用滑鼠拉伸放大和縮小
- 候選字以網格顯示，自動適應視窗大小
- 滑鼠點擊選字
- 鍵盤數字鍵 1-9 選字
- PageUp / PageDown 翻頁
"""

import tkinter as tk
from tkinter import font as tkfont
from .config import (
    CANDIDATE_WINDOW_WIDTH, CANDIDATE_WINDOW_HEIGHT,
    CANDIDATE_WINDOW_MIN_WIDTH, CANDIDATE_WINDOW_MIN_HEIGHT,
    CANDIDATES_PER_PAGE, CANDIDATE_FONT_FAMILY, CANDIDATE_FONT_SIZE,
    STATUS_FONT_SIZE, CANGJIE_RADICALS, THEME,
)


class CandidateWindow:
    """
    可拉伸的選字視窗

    使用標準 tkinter 視窗框架，使用者可以：
    - 在視窗邊界（上下左右及四角）用滑鼠拖曳來放大或縮小視窗
    - 點擊候選字來選取
    - 使用鍵盤快速選字
    """

    def __init__(self, root, on_select=None, on_page=None):
        """
        Args:
            root: tkinter root window
            on_select: 回調函式，選字時調用 on_select(index)
            on_page: 回調函式，翻頁時調用 on_page(direction) direction='next'|'prev'
        """
        self._root = root
        self._on_select = on_select
        self._on_page = on_page
        self._visible = False
        self._candidates = []
        self._page = 0
        self._total_pages = 0
        self._input_display = ''
        self._status_text = '速成'

        self._window = tk.Toplevel(root)
        self._window.title('速成輸入法 - 選字')
        self._window.withdraw()  # 初始隱藏

        # ===== 允許視窗拉伸 =====
        self._window.resizable(True, True)
        self._window.minsize(CANDIDATE_WINDOW_MIN_WIDTH, CANDIDATE_WINDOW_MIN_HEIGHT)
        self._window.geometry(f'{CANDIDATE_WINDOW_WIDTH}x{CANDIDATE_WINDOW_HEIGHT}')

        # 視窗置頂
        self._window.attributes('-topmost', True)

        # 防止視窗被關閉（改為隱藏）
        self._window.protocol('WM_DELETE_WINDOW', self.hide)

        # 設置整體背景
        self._window.configure(bg=THEME['bg'])

        self._build_ui()
        self._bind_resize()

    def _build_ui(self):
        """建構使用者介面"""
        # ----- 頂部：輸入顯示區 -----
        self._header_frame = tk.Frame(
            self._window, bg=THEME['header_bg'], padx=8, pady=4
        )
        self._header_frame.pack(fill=tk.X, side=tk.TOP)

        self._status_label = tk.Label(
            self._header_frame,
            text='[ 速成 ]',
            font=(CANDIDATE_FONT_FAMILY, STATUS_FONT_SIZE, 'bold'),
            bg=THEME['header_bg'], fg=THEME['header_fg'],
            padx=4,
        )
        self._status_label.pack(side=tk.LEFT)

        self._input_label = tk.Label(
            self._header_frame,
            text='',
            font=(CANDIDATE_FONT_FAMILY, CANDIDATE_FONT_SIZE, 'bold'),
            bg=THEME['header_bg'], fg='#FFFF00',
            padx=8,
        )
        self._input_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._page_label = tk.Label(
            self._header_frame,
            text='',
            font=(CANDIDATE_FONT_FAMILY, STATUS_FONT_SIZE),
            bg=THEME['header_bg'], fg=THEME['header_fg'],
            padx=4,
        )
        self._page_label.pack(side=tk.RIGHT)

        # ----- 中部：候選字區域（可拉伸自適應）-----
        self._cand_frame = tk.Frame(self._window, bg=THEME['bg'])
        self._cand_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 候選字按鈕列表
        self._cand_buttons = []
        self._rebuild_candidate_grid()

        # ----- 底部：操作提示 -----
        self._footer_frame = tk.Frame(
            self._window, bg=THEME['status_bg'], padx=8, pady=3
        )
        self._footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self._hint_label = tk.Label(
            self._footer_frame,
            text='1-9選字 | Space確認 | PgUp/PgDn翻頁 | Esc取消 | 拖曳邊界調整大小',
            font=(CANDIDATE_FONT_FAMILY, 9),
            bg=THEME['status_bg'], fg=THEME['status_fg'],
        )
        self._hint_label.pack(side=tk.LEFT)

        # ----- 翻頁按鈕 -----
        self._nav_frame = tk.Frame(
            self._footer_frame, bg=THEME['status_bg']
        )
        self._nav_frame.pack(side=tk.RIGHT)

        self._prev_btn = tk.Button(
            self._nav_frame, text='◀', width=3,
            font=(CANDIDATE_FONT_FAMILY, 9),
            command=lambda: self._on_page_click('prev'),
            relief=tk.FLAT, bg=THEME['status_bg'],
        )
        self._prev_btn.pack(side=tk.LEFT, padx=2)

        self._next_btn = tk.Button(
            self._nav_frame, text='▶', width=3,
            font=(CANDIDATE_FONT_FAMILY, 9),
            command=lambda: self._on_page_click('next'),
            relief=tk.FLAT, bg=THEME['status_bg'],
        )
        self._next_btn.pack(side=tk.LEFT, padx=2)

    def _rebuild_candidate_grid(self):
        """重建候選字網格佈局"""
        # 清除舊的按鈕
        for btn in self._cand_buttons:
            btn.destroy()
        self._cand_buttons = []

        # 配置 grid 行列權重，使其可拉伸
        # 使用 3 列 x 3 行 的網格（共 9 個位置）
        cols = 3
        rows = (CANDIDATES_PER_PAGE + cols - 1) // cols

        for i in range(cols):
            self._cand_frame.columnconfigure(i, weight=1, uniform='col')
        for i in range(rows):
            self._cand_frame.rowconfigure(i, weight=1, uniform='row')

        for idx in range(CANDIDATES_PER_PAGE):
            row = idx // cols
            col = idx % cols

            btn = tk.Button(
                self._cand_frame,
                text='',
                font=(CANDIDATE_FONT_FAMILY, CANDIDATE_FONT_SIZE),
                bg=THEME['bg'], fg=THEME['fg'],
                activebackground=THEME['highlight_bg'],
                activeforeground=THEME['highlight_fg'],
                relief=tk.FLAT,
                borderwidth=1,
                highlightthickness=1,
                highlightbackground=THEME['border'],
                cursor='hand2',
                anchor='w',
                padx=8, pady=4,
            )
            btn.grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

            # 綁定點擊事件
            btn_idx = idx
            btn.configure(command=lambda i=btn_idx: self._on_candidate_click(i))

            # 滑鼠懸停效果
            btn.bind('<Enter>', lambda e, b=btn: b.configure(
                bg=THEME['highlight_bg'], fg=THEME['highlight_fg']
            ))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(
                bg=THEME['bg'], fg=THEME['fg']
            ))

            self._cand_buttons.append(btn)

    def _bind_resize(self):
        """綁定視窗大小變更事件"""
        self._window.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        """視窗拉伸時自動調整字體大小"""
        if event.widget != self._window:
            return

        # 根據視窗大小動態調整字體
        w = event.width
        h = event.height

        # 計算合適的字體大小（依視窗大小線性縮放）
        base_size = CANDIDATE_FONT_SIZE
        scale_w = w / CANDIDATE_WINDOW_WIDTH
        scale_h = h / CANDIDATE_WINDOW_HEIGHT
        scale = min(scale_w, scale_h)

        new_size = max(12, min(36, int(base_size * scale)))

        for btn in self._cand_buttons:
            btn.configure(font=(CANDIDATE_FONT_FAMILY, new_size))

    def _on_candidate_click(self, index):
        """處理滑鼠點擊候選字"""
        if self._on_select and index < len(self._candidates):
            self._on_select(index)

    def _on_page_click(self, direction):
        """處理翻頁按鈕點擊"""
        if self._on_page:
            self._on_page(direction)

    def update_candidates(self, candidates, page=0, total_pages=0,
                          input_display='', status_text='速成'):
        """
        更新候選字顯示

        Args:
            candidates: 當前頁的候選字列表
            page: 當前頁碼 (0-based)
            total_pages: 總頁數
            input_display: 輸入中的字根顯示
            status_text: 狀態文字
        """
        self._candidates = candidates
        self._page = page
        self._total_pages = total_pages
        self._input_display = input_display

        # 更新輸入顯示
        self._input_label.configure(text=input_display)

        # 更新狀態
        self._status_label.configure(text=f'[ {status_text} ]')

        # 更新頁碼
        if total_pages > 0:
            self._page_label.configure(text=f'{page + 1}/{total_pages}')
        else:
            self._page_label.configure(text='')

        # 更新候選字按鈕
        for i, btn in enumerate(self._cand_buttons):
            if i < len(candidates):
                num = i + 1
                btn.configure(
                    text=f' {num}. {candidates[i]}',
                    state=tk.NORMAL,
                )
            else:
                btn.configure(text='', state=tk.DISABLED)

        # 如果有候選字就顯示視窗
        if candidates:
            self.show()
        elif not input_display:
            self.hide()

    def update_input_only(self, input_display, status_text='速成'):
        """只更新輸入顯示（尚未查到候選字時）"""
        self._input_label.configure(text=input_display)
        self._status_label.configure(text=f'[ {status_text} ]')
        self._page_label.configure(text='')
        for btn in self._cand_buttons:
            btn.configure(text='', state=tk.DISABLED)
        self.show()

    def show(self):
        """顯示選字視窗"""
        if not self._visible:
            self._window.deiconify()
            self._visible = True

    def hide(self):
        """隱藏選字視窗"""
        if self._visible:
            self._window.withdraw()
            self._visible = False

    @property
    def visible(self):
        return self._visible

    def set_position(self, x, y):
        """設定視窗位置"""
        # 確保視窗不超出螢幕
        screen_w = self._window.winfo_screenwidth()
        screen_h = self._window.winfo_screenheight()
        win_w = self._window.winfo_width()
        win_h = self._window.winfo_height()

        if x + win_w > screen_w:
            x = screen_w - win_w
        if y + win_h > screen_h:
            y = screen_h - win_h
        if x < 0:
            x = 0
        if y < 0:
            y = 0

        self._window.geometry(f'+{x}+{y}')

    def destroy(self):
        """銷毀視窗"""
        self._window.destroy()


class StatusBar:
    """
    狀態列 - 顯示目前輸入法狀態
    懸浮在螢幕右下角的小視窗
    """

    def __init__(self, root, on_toggle=None):
        self._root = root
        self._on_toggle = on_toggle

        self._window = tk.Toplevel(root)
        self._window.title('速成')
        self._window.overrideredirect(True)  # 無邊框
        self._window.attributes('-topmost', True)
        self._window.attributes('-alpha', 0.9)

        # 放在螢幕右下角
        screen_w = self._window.winfo_screenwidth()
        screen_h = self._window.winfo_screenheight()
        self._window.geometry(f'80x32+{screen_w - 100}+{screen_h - 70}')

        self._frame = tk.Frame(
            self._window, bg=THEME['header_bg'],
            highlightthickness=1, highlightbackground=THEME['border'],
        )
        self._frame.pack(fill=tk.BOTH, expand=True)

        self._label = tk.Label(
            self._frame,
            text='EN',
            font=(CANDIDATE_FONT_FAMILY, 11, 'bold'),
            bg=THEME['header_bg'], fg=THEME['header_fg'],
            cursor='hand2',
        )
        self._label.pack(fill=tk.BOTH, expand=True)

        # 點擊切換
        self._label.bind('<Button-1>', lambda e: self._toggle())

        # 拖曳移動
        self._drag_data = {'x': 0, 'y': 0}
        self._label.bind('<Button-3>', self._start_drag)
        self._label.bind('<B3-Motion>', self._do_drag)

    def _toggle(self):
        if self._on_toggle:
            self._on_toggle()

    def _start_drag(self, event):
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def _do_drag(self, event):
        x = self._window.winfo_x() + (event.x - self._drag_data['x'])
        y = self._window.winfo_y() + (event.y - self._drag_data['y'])
        self._window.geometry(f'+{x}+{y}')

    def update_status(self, text):
        """更新狀態文字"""
        self._label.configure(text=text)
        if text == '速成':
            self._label.configure(bg='#D4380D', fg='#FFFFFF')
            self._frame.configure(bg='#D4380D')
        else:
            self._label.configure(bg=THEME['header_bg'], fg=THEME['header_fg'])
            self._frame.configure(bg=THEME['header_bg'])

    def destroy(self):
        self._window.destroy()
