import random

class Nim():

    def __init__(self, initial=[1, 3, 5, 7]):
        self.piles = initial.copy()
        self.player = 0
        self.winner = None

    @classmethod
    def available_actions(cls, piles):
        actions = set()
        for i, pile in enumerate(piles):
            for j in range(1, pile + 1):
                actions.add((i, j))
        return actions

    @classmethod
    def other_player(cls, player):
        return 0 if player == 1 else 1

    def switch_player(self):
        self.player = Nim.other_player(self.player)

    def move(self, action):
        pile, count = action

        # Check for errors
        if self.winner is not None:
            raise Exception("Game already won")
        elif pile < 0 or pile >= len(self.piles):
            raise Exception("Invalid pile")
        elif count < 1 or count > self.piles[pile]:
            raise Exception("Invalid number of objects")

        # Update pile
        self.piles[pile] -= count
        self.switch_player()

        # Check for a winner
        if all(pile == 0 for pile in self.piles):
            self.winner = self.player


class NimAI():

    def __init__(self, alpha=0.5, epsilon=0.1):
        self.q = dict()
        self.alpha = alpha
        self.epsilon = epsilon

    def update(self, old_state, action, new_state, reward):
        old = self.get_q_value(old_state, action)
        best_future = self.best_future_reward(new_state)
        self.update_q_value(old_state, action, old, reward, best_future)

    def get_q_value(self, state, action):
        if (tuple(state), action) in self.q.keys():
            return self.q[(tuple(state), action)]
        return 0

    def update_q_value(self, state, action, old_q, reward, future_rewards):
        self.q[(tuple(state), action)] = old_q + (self.alpha * (reward + future_rewards - old_q))

    def best_future_reward(self, state):
        tmp_max = 0
        for i, val_i in enumerate(state):
            if val_i == 0:
                continue
            for j in range(1, val_i+1):
                if self.get_q_value(state, (i, j)) > tmp_max:
                    tmp_max = self.get_q_value(state, (i, j))
        return tmp_max


    def choose_action(self, state, epsilon=True):
        tmp_max = -2
        tmp_action = tuple()
        if epsilon:
            if random.choices(["random", "greedy"], [self.epsilon, 1-self.epsilon])[0] == "random":
                actions = list()
                for i, val_i in enumerate(state):
                    if val_i == 0:
                        continue
                    for j in range(1, val_i+1):
                        actions.append((i, j))
                return random.choices(actions)[0]
        for i, val_i in enumerate(state):
            if val_i == 0:
                continue
            for j in range(1, val_i+1):
                if not self.q:
                    return (i, j)
                if self.get_q_value(state, (i, j)) > tmp_max:
                    tmp_max = self.get_q_value(state, (i, j))
                    tmp_action = (i, j)
        return tmp_action

    def terminal(state):
        for pile in state:
            if pile != 0:
                return False
        return True


def train(n):
    player = NimAI()

    for i in range(n):
        print(f"Playing training game {i + 1}")
        game = Nim()

        last = {
            0: {"state": None, "action": None},
            1: {"state": None, "action": None}
        }

        while True:
            state = game.piles.copy()
            action = player.choose_action(game.piles)

            last[game.player]["state"] = state
            last[game.player]["action"] = action

            game.move(action)
            new_state = game.piles.copy()

            if game.winner is not None:
                player.update(state, action, new_state, -1)
                player.update(
                    last[game.player]["state"],
                    last[game.player]["action"],
                    new_state,
                    1
                )
                break

            elif last[game.player]["state"] is not None:
                player.update(
                    last[game.player]["state"],
                    last[game.player]["action"],
                    new_state,
                    0
                )

    print("Done training")
    return player