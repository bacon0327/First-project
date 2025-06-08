import tkinter as tk
import threading
import math
from tkinter import messagebox, scrolledtext
from main import ask_type, ask_gomoku_type, run_once_and_return_json, normalize_text
from ai_gomoku import GomokuAI
from gomoku_gui import GomokuGame

# 定義家具位置、顏色、尺寸
FURNITURE_COLOR = {
    "椅子": "brown", "電腦桌": "sienna", "餐桌": "orange",
    "沙發": "olive drab", "電腦": "gray", "花瓶": "pink",
    "床": "lightblue", "立燈": "gold"
}
FURNITURE_SIZE = {
    "椅子": (40, 40), "電腦桌": (100, 60), "餐桌": (120, 70),
    "沙發": (120, 60), "電腦": (40, 30), "花瓶": (20, 20),
    "床": (140, 80), "立燈": (20, 60)
}
POSITION_MAP = {
    "右上角": (500, 50), "右下角": (500, 300),
    "左上角": (50, 50), "左下角": (50, 300),
    "中間": (300, 200)
}

def gui_ask_type(root):
    # === 使用 Frame 來包裝 Label，增加美化與中央化效果 ===
    frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20, bd=0, highlightthickness=0)
    frame.pack(pady=10, padx=10, fill="both", expand=True)

    # Label 文字樣式設計
    label = tk.Label(frame, text="請說明你要執行的操作（例如：我要控制家具、我要下五子棋）",
                      font=("Arial", 18, "bold"), bg="#f0f0f0", fg="#333")
    label.pack(pady=10)

    # 模擬「請稍候...」的動態提示效果
    tip_label = tk.Label(frame, text="🎤 等待語音輸入中...", font=("Arial", 14), bg="#f0f0f0", fg="#666")
    tip_label.pack(pady=5)

    root.update()

    # 進行語音指令辨識
    mode = ask_type()

    # 更新 Label，顯示辨識結果
    if mode == "gomoku":
        label.config(text="已選擇模式：五子棋", fg="#000000", font=("Arial", 14, "bold"))

    tip_label.config(text="")

    # 1.5 秒後自動移除整個 Frame
    if mode == "gomoku":
        root.after(1500, frame.destroy)
    else:
        root.after(0, frame.destroy)
    return mode

def gui_ask_gomoku_type(root):
    # 顯示「請問是雙人對戰還是人機對戰？」
    label = tk.Label(root, text="請問是雙人對戰還是人機對戰？", font=("Arial", 16))
    label.pack(pady=5, padx=5, fill=None, expand=False)
    root.update()
    ai_flag = ask_gomoku_type()
    # label.config(text=f"模式：{'雙人對戰' if not ai_flag else '人機對戰'}")
    # root.update()
    root.after(0, label.destroy)
    return ai_flag

class FurnitureControl:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=600, height=400, bg="lightgrey")
        self.canvas.pack()

        self.furniture = {}
        self.label = tk.Label(root, text="家具控制模式：等待語音指令...", font=("Arial", 14))
        self.label.pack()

        self.rotation_angles = {}  # 每件家具的旋轉角度（degrees）
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def listen_loop(self):
        while True:
            self.label.config(text="⏺️ 錄音中...")
            result = run_once_and_return_json()
            print(result)
            text = normalize_text(result.get("指令原文") or result.get("遊戲指令") or "") if result else ""
            self.label.config(text=f"✅ 指令：{text}")


            # 💡 檢查是否有「結束遊戲」關鍵字
            if "終止遊戲" in text:
                self.label.config(text="🔚 已結束遊戲，返回主選單")
                self.root.after(1000, lambda: restart_game(self.root))
                break  # 停止迴圈
            elif result and result.get("type") == "furniture_control":
                # 家具指令處理區
                action = result.get("動作")
                obj = result.get("object1")
                direction = result.get("方向")
                distance = result.get("距離")
                angle = result.get("角度")
                position_hint = next((pos for pos in POSITION_MAP if pos in text), None)

                if action == "移動" and obj in self.furniture:
                    dx = 10 if distance in ["一點", "一點點", "一些"] else 20
                    dy = 0
                    if direction in ["右"]:
                        dy = 0
                    elif direction in ["左"]:
                        dx = -dx
                    elif direction in ["上"]:
                        dx, dy = 0, -dx
                    elif direction in ["下"]:
                        dx, dy = 0, dx
                    self.canvas.move(obj, dx, dy)
                    self.label.config(text=f"移動 {obj} 向 {direction} {distance or ''}")
                elif action == "移除" and obj in self.furniture:
                    self.canvas.delete(self.furniture[obj])
                    del self.furniture[obj]
                    self.label.config(text=f"已移除 {obj}")
                elif action == "放置" and obj not in self.furniture:
                    x, y = POSITION_MAP.get(position_hint, (300, 200))
                    w, h = FURNITURE_SIZE.get(obj, (60, 40))
                    rect = self.canvas.create_rectangle(x, y, x + w, y + h, fill=FURNITURE_COLOR.get(obj, "skyblue"), tags=obj)
                    self.furniture[obj] = rect
                    self.rotation_angles[obj] = 0
                    self.label.config(text=f"已放置 {obj} 到 {position_hint or '預設位置'}")
                elif action == "轉向" and obj in self.furniture:
                    angle_val = int(angle.replace("度", "")) if angle else 90
                    self.rotation_angles[obj] = (self.rotation_angles[obj] + angle_val) % 360
                    x1, y1, x2, y2 = self.canvas.coords(self.furniture[obj])
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    w, h = FURNITURE_SIZE.get(obj, (60, 40))
                    rad = math.radians(self.rotation_angles[obj])
                    cos_a, sin_a = math.cos(rad), math.sin(rad)
                    new_x1 = cx - (w * cos_a - h * sin_a) / 2
                    new_y1 = cy - (w * sin_a + h * cos_a) / 2
                    new_x2 = cx + (w * cos_a - h * sin_a) / 2
                    new_y2 = cy + (w * sin_a + h * cos_a) / 2
                    self.canvas.coords(self.furniture[obj], new_x1, new_y1, new_x2, new_y2)
                    self.label.config(text=f"旋轉 {obj} {angle_val} 度")
                else:
                    self.label.config(text=f"⚠️ 未支援的家具動作或物件不存在")
            elif result:
                self.label.config(text="⚠️ 非家具指令，請重試")


def restart_game(old_root=None):
    if old_root:
        old_root.destroy()
    root = tk.Tk()
    root.title("語音系統")
    mode = gui_ask_type(root)
    if mode == "gomoku":
        ai_flag = gui_ask_gomoku_type(root)
        root.title("語音五子棋")
        GomokuGame(root, ai_flag)
    else:
        root.title("語音家具控制")
        FurnitureControl(root)
    root.mainloop()

if __name__ == "__main__":
    restart_game()