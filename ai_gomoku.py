import json

BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

PATTERN_SCORES = {
    (5, 0): 100000,
    (5, 1): 100000,  # 死五（仍視為勝利狀態）
    (4, 0): 20000,
    (4, 1): 3000,
    (3, 0): 2000,
    (3, 1): 100,
    (2, 0): 50,
    (2, 1): 10,
}

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1), (-1, 1) ,(-1, -1)]

def get_neighboring_moves(state):
    candidates = set()
    for (x, y) in state:
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = x + dx, y + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if (nx, ny) not in state:
                        candidates.add((nx, ny))
    return candidates if candidates else {(BOARD_SIZE // 2, BOARD_SIZE // 2)}

def evaluate_point(state, x, y, color):
    score = 0
    for dx, dy in DIRECTIONS:
        count = 1
        blocks = 0

        for step in [1, -1]:
            i = 1
            while True:
                nx, ny = x + dx * i * step, y + dy * i * step
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if state.get((nx, ny)) == color:
                        count += 1
                    elif (nx, ny) not in state:
                        break
                    else:
                        blocks += 1
                        break
                else:
                    blocks += 1
                    break
                i += 1

        score += PATTERN_SCORES.get((count, blocks), 0)
    return score

def evaluate_board(state):
    score = 0
    for (x, y), c in state.items():
        score += evaluate_point(state, x, y, WHITE)
        score += evaluate_point(state, x, y, BLACK) * 1.2
    return score

def minimax(state, depth, is_ai_turn):
    if depth == 0:
        return evaluate_board(state), None

    best_score = float('-inf') if is_ai_turn else float('inf')
    best_move = None

    for x, y in get_neighboring_moves(state):
        state_copy = state.copy()
        state_copy[(x, y)] = WHITE if is_ai_turn else BLACK
        score, _ = minimax(state_copy, depth - 1, not is_ai_turn)

        if is_ai_turn and score > best_score:
            best_score = score
            best_move = (x, y)
        elif not is_ai_turn and score < best_score:
            best_score = score
            best_move = (x, y)

    return best_score, best_move

class GomokuAI:
    def __init__(self):
        self.state = {}      # {(x, y): color}
        self.history = []    # 儲存落子順序 [(x, y)]

    def apply_json_move(self, move_json):
        color = WHITE if move_json["玩家棋子顏色"] == "白子" else BLACK
        x_str, y_str = move_json["下的格子"].split("之")
        x, y = int(x_str) - 1, int(y_str) - 1

        if (x, y) in self.state:
            print(f"⚠️ 無效落子：位置 ({x+1}之{y+1}) 已有 {'白子' if self.state[(x, y)] == WHITE else '黑子'}")
            return False
    
        self.state[(x, y)] = color
        self.history.append((x, y))
        return True    

    def get_best_move(self):
        _, move = minimax(self.state, depth=2, is_ai_turn=True)
        if move is None:
            move = (BOARD_SIZE // 2, BOARD_SIZE // 2)
        return {
            "玩家棋子顏色": "白子",
            "下的格子": f"{move[0]+1}之{move[1]+1}"
        }

    def undo_last_move(self):
        if self.history:
            last_move = self.history.pop()
            removed = self.state.pop(last_move, None)
            print(f"↩️ 悔棋成功，移除位置：{last_move} 棋子：{'白子' if removed == WHITE else '黑子'}")
        else:
            print("⚠️ 無法悔棋：無任何落子紀錄")
    
    def reset(self):
        self.state.clear()
        self.history.clear()
        print("♻️ GomokuAI 狀態已重設")

    def print_board(self):
        symbol = {EMPTY: '.', BLACK: 'X', WHITE: 'O'}
        print("    " + " ".join(f"{i+1:2}" for i in range(BOARD_SIZE)))
        for i in range(BOARD_SIZE):
            row = []
            for j in range(BOARD_SIZE):
                c = self.state.get((i, j), EMPTY)
                row.append(symbol[c])
            print(f"{i+1:2} | " + "  ".join(row))
            
    def undo_last_two_moves(self):
        if len(self.history) < 2:
            print("⚠️ 無法悔棋：落子紀錄少於兩步")
            return False

        for _ in range(2):
            last_move = self.history.pop()
            removed = self.state.pop(last_move, None)
            x, y = last_move
            print(f"↩️ 悔棋成功，移除位置：({x+1}之{y+1}) 棋子：{'白子' if removed == WHITE else '黑子'}")

        return True

