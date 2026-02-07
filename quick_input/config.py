"""
速成輸入法 - 設定檔
Configuration for Quick Input Method
"""

# 倉頡字根對應表 (鍵盤字母 → 字根名稱)
CANGJIE_RADICALS = {
    'a': '日', 'b': '月', 'c': '金', 'd': '木', 'e': '水',
    'f': '火', 'g': '土', 'h': '竹', 'i': '戈', 'j': '十',
    'k': '大', 'l': '中', 'm': '一', 'n': '弓', 'o': '人',
    'p': '心', 'q': '手', 'r': '口', 's': '尸', 't': '廿',
    'u': '山', 'v': '女', 'w': '田', 'x': '難', 'y': '卜',
}

# 切換輸入法的快捷鍵
TOGGLE_KEY = 'ctrl+space'

# 選字視窗預設大小
CANDIDATE_WINDOW_WIDTH = 420
CANDIDATE_WINDOW_HEIGHT = 300
CANDIDATE_WINDOW_MIN_WIDTH = 250
CANDIDATE_WINDOW_MIN_HEIGHT = 150

# 每頁顯示的候選字數
CANDIDATES_PER_PAGE = 9

# 字體設定
CANDIDATE_FONT_FAMILY = "Microsoft JhengHei"
CANDIDATE_FONT_SIZE = 16
STATUS_FONT_SIZE = 10

# 顏色主題
THEME = {
    'bg': '#FFFFFF',
    'fg': '#333333',
    'highlight_bg': '#0078D4',
    'highlight_fg': '#FFFFFF',
    'input_bg': '#F0F0F0',
    'input_fg': '#000000',
    'border': '#CCCCCC',
    'status_bg': '#E8E8E8',
    'status_fg': '#666666',
    'number_fg': '#0078D4',
    'header_bg': '#0078D4',
    'header_fg': '#FFFFFF',
}
