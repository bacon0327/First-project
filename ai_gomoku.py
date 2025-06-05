import numpy as np

BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]

pattern_scores = {
    "11111": 1000000,
    "011110": 300000,
    "011112": 10000,
    "0011100": 8000,
    "01100": 1000,
    "11011": 1000,
}

def get_lines(board):
    lines = []
    for row in board:
        lines.append(row)
    for col in board.T:
        lines.append(col)
    for offset in range(-BOARD_SIZE + 5, BOARD_SIZE - 4):
        lines.append(np.diagonal(board, offset=offset))
    flipped = np.fliplr(board)
    for offset in range(-BOARD_SIZE + 5, BOARD_SIZE - 4):
        lines.append(np.diagonal(flipped, offset=offset))
    return lines

def evaluate_line(line, color):
    opponent = BLACK if color == WHITE else WHITE
    line_str = ''.join(str(1 if x == color else (2 if x == opponent else 0)) for x in line)
    score = 0
    for pattern, value in pattern_scores.items():
        score += line_str.count(pattern) * value
    return score

def evaluate_board(state, color):
    board = np.full((BOARD_SIZE, BOARD_SIZE), EMPTY)
    for (i, j), c in state.items():
        board[i][j] = c
    score_self = sum(evaluate_line(line, color) for line in get_lines(board))
    score_oppo = sum(evaluate_line(line, BLACK if color == WHITE else WHITE) for line in get_lines(board))
    return score_self - score_oppo

def check_win_fast(state, x, y):
    color = state.get((x, y))
    for dx, dy in DIRECTIONS:
        count = 1
        for dir in [1, -1]:
            nx, ny = x, y
            while True:
                nx += dx * dir
                ny += dy * dir
                if state.get((nx, ny)) == color:
                    count += 1
                else:
                    break
        if count >= 5:
            return True
    return False

def minimax(state, depth, alpha, beta, is_ai_turn):
    for (x, y), c in state.items():
        if check_win_fast(state, x, y):
            return (1000000 if c == WHITE else -1000000), None

    if depth == 0:
        return evaluate_board(state, WHITE), None

    best_move = None
    moves = get_neighboring_moves(state)

    if is_ai_turn:
        max_score = float('-inf')
        for x, y in moves:
            state_copy = state.copy()
            state_copy[(x, y)] = WHITE
            score, _ = minimax(state_copy, depth - 1, alpha, beta, False)
            if score > max_score:
                max_score = score
                best_move = (x, y)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score, best_move
    else:
        min_score = float('inf')
        for x, y in moves:
            state_copy = state.copy()
            state_copy[(x, y)] = BLACK
            score, _ = minimax(state_copy, depth - 1, alpha, beta, True)
            if score < min_score:
                min_score = score
                best_move = (x, y)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score, best_move

def get_neighboring_moves(state):
    candidates = set()
    for (x, y), _ in state.items():
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = x + dx, y + dy
                if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                    if (nx, ny) not in state:
                        candidates.add((nx, ny))
    return candidates if candidates else {(BOARD_SIZE // 2, BOARD_SIZE // 2)}

class GomokuAI:
    def __init__(self):
        self.state = {}
        self.current_turn = BLACK
        self.history = []

    def apply_move(self, x, y):
        x0, y0 = x - 1, y - 1
        self.state[(x0, y0)] = self.current_turn
        self.history.append((x0, y0))
        self.current_turn = WHITE if self.current_turn == BLACK else BLACK

    def ai_move(self):
        _, move = minimax(self.state, depth=2, alpha=float('-inf'), beta=float('inf'), is_ai_turn=True)
        if move:
            self.apply_move(move[0]+1, move[1]+1)
            return (move[0]+1, move[1]+1)
        return None

    def check_win(self, x, y):
        x0, y0 = x - 1, y - 1
        color = self.state.get((x0, y0))
        for dx, dy in DIRECTIONS:
            count = 1
            for dir in [1, -1]:
                nx, ny = x0, y0
                while True:
                    nx += dx * dir
                    ny += dy * dir
                    if (nx, ny) in self.state and self.state[(nx, ny)] == color:
                        count += 1
                    else:
                        break
            if count >= 5:
                return True
        return False

    def reset(self):
        self.state.clear()
        self.history.clear()
        self.current_turn = BLACK

    def undo_last_two_moves(self):
        if len(self.history) < 2:
            return False
        for _ in range(2):
            last = self.history.pop()
            self.state.pop(last, None)
        self.current_turn = BLACK
        return True

    def apply_json_move(self, move_json):
        color = WHITE if move_json["玩家棋子顏色"] == "白子" else BLACK
        x_str, y_str = move_json["下的格子"].split("之")
        x, y = int(x_str) - 1, int(y_str) - 1

        # ✅ 防止重複落子
        if (x, y) in self.state:
            return False

        self.state[(x, y)] = color
        self.history.append((x, y))
        return True

    def get_best_move(self):
        _, move = minimax(self.state, depth=2, alpha=float('-inf'), beta=float('inf'), is_ai_turn=True)
        if move is None:
            move = (BOARD_SIZE // 2, BOARD_SIZE // 2)
        return {
            "玩家棋子顏色": "白子",
            "下的格子": f"{move[0]+1}之{move[1]+1}"
        }