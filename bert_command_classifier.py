
from transformers import BertTokenizer, BertForSequenceClassification
import torch

class BertCommandClassifier:
    def __init__(self, model_dir="best_model"):
        self.tokenizer = BertTokenizer.from_pretrained(model_dir)
        self.model = BertForSequenceClassification.from_pretrained(model_dir)
        self.model.eval()

    def predict_label(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            predicted_class_id = logits.argmax(dim=-1).item()
        return predicted_class_id

    def to_gomoku_json(self, text):
        # 假設格式為：「白子放在五之七」或「黑子下在三之三」
        import re
        color = "白子" if "白" in text else "黑子"
        match = re.search(r"(\d{1,2})[之-](\d{1,2})", text)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            return {
                "玩家棋子顏色": color,
                "下的格子": f"{x}之{y}"
            }
        else:
            return None
        
    def to_game_control_json(self, text):
        text = text.lower()

        restart_keywords = ["再來", "再一局", "重新開始", "再玩一次"]
        quit_keywords = ["不玩", "退出", "結束", "關掉","終止遊戲"]
        regret_keywords = ["悔棋", "回上一步", "倒退", "反悔", "上一步"]

        if any(kw in text for kw in restart_keywords):
            return {
                "type": "game_control",
                "遊戲指令": "重新開始"
            }

        elif any(kw in text for kw in quit_keywords):
            return {
                "type": "game_control",
                "遊戲指令": "終止遊戲"
            }

        elif any(kw in text for kw in regret_keywords):
            return {
                "type": "game_control",
                "遊戲指令": "悔棋"
            }

        return None

