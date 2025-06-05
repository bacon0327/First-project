
import pyaudio
import wave
import webrtcvad
import whisper
import json
import collections
import re
from bert_command_classifier import BertCommandClassifier
from ai_gomoku import GomokuAI
from datetime import time 

AUDIO_PATH = "record_temp.wav"
JSON_OUTPUT_PATH = "output_bert.json"

INIT_PROMPT = (
    "這是一個五子棋語音指令系統。"
    "玩家會說出像是「黑子下在三之三」、「白子放在五之七」這類語句。"
    "請確保關鍵詞如：黑子、白子、下、放、之、棋盤座標（三之三、五之七等）都能正確辨識。"
)

# === 初始化模型 ===
print("載入 Whisper 模型...")
whisper_model = whisper.load_model("medium")
print("✅ Whisper 載入完成。")
print("載入 BERT 分類器...")
bert_classifier = BertCommandClassifier("./0604/BERTv2") #改BERTv2
print("✅ BERT 分類器載入完成。")

# 中文數字轉換
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
    return f"{int(left_num)}-{int(right_num)}"

def normalize_text(text):
    text = (
        text.replace("黑紙", "黑子")
            .replace("白紙", "白子")
            .replace("黑紫", "黑子")
            .replace("白紫", "白子")
            .replace("黑棋", "黑子")
            .replace("白棋", "白子")
    )
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
        while True:
            frame = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            is_speech = vad.is_speech(frame, RATE)
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.8 * ring_buffer.maxlen:
                    triggered = True
                    voiced_frames.extend([f for f, s in ring_buffer])
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > 0.8 * ring_buffer.maxlen:
                    print("⏹️ 偵測到靜音，自動存檔")
                    wf = wave.open(out_path, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(voiced_frames))
                    wf.close()
                    break
    except KeyboardInterrupt:
        print("錄音手動結束。")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("錄音已結束。")

def run_once_and_return_json():
    record_and_segment(AUDIO_PATH)
    segments = whisper_model.transcribe(
        AUDIO_PATH, language="zh", task="transcribe",
        fp16=False, initial_prompt=INIT_PROMPT
    )["segments"]

    for seg in segments:
        normalized_text = normalize_text(seg['text'])
        label = bert_classifier.predict_label(normalized_text)

        if label == 1:
            info = bert_classifier.to_gomoku_json(normalized_text)
            return {"type": "gomoku", "data": info}

        elif label == 2:
            output = bert_classifier.to_game_control_json(normalized_text)
            return {"type": "game_control", "data": output}

        elif label == 0:
            return {"type": "non_command", "text": seg['text']}

    return {"type": "no_result"}

def main():
    print("=== Whisper + BERT 五子棋語音系統啟動 ===")
    ai = GomokuAI()

    # === 啟動時判定對戰模式 ===
    print("🎤 是否與 AI 對戰？請說『人機』或『雙人』")
    record_and_segment(AUDIO_PATH)
    segments = whisper_model.transcribe(AUDIO_PATH, language="zh")["segments"]
    text = normalize_text(segments[0]['text'])

    if "AI" in text or "人機" in text or "電腦" in text:
        ai_enabled = True
    else:
        ai_enabled = False
        print("⚠️ 預設為雙人對戰")

    print(f"模式選擇完成：{'與 AI 對戰' if ai_enabled else '雙人對戰'}")

    # === 主語音迴圈 ===
    try:
        while True:
            print("\n🎤 請說出指令...")
            record_and_segment(AUDIO_PATH)
            segments = whisper_model.transcribe(
                AUDIO_PATH, language="zh", task="transcribe",
                fp16=False, initial_prompt=INIT_PROMPT
            )["segments"]

            found = False

            for seg in segments:
                normalized_text = normalize_text(seg['text'])
                label = bert_classifier.predict_label(normalized_text)
                print(segments)
                print(label)

                if label == 1:
                    info = bert_classifier.to_gomoku_json(normalized_text)
                    if info:
                        ai.apply_json_move(info)
                        print(f"玩家落子：{info}")

                        if ai_enabled:
                            ai_move = ai.get_best_move()
                            ai.apply_json_move(ai_move)
                            print(f"AI 回應：{ai_move}")

                        found = True
                        break

                elif label == 2:
                    output = bert_classifier.to_game_control_json(normalized_text)
                    found = True 
                    if output:
                        print(f"接收到遊戲控制指令：{output['遊戲指令']}")
                        
                        if output["遊戲指令"] == "重新開始" and ai_enabled:
                            ai.reset()
                        
                        elif output["遊戲指令"] == "終止遊戲":
                            print("👋 感謝遊玩，再見！")
                            return
                        
                        if output["遊戲指令"] == "悔棋":
                            if ai_enabled:
                                success = ai.undo_last_two_moves()
                                if success:
                                    print("已悔棋（玩家與 AI 各一步）")
                                else:
                                    print("悔棋失敗：棋子少於兩顆")
                            else:
                                print("⚠️ 雙人對戰模式不由 Python 控制悔棋，請交由 C# 處理")
                        
                        with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
                            json.dump(output, f, ensure_ascii=False, indent=2)

                    else:
                        print("無法判斷的遊戲控制語句：", normalized_text)


                elif label == 0:
                    print(f"非指令語句：{seg['text']}")

            if not found:
                print("本段無有效指令，不輸出 JSON。")

    except KeyboardInterrupt:
        print("使用者中止，程式結束")

if __name__ == "__main__":
    main()
