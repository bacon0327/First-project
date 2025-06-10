import tkinter as tk
import threading
from tkinter import messagebox, scrolledtext
from main import ask_type, ask_gomoku_type, run_once_and_return_json
from ai_gomoku import GomokuAI

CELL_SIZE = 50
RADIUS = 15

class GomokuGame:
    def __init__(self, root, ai_enabled):
        self.root = root
        self.ai_enabled = ai_enabled
        self.ai = GomokuAI()
        self.loading = False
        self.is_listening = False

        self.canvas = tk.Canvas(root, width=CELL_SIZE * 16, height=CELL_SIZE * 16, bg="burlywood")
        self.canvas.pack(side=tk.LEFT)

        self.move_textbox = scrolledtext.ScrolledText(root, width=30, height=25, font=("Arial", 12))
        self.move_textbox.pack(side=tk.RIGHT, fill=tk.Y)
        self.append_textbox("🎙️ 等待語音指令...")

        self.update_board()
        threading.Thread(target=self.auto_listen_loop, daemon=True).start()

    def append_textbox(self, message):
        self.move_textbox.insert(tk.END, message + "\n")
        self.move_textbox.see(tk.END)

    def update_board(self):
        self.canvas.delete("all")
        
        # ✅ 畫內部格線（從第 1 行開始，跳過最外層線）
        for i in range(1, 15):
            y = CELL_SIZE + i * CELL_SIZE
            x = CELL_SIZE + i * CELL_SIZE
            self.canvas.create_line(CELL_SIZE, y, CELL_SIZE * 15, y, fill="white")  # 水平線
            self.canvas.create_line(x, CELL_SIZE, x, CELL_SIZE * 15, fill="white")  # 垂直線

        # ✅ 畫棋盤坐標文字
        for i in range(15):
            self.canvas.create_text(CELL_SIZE + i * CELL_SIZE, CELL_SIZE / 2, text=str(i + 1), font=("Arial", 10), fill="white")
            self.canvas.create_text(CELL_SIZE / 2, CELL_SIZE + i * CELL_SIZE, text=str(i + 1), font=("Arial", 10), fill="white")
        
        # ✅ 畫外框，保留最外層線條
        self.canvas.create_rectangle(CELL_SIZE, CELL_SIZE, CELL_SIZE * 15, CELL_SIZE * 15, outline="white", width=2)
        
        # ✅ 畫棋子
        for (x, y), color in self.ai.state.items():
            if x >= 15 or y >= 15:
                continue
            cx, cy = CELL_SIZE + x * CELL_SIZE, CELL_SIZE + y * CELL_SIZE
            fill = "black" if color == 1 else "white"
            self.canvas.create_oval(cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS, fill=fill, outline="black")
        
        self.update_move_textbox()


    def update_move_textbox(self):
        self.move_textbox.delete("1.0", tk.END)
        self.append_textbox("🎙️ 棋盤落子紀錄：")
        for idx, (x, y) in enumerate(self.ai.history, start=1):
            color = "黑子" if self.ai.state.get((x, y)) == 1 else "白子"
            self.append_textbox(f"{idx}. {color} → {x + 1}之{y + 1}")

    def start_loading_animation(self, message="⏺️ 處理中"):
        self.loading = True
        self.append_textbox(message)
        def animate():
            dot_count = 0
            while self.loading and self.move_textbox.winfo_exists():
                dots = '.' * (dot_count % 4)
                try:
                    self.move_textbox.delete("end-2l", "end-1l")
                    self.move_textbox.insert(tk.END, f"{message}{dots}\n")
                    self.move_textbox.see(tk.END)
                except tk.TclError:
                    break
                dot_count += 1
                self.root.update_idletasks()
                self.root.after(500)
        threading.Thread(target=animate, daemon=True).start()


    def stop_loading_animation(self):
        self.loading = False

    def show_auto_close_message(self, title, message, duration=3000):
        win = tk.Toplevel(self.root)
        win.title(title)
        tk.Label(win, text=message, font=("Arial", 14)).pack(padx=20, pady=20)
        win.after(duration, win.destroy)

    def apply_and_check_win(self, move_json, is_ai=False):
        color = 1 if move_json["玩家棋子顏色"] == "黑子" else 2
        # ✅ 計算目前黑白子數
        black_count = list(self.ai.state.values()).count(1)
        white_count = list(self.ai.state.values()).count(2)

        # ✅ 先判斷第一步必須是黑子
        if not self.ai.state and color != 1:
            self.append_textbox("⚠️ 遊戲第一步必須是黑子下！")
            return False

        # ✅ 輪到誰下
        if black_count == white_count:
            # 輪到黑子
            if color != 1:
                self.append_textbox("⚠️ 輪到黑子下，請再試一次！")
                return False
        elif black_count > white_count:
            # 輪到白子
            if color != 2:
                self.append_textbox("⚠️ 輪到白子下，請再試一次！")
                return False
        else:
            self.append_textbox("⚠️ 棋盤出現異常，請重新開始！")
            return False
        
        if not self.ai.apply_json_move(move_json):
            self.append_textbox(f"⚠️ 無效落子（重複）：{move_json['下的格子']}")
            return False
        self.update_board()
        who = "AI" if is_ai else "玩家"
        self.append_textbox(f"{who} 下在：{move_json['下的格子']}")
        x_str, y_str = move_json["下的格子"].split("之")
        if self.ai.check_win(int(x_str), int(y_str)):
            self.show_auto_close_message("遊戲結束", f"🎉 {who} 獲勝！")
            self.root.after(3000, self.reset_board)
            return True
        return False

    def auto_listen_loop(self):
        if self.is_listening:
            return
        self.is_listening = True
        try:
            while True:
                self.start_loading_animation()
                try:
                    result = run_once_and_return_json()
                except Exception as e:
                    self.append_textbox(f"⚠️ 語音識別錯誤：{e}")
                    continue
                self.stop_loading_animation()

                if result is None or not isinstance(result, dict):
                    continue
                if result.get("type") == "game_control":
                    command = result["遊戲指令"]
                    if command == "重新開始":
                        self.append_textbox("🌀 已重置棋盤，3 秒後自動重開新局")
                        self.root.update()
                        self.root.after(3000, self.reset_board)
                        return
                    elif command == "悔棋":
                        if self.ai.undo_last_two_moves():
                            self.update_board()
                            self.append_textbox("↩️ 悔棋成功")
                        else:
                            self.append_textbox("⚠️ 悔棋失敗")
                    elif command == "終止遊戲":
                        self.append_textbox("⚠️ 結束遊戲，返回主選單...")
                        self.root.update()
                        # ✅ 延遲匯入以避免循環 import
                        from tkinter_v4 import restart_game
                        self.root.after(1000, lambda: restart_game(self.root))
                        return
                elif "玩家棋子顏色" in result:
                    if self.apply_and_check_win(result):
                        return
                    if self.ai_enabled:
                        ai_move = self.ai.get_best_move()
                        if self.apply_and_check_win(ai_move, is_ai=True):
                            return
        finally:
            self.is_listening = False

    def reset_board(self):
        self.ai.state.clear()
        self.ai.history.clear()
        self.update_board()
        self.move_textbox.delete("1.0", tk.END)
        self.append_textbox("🎙️ 已重置棋盤，準備進入新局...")
        self.root.update()
        threading.Thread(target=self.auto_listen_loop, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("🎮 Gomoku 語音對戰")
    game = GomokuGame(root, ai_enabled=True)  # 你可將 ai_enabled 設為 False 做雙人對戰
    root.mainloop()