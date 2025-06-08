# First-project

本專案為語音控制與 BERT 指令分類整合應用，支援語音下棋與簡易家具語句辨識。

---

## 📁 專案結構

- `main.py`：主流程整合 Whisper 與 BERT
- `tkinter_v4.py`：結合五子棋與家具控制的圖形化介面
- `gomoku_gui.py`：改進版的五子棋圖形化介面
- `bert_command_classifier.py`：BERT 指令分類模組
- `ai_gomoku.py`：AI 對弈邏輯


---


## 📦 模型下載

請先下載 BERT 模型檔案，並放置於 best_model 資料夾中。
👉 [模型下載連結](https://drive.google.com/drive/folders/1vjtY7rQvzkeaqsiSn2SpGMTRLXsk1ymH)


---


## 🔧 安裝環境建議

建議使用 Conda 建立虛擬環境，Python 版本建議為 3.10。

```bash
pip install -r requirements.txt

