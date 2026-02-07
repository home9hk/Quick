"""
速成輸入法引擎 - Quick Input Method Engine
處理按鍵輸入、查詢碼表、管理候選字
"""

import os
from .config import CANGJIE_RADICALS, CANDIDATES_PER_PAGE
from .quick_dict import QUICK_DICT, PUNCTUATION_MAP, load_external_dict, merge_dicts


class QuickEngine:
    """速成輸入法引擎"""

    def __init__(self):
        self._dict = dict(QUICK_DICT)
        self._load_user_dict()
        self._input_buffer = ''       # 目前輸入的碼 (最多2個字母)
        self._candidates = []          # 當前候選字列表
        self._page = 0                 # 當前頁碼
        self._active = False           # 是否啟用中文輸入模式
        self._punctuation_mode = False # 是否在標點符號模式 (z鍵觸發)

    def _load_user_dict(self):
        """載入使用者自訂碼表"""
        user_dict_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'user_dict.txt'
        )
        if os.path.exists(user_dict_path):
            extra = load_external_dict(user_dict_path)
            self._dict = merge_dicts(self._dict, extra)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        if not value:
            self.reset()

    @property
    def input_buffer(self):
        return self._input_buffer

    @property
    def input_display(self):
        """顯示目前輸入的字根名稱"""
        return ''.join(CANGJIE_RADICALS.get(c, c) for c in self._input_buffer)

    @property
    def candidates(self):
        return self._candidates

    @property
    def page(self):
        return self._page

    @property
    def total_pages(self):
        if not self._candidates:
            return 0
        return (len(self._candidates) - 1) // CANDIDATES_PER_PAGE + 1

    @property
    def page_candidates(self):
        """取得當前頁的候選字"""
        start = self._page * CANDIDATES_PER_PAGE
        end = start + CANDIDATES_PER_PAGE
        return self._candidates[start:end]

    def reset(self):
        """重置輸入狀態"""
        self._input_buffer = ''
        self._candidates = []
        self._page = 0
        self._punctuation_mode = False

    def toggle(self):
        """切換中英文模式"""
        self._active = not self._active
        self.reset()
        return self._active

    def handle_key(self, key):
        """
        處理按鍵輸入
        返回: (action, data)
            action 可能的值:
            - 'candidates': 顯示候選字, data = page_candidates
            - 'commit': 確認輸入, data = 選中的字
            - 'reset': 重置, data = None
            - 'page': 翻頁, data = page_candidates
            - 'pass': 不處理, data = None
            - 'buffer': 更新輸入緩衝, data = input_display
        """
        if not self._active:
            return ('pass', None)

        # 處理標點符號模式
        if self._punctuation_mode:
            self._punctuation_mode = False
            punct_key = 'z' + key
            if punct_key in PUNCTUATION_MAP:
                char = PUNCTUATION_MAP[punct_key]
                self.reset()
                return ('commit', char)
            else:
                self.reset()
                return ('reset', None)

        # z 鍵進入標點符號模式
        if key == 'z' and not self._input_buffer:
            self._punctuation_mode = True
            self._input_buffer = 'z'
            return ('buffer', '符')

        # 數字鍵選字 (1-9)
        if key.isdigit() and key != '0' and self._candidates:
            idx = int(key) - 1
            page_cands = self.page_candidates
            if 0 <= idx < len(page_cands):
                char = page_cands[idx]
                self.reset()
                return ('commit', char)
            return ('pass', None)

        # 空白鍵 - 若有候選字則選第一個，否則輸出空格
        if key == 'space':
            if self._candidates:
                char = self.page_candidates[0]
                self.reset()
                return ('commit', char)
            elif self._input_buffer:
                self.reset()
                return ('reset', None)
            return ('pass', None)

        # Enter 鍵 - 清除輸入
        if key == 'return':
            if self._input_buffer:
                self.reset()
                return ('reset', None)
            return ('pass', None)

        # Escape 鍵 - 清除輸入
        if key == 'escape':
            if self._input_buffer or self._candidates:
                self.reset()
                return ('reset', None)
            return ('pass', None)

        # Backspace 鍵 - 刪除最後一個字根
        if key == 'backspace':
            if self._input_buffer:
                self._input_buffer = self._input_buffer[:-1]
                if self._input_buffer:
                    self._lookup()
                    return ('candidates', self.page_candidates)
                else:
                    self._candidates = []
                    self._page = 0
                    return ('reset', None)
            return ('pass', None)

        # PageDown / 下一頁
        if key in ('next', 'pagedown', '.'):
            if self._candidates and key == '.' and not self._input_buffer:
                return ('pass', None)
            if self._candidates:
                if self._page < self.total_pages - 1:
                    self._page += 1
                else:
                    self._page = 0
                return ('page', self.page_candidates)
            return ('pass', None)

        # PageUp / 上一頁
        if key in ('prior', 'pageup'):
            if self._candidates:
                if self._page > 0:
                    self._page -= 1
                else:
                    self._page = self.total_pages - 1
                return ('page', self.page_candidates)
            return ('pass', None)

        # 字母鍵 a-y (速成碼輸入)
        if key.isalpha() and len(key) == 1 and key.lower() in CANGJIE_RADICALS:
            letter = key.lower()
            if len(self._input_buffer) < 2:
                self._input_buffer += letter
                self._lookup()
                if len(self._input_buffer) >= 1:
                    return ('candidates', self.page_candidates)
            else:
                # 已經有2個碼，自動選第一個候選字然後開始新輸入
                if self._candidates:
                    char = self.page_candidates[0]
                    self.reset()
                    self._input_buffer = letter
                    self._lookup()
                    return ('commit_and_continue', (char, self.page_candidates))
                else:
                    self.reset()
                    self._input_buffer = letter
                    self._lookup()
                    return ('candidates', self.page_candidates)

        return ('pass', None)

    def _lookup(self):
        """查詢碼表"""
        self._page = 0
        if not self._input_buffer:
            self._candidates = []
            return

        code = self._input_buffer
        self._candidates = list(self._dict.get(code, []))

    def select_candidate(self, index):
        """
        直接選擇指定索引的候選字 (用於滑鼠點擊)
        index: 在當前頁中的索引 (0-based)
        """
        page_cands = self.page_candidates
        if 0 <= index < len(page_cands):
            char = page_cands[index]
            self.reset()
            return char
        return None

    def get_status_text(self):
        """取得狀態列文字"""
        if self._active:
            return '速成'
        return 'EN'
