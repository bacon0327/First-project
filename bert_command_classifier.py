from transformers import BertTokenizer, BertForSequenceClassification
import torch
import re

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
        quit_keywords = ["不玩", "退出", "結束", "關掉"]
        regret_keywords = ["悔棋", "倒退", "反悔", "上一步" ,"回棋"]

        if any(kw in text for kw in restart_keywords):
            return {"type": "game_control", "遊戲指令": "重新開始"}
        elif any(kw in text for kw in quit_keywords):
            return {"type": "game_control", "遊戲指令": "終止遊戲"}
        elif any(kw in text for kw in regret_keywords):
            return {"type": "game_control", "遊戲指令": "悔棋"}
        return None

    def to_furniture_control_json(self, text):
        furniture_list = ["椅子", "電腦桌", "電腦椅", "電腦", "餐桌", "沙發", "花瓶", "床", "立燈"]
        action_keywords = {
            "放置": ["放", "擺"],
            "移除": ["拿掉", "移除", "去掉", "丟掉"],
            "移動": ["移", "挪", "靠", "搬"],
            "轉向": ["轉", "轉向", "旋轉"]
        }
        direction_keywords = ["左", "右", "前", "後", "上", "下", "中間", "旁邊"]
        distance_keywords = ["一點點", "稍微", "一點", "多一點", "很多"]
        angle_keywords = ["90度", "180度", "45度", "270度"]

        action = None
        for key, variants in action_keywords.items():
            if any(k in text for k in variants):
                action = key
                break
        if not action:
            return None

        object1 = None
        for obj in furniture_list:
            if obj in text:
                object1 = obj
                break
        if not object1:
            return None

        object2 = None
        for obj in furniture_list:
            if obj != object1 and obj in text:
                object2 = obj
                break

        direction = next((d for d in direction_keywords if d in text), None)
        distance = next((d for d in distance_keywords if d in text), None)
        angle = next((a for a in angle_keywords if a in text), None)

        result = {
            "type": "furniture_control",
            "object1": object1,
            "object2": object2,
            "動作": action
        }
        if direction:
            result["方向"] = direction
        if distance:
            result["距離"] = distance
        if angle:
            result["角度"] = angle
        position_hints = ["左上角", "左下角", "右上角", "右下角", "中間"]
        position = next((p for p in position_hints if p in text), None)
        if position:
            result["位置"] = position
        return result