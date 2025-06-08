import tkinter as tk
import threading
from tkinter import messagebox, scrolledtext
from main import ask_type, ask_gomoku_type, run_once_and_return_json,normalize_text
from ai_gomoku import GomokuAI
import math

CELL_SIZE = 40
RADIUS = 15

FURNITURE_COLOR = {
    "椅子": "brown",
    "電腦桌": "sienna",
    "餐桌": "orange",
    "沙發": "olive drab",
    "電腦": "gray",
    "花瓶": "pink",
    "床": "lightblue",
    "立燈": "gold"
}

FURNITURE_SIZE = {
    "椅子": (40, 40),
    "電腦桌": (100, 60),
    "餐桌": (120, 70),
    "沙發": (120, 60),
    "電腦": (40, 30),
    "花瓶": (20, 20),
    "床": (140, 80),
    "立燈": (20, 60)
}

POSITION_MAP = {
    "右上角": (500, 50),
    "右下角": (500, 300),
    "左上角": (50, 50),
    "左下角": (50, 300),
    "中間": (300, 200)
}
class GomokuGame:
    def __init__(self, root, ai_enabled):
        self.root = root
        self.canvas = tk.Canvas(root, width=CELL_SIZE*17, height=CELL_SIZE*17, bg="burlywood")
        self.canvas.pack(side=tk.LEFT)

        self.move_textbox = scrolledtext.ScrolledText(root, width=30, height=25, font=("Arial", 12))
        self.move_textbox.pack(side=tk.RIGHT, fill=tk.Y)
        self.move_textbox.insert(tk.END, "🎙️ 等待語音指令...\n")

        self.ai_enabled = ai_enabled
        self.ai = GomokuAI()
        self.update_board()
        threading.Thread(target=self.auto_listen_loop, daemon=True).start()

    def update_board(self):
        self.canvas.delete("all")
        for i in range(15):
            x = CELL_SIZE + i * CELL_SIZE
            y = CELL_SIZE + i * CELL_SIZE
            self.canvas.create_line(CELL_SIZE, y, CELL_SIZE * 16, y)
            self.canvas.create_line(x, CELL_SIZE, x, CELL_SIZE * 16)
        for i in range(15):
            self.canvas.create_text(CELL_SIZE + i * CELL_SIZE, CELL_SIZE / 2, text=str(i+1), font=("Arial", 10))
            self.canvas.create_text(CELL_SIZE / 2, CELL_SIZE + i * CELL_SIZE, text=str(i+1), font=("Arial", 10))
        for (x, y), color in self.ai.state.items():
            cx = CELL_SIZE + x * CELL_SIZE
            cy = CELL_SIZE + y * CELL_SIZE
            fill = "black" if color == 1 else "white"
            self.canvas.create_oval(cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS, fill=fill, outline="black")
        self.update_move_textbox()

    def update_move_textbox(self):
        self.move_textbox.delete("1.0", tk.END)
        self.move_textbox.insert(tk.END, "🎙️ 棋盤落子紀錄：\n")
        for idx, (x, y) in enumerate(self.ai.history, start=1):
            color = "黑子" if self.ai.state.get((x, y)) == 1 else "白子"
            self.move_textbox.insert(tk.END, f"{idx}. {color} → {x+1}之{y+1}\n")

    def auto_listen_loop(self):
        while True:
            self.move_textbox.insert(tk.END, "⏺️ 錄音中...")
            self.move_textbox.see(tk.END)
            result = run_once_and_return_json()
            self.move_textbox.insert(tk.END, "✅ 錄音完成，處理結果中...")
            self.move_textbox.see(tk.END)
            if result is None or not isinstance(result, dict):
                continue
            if result.get("type") == "game_control":
                command = result["遊戲指令"]
                if command == "重新開始":
                    self.ai.reset()
                    self.update_board()
                    self.move_textbox.delete("1.0", tk.END)
                    messagebox.showinfo("系統訊息", "🌀 已重置棋盤")
                elif command == "悔棋":
                    if self.ai.undo_last_two_moves():
                        self.update_board()
                        self.move_textbox.insert(tk.END, "↩️ 悔棋成功\n")
                    else:
                        self.move_textbox.insert(tk.END, "⚠️ 悔棋失敗\n")
                elif command == "終止遊戲":
                    self.root.quit()
            elif "玩家棋子顏色" in result:
                if not self.ai.apply_json_move(result):
                    self.move_textbox.insert(tk.END, f"⚠️ 無效落子（重複）：{result['下的格子']}\n")
                    continue
                self.update_board()
                self.move_textbox.insert(tk.END, f"玩家下在：{result['下的格子']}\n")
                x_str, y_str = result["下的格子"].split("之")
                if self.ai.check_win(int(x_str), int(y_str)):
                    messagebox.showinfo("遊戲結束", "🎉 玩家獲勝！")
                    return
                if self.ai_enabled:
                    ai_move = self.ai.get_best_move()
                    self.ai.apply_json_move(ai_move)
                    self.update_board()
                    self.move_textbox.insert(tk.END, f"AI 下在：{ai_move['下的格子']}\n")
                    ax, ay = ai_move['下的格子'].split("之")
                    if self.ai.check_win(int(ax), int(ay)):
                        messagebox.showinfo("遊戲結束", "🤖 AI 獲勝！")
                        return

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
            text = normalize_text(result.get("指令原文", "")) if result else ""
            self.label.config(text=f"✅ 指令：{text}")
            if result and result.get("type") == "furniture_control":
                action = result.get("動作")
                obj = result.get("object1")
                direction = result.get("方向")
                distance = result.get("距離")
                angle = result.get("角度")
                text = normalize_text(result.get("指令原文", ""))
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

if __name__ == "__main__":
    mode = ask_type()
    root = tk.Tk()
    if mode == "gomoku":
        ai_flag = ask_gomoku_type()
        root.title("語音五子棋")
        GomokuGame(root, ai_flag)
    else:
        root.title("語音家具控制")
        FurnitureControl(root)
    root.mainloop()