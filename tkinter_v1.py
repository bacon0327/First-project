import tkinter as tk
import main # 語音辨識與指令解析模組
from ai_gomoku import GomokuAI  # 包含 AI 演算法與棋盤邏輯
import threading
import time
from tkinter import messagebox, scrolledtext
from main import whisper_model, record_and_segment, normalize_text  # 引入必要方法
AUDIO_PATH = "record_temp.wav"
ai_enabled = True  # 預設為 True（避免未定義）


# 四個方向：橫、直、兩個斜線，用於判斷勝利條件
DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1), (-1, 1) ,(-1, -1)]

# 建立 AI 對弈物件
ai = GomokuAI()

# 判斷某一落子是否形成五連線
def check_win(state, last_move, color):
    x, y = last_move
    for dx, dy in DIRECTIONS:
        count = 1
        for step in [1, -1]:
            i = 1
            while True:
                nx, ny = x + dx * i * step, y + dy * i * step
                if (nx, ny) in state and state[(nx, ny)] == color:
                    count += 1
                    i += 1
                else:
                    break
        if count >= 5:
            return True
    return False

# 語音監聽主邏輯（會一直跑）
def auto_listen_loop():
    while True:
        result = main.run_once_and_return_json()

        if result is None:
            print("❌ 語音辨識失敗，result 為 None，跳過")
            continue

        # 🔎 防止非 dict 結構造成錯誤
        if not isinstance(result, dict):
            print("⚠️ 不合法的結果格式：", result)
            continue

        if result:
            # 🔎 先檢查是否有外層 type/data 結構
            if "type" in result and "data" in result:
                result = result["data"]

            # 🟩 處理遊戲指令（如 重新開始、悔棋、終止遊戲）
            if "遊戲指令" in result:
                command = result["遊戲指令"]
                if command == "重新開始":
                    ai.reset()
                    update_board()
                    move_textbox.delete("1.0", tk.END)
                    messagebox.showinfo("系統訊息", "🌀 已重置棋盤")
                elif command == "悔棋":
                    success = ai.undo_last_two_moves()
                    if success:
                        update_board()
                        move_textbox.insert(tk.END, "↩️ 悔棋成功，已回退上一步\n")
                    else:
                        move_textbox.insert(tk.END, "⚠️ 悔棋失敗：棋子少於兩顆\n")
                elif command == "終止遊戲":
                    root.quit()
                else:
                    print("⚠️ 未知的遊戲控制指令")
                continue  # 控制指令處理完後，進入下一輪

            # 🟩 處理玩家下棋指令
            elif "玩家棋子顏色" in result:
                # 玩家落子
                success = ai.apply_json_move(result)
                if not success:
                    move_textbox.insert(tk.END, f"⚠️ 無效落子（重複）：{result['下的格子']}\n")
                    continue  # ⚠️ 不要讓 AI 接著下棋，直接跳下一輪語音

                update_board()
                player_move = result["下的格子"]
                move_textbox.insert(tk.END, f"玩家下在：{player_move}\n")
                x_str, y_str = player_move.split("之")
                x, y = int(x_str) - 1, int(y_str) - 1
                if check_win(ai.state, (x, y), 1):
                    root.after(0, lambda: messagebox.showinfo("遊戲結束", "🎉 玩家獲勝！"))
                    return  # 結束遊戲

                time.sleep(0.5)  # 稍作延遲

                # AI 回應落子（只在 AI 模式下）
                if ai_enabled:
                    ai_move = ai.get_best_move()
                    if not ai_move:
                        move_textbox.insert(tk.END, "🤖 AI 無法落子，平手！\n")
                        return
                    ai.apply_json_move(ai_move)
                    update_board()
                    ai_x_str, ai_y_str = ai_move["下的格子"].split("之")
                    move_textbox.insert(tk.END, f"AI 下在：{ai_move['下的格子']}\n")
                    ai_x, ai_y = int(ai_x_str) - 1, int(ai_y_str) - 1
                    if check_win(ai.state, (ai_x, ai_y), 2):
                        root.after(0, lambda: messagebox.showinfo("遊戲結束", "🤖 AI 獲勝！"))
                        return  # 結束遊戲
                # 🟩 不明格式
                else:
                    print("⚠️ 不明的語音指令格式，略過：", result)
        else:
            print("❌ 無效語音，跳過")


def update_move_textbox():
    move_textbox.delete("1.0", tk.END)
    move_textbox.insert(tk.END, "🎙️ 棋盤落子紀錄：\n")
    for idx, (x, y) in enumerate(ai.history, start=1):
        color = "黑子" if ai.state.get((x, y)) == 1 else "白子"
        move_textbox.insert(tk.END, f"{idx}. {color} → {x+1}之{y+1}\n")


# 更新棋盤畫面
def update_board():
    canvas.delete("all")  # 清除畫面

    # 畫棋盤線
    for i in range(15):
        x = CELL_SIZE + i * CELL_SIZE
        y = CELL_SIZE + i * CELL_SIZE
        canvas.create_line(CELL_SIZE, y, CELL_SIZE * 16, y)  # 水平線
        canvas.create_line(x, CELL_SIZE, x, CELL_SIZE * 16)  # 垂直線

    # 畫座標數字（上方與左側）
    for i in range(15):
        canvas.create_text(CELL_SIZE + i * CELL_SIZE, CELL_SIZE / 2, text=str(i+1), font=("Arial", 10))
        canvas.create_text(CELL_SIZE / 2, CELL_SIZE + i * CELL_SIZE, text=str(i+1), font=("Arial", 10))

    # 畫棋子
    for (x, y), color in ai.state.items():
        cx = CELL_SIZE + x * CELL_SIZE
        cy = CELL_SIZE + y * CELL_SIZE
        fill = "black" if color == 1 else "white"
        canvas.create_oval(cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS, fill=fill, outline="black")
    # ➜ 同步更新右邊的落子紀錄 Textbox
    update_move_textbox()
# === 啟動時語音選擇對戰模式 ===
print("是否與 AI 對戰？請說『人機』或『雙人』")
record_and_segment(AUDIO_PATH)
segments_generator, _ = whisper_model.transcribe(AUDIO_PATH, language="zh")
segments = list(segments_generator)
if segments:
    text = normalize_text(segments[0].text)
else:
    print("⚠️ 未偵測到語音內容")
    text = ""

if "雙人" in text or "兩人" in text :
    print("🧪 Whisper 辨識段落：", segments)
    ai_enabled = False
    print("✅ 模式選擇完成：雙人對戰")
else:
    ai_enabled = True
    print("🧪 Whisper 辨識段落：", segments)
    print("✅ 模式選擇完成：與 AI 對戰")

# === Tkinter 主介面設置 ===
root = tk.Tk()
root.title("語音五子棋 (自動偵測)")

# 棋盤設定
CELL_SIZE = 40
RADIUS = 15
canvas = tk.Canvas(root, width=CELL_SIZE*17, height=CELL_SIZE*17, bg="burlywood")
canvas.pack(side=tk.LEFT)

# 文字框記錄落子資訊
move_textbox = scrolledtext.ScrolledText(root, width=30, height=25, font=("Arial", 12))
move_textbox.pack(side=tk.RIGHT, fill=tk.Y)
move_textbox.insert(tk.END, "🎙️ 等待語音指令...\n")

update_board()  # 初始畫面

# 使用背景執行緒執行語音偵測（不會卡住 UI）
threading.Thread(target=auto_listen_loop, daemon=True).start()

root.mainloop()  # 啟動 GUI 事件迴圈