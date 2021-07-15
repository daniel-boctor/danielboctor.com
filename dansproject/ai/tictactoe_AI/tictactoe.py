from copy import deepcopy
import random

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    empty_spaces = 0
    for row in board:
        for cell in row:
            if not cell:
                empty_spaces += 1
    if empty_spaces % 2 == 0:
        return O
    else:
        return X


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """
    actions = set()
    for i in range(len(board)):
        for j in range(len(board[i])):
            if not board[i][j]:
                actions.add((i, j))
    return actions
                


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    if not actions(board):
        raise RuntimeError
    result = deepcopy(board)
    result[action[0]][action[1]] = player(board)
    return result


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    for row in board:
        if row[0] is not None and row[0] == row[1] == row[2]:
            return row[0]
    for col in range(3):
        if board[0][col] is not None and board[0][col] == board[1][col] == board[2][col]:
            return board[0][col]
    if board[0][0] is not None and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] is not None and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
        
    return None
    

def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """
    if winner(board):
        return True
    if not actions(board):
        return True
    return False


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """
    if winner(board) == X:
        return 1
    if winner(board) == O:
        return -1
    else:
        return 0

def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """
    tmp = 0
    for row in board:
        for cell in row:
            if cell == None:
                tmp += 1
    if tmp == 9:
        return (0, 1)
    if player(board) == X:
        v = -2
        for action in actions(board):
            tmp = min_value(result(board, action), v)
            if tmp > v:
                v = tmp
                best_action = action
        return best_action
            

    elif player(board) == O:
        v = 2
        for action in actions(board):
            tmp = max_value(result(board, action), v)
            if tmp < v:
                v = tmp
                best_action = action
        return best_action

def max_value(board, running_best_util):
    if terminal(board):
        return utility(board)
    v = -2
    for action in actions(board):
        if v > running_best_util:
            return 2
        v = max(v, min_value(result(board, action), v))
    return v
    
def min_value(board, running_best_util):
    if terminal(board):
        return utility(board)
    v = 2
    for action in actions(board):
        if v < running_best_util:
            return -2
        v = min(v, max_value(result(board, action), v))
    return v

class tictactoe_AI():
    def __init__(self, alpha=0.5, epsilon=0.1):
        self.q = dict()
        self.alpha = alpha
        self.epsilon = epsilon

    def get_available_moves(self, state):
        moves = []
        for row in range(len(state)):
            for cell in range(len((state[row]))):
                if state[row][cell] == EMPTY:
                    moves.append((row, cell))
        return moves

    def update(self, old_state, action, new_state, reward):
        old = self.get_q_value(old_state, action)
        best_future = self.best_future_reward(new_state)
        self.update_q_value(old_state, action, old, reward, best_future)
    
    def get_q_value(self, state, action):
        if (tuple([tuple(row) for row in state]), action) in self.q.keys():
            return self.q[(tuple([tuple(row) for row in state]), action)]
        return 0

    def update_q_value(self, state, action, old_q, reward, future_rewards):
        self.q[(tuple([tuple(row) for row in state]), action)] = old_q + (self.alpha * (reward + future_rewards - old_q))

    def best_future_reward(self, state):
        tmp_max = 0
        for move in self.get_available_moves(state):
            if self.get_q_value(state, move) > tmp_max:
                tmp_max = self.get_q_value(state, move)
        return tmp_max

    def choose_action(self, state, epsilon=True):
        tmp_max = -2
        tmp_action = tuple()
        if epsilon:
            if random.choices(["random", "greedy"], [self.epsilon, 1-self.epsilon])[0] == "random":
                return random.choice(self.get_available_moves(state))
        for move in self.get_available_moves(state):
                if not self.q:
                    return move
                if self.get_q_value(state, move) > tmp_max:
                    tmp_max = self.get_q_value(state, move)
                    tmp_action = move
        return tmp_action

def train(n):
    AI = tictactoe_AI()

    for i in range(n):
        print(f"Playing training game {i + 1}")

        last = {
            X: {"state": None, "action": None},
            O: {"state": None, "action": None}
        }

        board = initial_state()
        while True:
            action = AI.choose_action(board)

            last[player(board)]["state"] = deepcopy(board)
            last[player(board)]["action"] = deepcopy(action)

            board[action[0]][action[1]] = player(board)

            if terminal(board) == True:
                if winner(board):
                    winner1 = winner(board)
                    loser = O if winner1 == X else X
                    AI.update(last[winner1]["state"],
                    last[winner1]["action"],
                    board,
                    1)
                    AI.update(last[loser]["state"],
                    last[loser]["action"],
                    board,
                    -1)
                else:
                    AI.update(last[X]["state"],
                    last[X]["action"],
                    board,
                    0)
                    AI.update(last[O]["state"],
                    last[O]["action"],
                    board,
                    0)
                break

            elif last[player(board)]["state"] is not None:
                AI.update(
                    last[player(board)]["state"],
                    last[player(board)]["action"],
                    board,
                    0
                )

    print("Done training")
    return AI