from bert_command_classifier import BertCommandClassifier
from ai_gomoku import GomokuAI
import collections
import json
import numpy as np
import pyaudio
import re
import sys
import time
import wave
import webrtcvad
import whisper

AUDIO_PATH = "record_temp.wav"
lab2_OUTPUT_PATH = "D:/Program Files/code/GomokuGame/Assets/StreamingAssets/step.json"
lab3_OUTPUT_PATH = "D:/Program Files/code/GomokuGame/Assets/StreamingAssets/furniture_command.json"
TYPE_OUTPUT_PATH = "D:/Program Files/code/GomokuGame/Assets/StreamingAssets/change.json"
last_label = None  # 放在 main.py 最上方做為全域變數

print("載入 Whisper 模型...")
whisper_model = whisper.load_model("large-v3", device="cuda")
print("✅ Whisper 載入完成。")
print("載入 BERT 分類器...")
bert_classifier = BertCommandClassifier("best_model")
print("✅ BERT 分類器載入完成。")

gomoku_ai = GomokuAI()
ai_enabled = True

zh_to_arabic = {
    '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
    '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
    '十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15'
}
sorted_zh = sorted(zh_to_arabic.keys(), key=lambda x: -len(x))
zh_number_pattern = '|'.join(sorted_zh)
arabic_pattern = r'\d{1,2}'
mixed_pattern = re.compile(rf'({zh_number_pattern}|{arabic_pattern}|山)之({zh_number_pattern}|{arabic_pattern}|山)')

def normalize_coordinate(match):
    left = match.group(1).replace("山", "三")
    right = match.group(2).replace("山", "三")
    left_num = zh_to_arabic.get(left, left)
    right_num = zh_to_arabic.get(right, right)
    return f"{int(left_num)}之{int(right_num)}"

def normalize_text(text):
    text = (
        text.replace("黑紙", "黑子")
            .replace("白紙", "白子")
            .replace("黑紫", "黑子")
            .replace("白紫", "白子")
            .replace("黑棋", "黑子")
            .replace("白棋", "白子")
    )

    # 同音誤字修正
    for wrong in ["傢俱", "加劇", "傢具", "家俱"]:
        text = text.replace(wrong, "家具")

    # 方位誤字修正
    direction_aliases = {
        "桌上角": "左上角",
        "桌下角": "左下角",
        "右上方": "右上角",
        "右下方": "右下角",
        "左上方": "左上角",
        "左下方": "左下角",
        "入下角": "右下角",
        "由下角": "右下角",
        "中監": "中間",
        "中鍵": "中間"
    }
    for wrong, correct in direction_aliases.items():
        text = text.replace(wrong, correct)

    text = mixed_pattern.sub(normalize_coordinate, text)
    return text

def record_and_segment(out_path=AUDIO_PATH):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK_DURATION_MS = 30
    PADDING_DURATION_MS = 1500
    CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
    NUM_PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
    vad = webrtcvad.Vad(2)

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
    print(" 開始錄音，請說話...（Ctrl+C結束）")

    try:
        ring_buffer = collections.deque(maxlen=NUM_PADDING_CHUNKS)
        triggered = False
        voiced_frames = []
        dots = 0
        frame_count = 0
        start_time = None
        
        while True:
            frame = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            is_speech = vad.is_speech(frame, RATE)
            
            if triggered:
                frame_count += 1
                if frame_count >= 3:
                    sys.stdout.write('\r錄音中' + '.' * (dots % 4) + '   ')
                    sys.stdout.flush()
                    dots += 1
                    frame_count = 0
            
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.5 * ring_buffer.maxlen:
                    triggered = True
                    start_time = time.time()
                    voiced_frames.extend([f for f, s in ring_buffer])
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > 0.8 * ring_buffer.maxlen and (time.time() - start_time) > 1.0:
                    print("\n偵測到靜音，自動存檔")
                    wf = wave.open(out_path, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(voiced_frames))
                    wf.close()
                    break
    except KeyboardInterrupt:
        print("\n錄音手動結束。")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("錄音已結束。")

def ask_type():
    print("請說明你要執行的操作（例如：我要控制家具、我要下五子棋）...")

    with open(TYPE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"type":""}, f, ensure_ascii=False, indent=2)

    record_and_segment(AUDIO_PATH)
    result = whisper_model.transcribe(AUDIO_PATH, language="zh")
    text = normalize_text(result["text"].strip())
    print(f"辨識結果：{text}")
    if "家具" in text:
        print("進入家具控制模式")
        mode = "furniture"
    else:
        print("進入五子棋模式（預設）")
        mode = "gomoku"

    with open(TYPE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"type": mode}, f, ensure_ascii=False, indent=2)
    return mode

def ask_gomoku_type():
    print("請問是雙人對戰還是人機對戰？")
    record_and_segment(AUDIO_PATH)
    result = whisper_model.transcribe(AUDIO_PATH, language="zh")
    text = normalize_text(result["text"].strip())
    print(f"辨識結果：{text}")
    if "雙人" in text or "兩人" in text:
        print("模式：雙人對戰")
        return False
    print("未偵測到有效輸出，預設為人機對戰")
    return True

def confirm_switch_mode():
    print("請問您要切換模式嗎？（是/否）")
    record_and_segment(AUDIO_PATH)
    result = whisper_model.transcribe(AUDIO_PATH, language="zh")
    text = result["text"].strip()
    print(f"辨識結果：{text}")
    if "是" in text or "是的" in text or "好" in text:
        return True
    return False

def run_once_and_return_json():

    global last_label
    global last_recognized_text # 使用全域變數

    record_and_segment(AUDIO_PATH)
    result = whisper_model.transcribe(
        AUDIO_PATH,
        language="zh",
        initial_prompt= (
            "這是一個語音指令系統，包含家具控制與五子棋。"
            "玩家會說出像是「黑子下在三之三」、「白子放在五之七」這類語句。"
            "請確保關鍵詞如：黑子、白子、下、放、之、棋盤座標（三之三、五之七等）都能正確辨識。"
            "關鍵詞還有：悔棋、回上一步、結束遊戲、重開遊戲"
        )
    )
    text = normalize_text(result["text"].strip())
    last_recognized_text = text # 將原始文本儲存到全域變數
    print(f"辨識結果：{text}")
    label = bert_classifier.predict_label(text)
    last_label = label
    print(f"指令類型:label = {label}")

    if label == 0:
        print("非指令語句：", text)
        return None
    elif label == 1:
        return bert_classifier.to_gomoku_json(text)
    elif label == 2:
        return bert_classifier.to_game_control_json(text)
    elif label == 3:
        return bert_classifier.to_furniture_control_json(text)

    return None

def main():

    global ai_enabled
    global last_label # 確保在 main 中可以讀取到 last_label
    global last_recognized_text # 確保在 main 中可以讀取到 last_recognized_text
    
    switch_keywords = ["切換", "切换"]

    print("=== Whisper + BERT 指令辨識系統啟動 ===")

    mode = ask_type()

    if mode == "furniture":
        print("家具控制模式已啟動。")
    else:
        ai_enabled = ask_gomoku_type()
        print(f"模式選擇完成：{'與 AI 對戰' if ai_enabled else '雙人對戰'}")

    try:
        while True:
            print("\n🎤 請說出語音指令...")
            result = run_once_and_return_json()

            if last_label == 0 and any(keyword in last_recognized_text for keyword in switch_keywords):
                if confirm_switch_mode():
                    if mode == "furniture":
                        mode = "gomoku"
                        print("模式已切換為五子棋。")
                        ai_enabled = ask_gomoku_type()
                        print(f"模式選擇完成：{'與 AI 對戰' if ai_enabled else '雙人對戰'}")
                    else:
                        mode = "furniture"
                        print("模式已切換為家具控制。")
                    
                    # 通知 C# 端切換模式
                    with open(TYPE_OUTPUT_PATH, "w", encoding="utf-8") as f:
                        json.dump({"type": mode}, f, ensure_ascii=False, indent=2)
                    continue # 切換模式後，重新開始循環，避免處理當前指令
                else:
                    print("已取消模式切換。")
                    continue # 重新開始循環，等待下一個指令
            
            if result is not None:
                # 檢查是否跨模式指令（需要切換）
                if mode == "gomoku" and last_label == 3:
                    print("⚠️ 偵測到家具指令，當前為五子棋模式")
                    if confirm_switch_mode():
                        mode = "furniture"
                        print("模式已切換為家具控制")
                        with open(TYPE_OUTPUT_PATH, "w", encoding="utf-8") as f:
                            json.dump({"type": mode}, f, ensure_ascii=False, indent=2)
                    else:
                        print("使用者取消切換，忽略此次指令")
                    continue  # 跳過此次 result 處理

                elif mode == "furniture" and last_label == 1:
                    print("⚠️ 偵測到五子棋指令，當前為家具模式")
                    if confirm_switch_mode():
                        mode = "gomoku"
                        print("模式已切換為五子棋")
                        ai_enabled = ask_gomoku_type()
                        with open(TYPE_OUTPUT_PATH, "w", encoding="utf-8") as f:
                            json.dump({"type": mode}, f, ensure_ascii=False, indent=2)
                    else:
                        print("使用者取消切換，忽略此次指令")
                    continue

                if mode == "gomoku":
                    with open(lab2_OUTPUT_PATH, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print("指令已寫入 JSON：", result)

                    if ai_enabled and last_label == 1:
                        ai_move = gomoku_ai.get_best_move()
                        gomoku_ai.apply_json_move(ai_move)
                        time.sleep(1)
                        with open(lab2_OUTPUT_PATH, "w", encoding="utf-8") as f:
                            json.dump(ai_move, f, ensure_ascii=False, indent=2)
                        print("AI 已下棋並更新 JSON：", ai_move)

                elif mode == "furniture":
                    with open(lab3_OUTPUT_PATH, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print("指令已寫入 JSON：", result)

    except KeyboardInterrupt:
        print("使用者中止，程式結束")

if __name__ == "__main__":
    main()