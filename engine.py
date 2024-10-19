from states import Board
import numpy as np
import math
import time
import copy
import heapq
from collections import defaultdict, OrderedDict
from parameters import IMP_MOVES_SIZE, ORDENING, TT, AS, MULTICUT, VARIABLE_DEPTH


class Engine:
    """
    A class representing the game engine responsible for handling the game state,
    performing alpha-beta pruning using Negamax, and managing transposition tables.
    """

    def __init__(
        self, size: int = 4000, p: float = 0.75, reset_table: bool = True
    ) -> None:
        """
        Initialize the Engine with transposition table settings, zobrist hashing,
        and move-tracking structures like killer moves and important moves.

        Parameters:
            size (int): Size of the transposition table.
            p (float): Percentage of table to retain during optimization.
            reset_table (bool): Whether to reset the transposition table after each move.
        """
        self.proof = 3
        self.size = size
        self.reset_table = reset_table
        self.percentage = p
        self.collisions = 0
        self.max_depth = 0
        self.pruning_numbers = 0
        dtype = np.dtype(
            [
                ("score", np.int32),
                ("flag", "U10"),
                ("upper_bound", np.int32),
                ("lower_bound", np.int32),
                ("depth", np.int8),
                ("best_move", object),
            ]
        )

        self.t_table = np.zeros(self.size, dtype=dtype)

        self.num_elements = 0
        self.pruningMoves = dict()
        self.killerMoves = defaultdict(lambda: OrderedDict())
        self.histHeuristic = dict()
        self.max_size = IMP_MOVES_SIZE
        self.zobrist_table = np.random.randint(
            0, 2**63 - 1, size=(9, 9, 3), dtype=np.int64
        )

    def aspirational_search(self, board: Board, d: int, alpha: int, beta: int):
        guess = 0
        guess = 0
        start_time = time.time()  # Record the start time

        for d in range(1, 7):
            if (
                time.time() - start_time > 15
            ):  # Check if the elapsed time exceeds 15 seconds
                break

            alpha = guess - 15000
            beta = guess + 15000
            score, bestBoard = self.alpha_beta_Negamax(board, d, alpha, beta)

            score = -score
            if score <= alpha:
                print("fail low")
                alpha = -math.inf
                beta = score
                score, bestBoard = self.alpha_beta_Negamax(board, d, alpha, beta)
                score = -score

            elif score >= beta:
                print("fail high")
                alpha = score
                beta = math.inf
                score, bestBoard = self.alpha_beta_Negamax(board, d, alpha, beta)
                score = -score

            guess = score

        return score, bestBoard

    def multi_cut(self, C, M, board: Board, depth: int, alpha: float, beta: float):

        if depth == 0:
            if board.turn == board.team:
                board.utility_function()

            else:
                board.utility_function()
                board.utility = -board.utility

            return board.utility, board

        score = -math.inf
        boards = self.next_moves(board)
        print(boards)
        c = 0
        m = 0
        while len(boards) > 0 and m < M:
            b, oi, oj, i, j = boards.pop(0)
            value, _ = self.alpha_beta_Negamax_TT(b, depth - 1 - 2, -beta, -alpha)

            value = -value

            if value >= beta:
                c += 1
                if c >= C:
                    return beta, b
            m += 1

        for b, oi, oj, i, j in boards:
            if VARIABLE_DEPTH:
                if abs(oi - i) > 1:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth, -beta, -alpha)

                else:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth - 1, -beta, -alpha)

            else:
                value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)
            value = -value
            if value > score:
                score = value
                bestBoard = b
                bestMove = (oi, oj, i, j)

            alpha = max(alpha, score)

            if alpha >= beta:
                if ORDENING["killer_moves"]:
                    self.add_killer_move(depth, (board.zobrist, b.zobrist))
                if ORDENING["pruning_moves"]:
                    self.add_pruning_move((board.zobrist, b.zobrist))
                self.pruning_numbers += 1
                break
        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((bestMove), depth)
        return score, bestBoard

    def alpha_beta_Negamax(self, board: Board, depth: int, alpha: float, beta: float):

        if depth == 0:
            if board.turn == board.team:
                board.utility_function()

            else:
                board.utility_function()
                board.utility = -board.utility

            return board.utility, board

        score = -math.inf
        boards = self.next_moves(board)

        for b, oi, oj, i, j in boards:
            if VARIABLE_DEPTH:
                if abs(oi - i) > 1:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth, -beta, -alpha)

                else:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth - 1, -beta, -alpha)

            else:
                value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)
            value = -value
            if value > score:
                score = value
                bestBoard = b
                bestMove = (oi, oj, i, j)

            alpha = max(alpha, score)

            if alpha >= beta:
                if ORDENING["killer_moves"]:
                    self.add_killer_move(depth, (board.zobrist, b.zobrist))
                if ORDENING["pruning_moves"]:
                    self.add_pruning_move((board.zobrist, b.zobrist))
                self.pruning_numbers += 1
                break
        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((bestMove), depth)
        return score, bestBoard

    def alpha_beta_Negamax_TT(
        self, board: Board, depth: int, alpha: float, beta: float
    ):
        """
        Implements the Alpha-Beta pruning algorithm with Negamax search and transposition table (TT) lookup.
        This method efficiently searches for the best move in a two-player zero-sum game.

        Parameters:
            board (Board): The current state of the game board.
            depth (int): The maximum depth for the search.
            alpha (float): The current lower bound of the search window.
            beta (float): The current upper bound of the search window.

        Returns:
            (float, Board): A tuple containing the best score evaluated and the corresponding board state after the best move.

        This implementation uses the following strategies:
        1. **Transposition Table (TT)**: Stores previously computed game states (zobrist keys) to avoid redundant calculations.
           It checks if a state has been explored with the same or greater depth, returning the stored result to prune unnecessary branches.
           The flags used in the TT entry are:
             - "EXACT": Exact value of the board score.
             - "LOWER_BOUND": Score is greater than or equal to this value.
             - "UPPER_BOUND": Score is less than or equal to this value.

        2. **Negamax**: A variant of minimax for two-player zero-sum games. Here, maximizing the opponent's score is equivalent to minimizing the player's score,
           so the algorithm negates the result at each recursive level.

        3. **Alpha-Beta Pruning**: Cuts off branches of the search tree that can't improve the current evaluation, reducing the number of nodes to evaluate.

        4. **Variable Depth**: Allows dynamic depth adjustments for certain moves, extending the search depth for specific cases (e.g., moves that involve greater changes).

        5. **Move Ordering**: Heuristic techniques such as killer moves, history heuristic, and pruning moves are used to prioritize promising moves early in the search,
           increasing pruning efficiency.

        This method updates the TT with the best move, score, and flags after evaluating all possible next moves.

        """
        old_alpha = alpha
        zobrist_key = board.zobrist
        board.depth = depth
        ttEntry = self.get(zobrist_key)
        if ttEntry["depth"] != 0:
            if ttEntry["flag"] == "EXACT":
                oi, oj, i, j = ttEntry["best_move"]
                newBoard = board.create_new_board(oi, oj, i, j)
                newBoard.zobrist = self.zobrist_hash(newBoard)
                return ttEntry["score"], newBoard

            elif ttEntry["flag"] == "LOWER_BOUND":
                alpha = max(alpha, ttEntry["score"])
                board.lower_bound = alpha
            elif ttEntry["flag"] == "UPPER_BOUND":
                beta = min(beta, ttEntry["score"])
                board.upper_bound = beta

            if alpha >= beta:
                return ttEntry["score"], board

        if depth == 0:
            if board.turn == board.team:
                board.utility_function()

            else:
                board.utility_function()
                board.utility = -board.utility

            return board.utility, board

        score = -math.inf

        boards = self.next_moves(board)

        for b, oi, oj, i, j in boards:
            if VARIABLE_DEPTH:
                if abs(oi - i) > 1:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth, -beta, -alpha)

                else:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth - 1, -beta, -alpha)

            else:
                value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)

            value = -value
            if value > score:
                score = value
                bestMove = (oi, oj, i, j)
                bestBoard = b

            alpha = max(alpha, score)

            if alpha >= beta:
                if ORDENING["killer_moves"]:
                    self.add_killer_move(depth, (board.zobrist, b.zobrist))
                if ORDENING["pruning_moves"]:
                    self.add_pruning_move((board.zobrist, b.zobrist))
                self.pruning_numbers += 1

                break
        board.flag = "EXACT"
        if score <= old_alpha:
            board.flag = "UPPER_BOUND"
        elif score >= beta:
            board.flag = "LOWER_BOUND"
        board.upper_bound = beta
        board.lower_bound = alpha
        board.best_move = bestMove
        board.score = score
        board.bestBoard = bestBoard

        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((bestMove), depth)

        self.insert(board)

        return score, bestBoard

    def next_moves(self, board: Board):
        """
        Process the possible moves for a given piece and update the board lists.

        Parameters:
            board (Board): The current board state.
            piece (Piece): The piece being processed.
            boards (List): List to append regular moves.
            imp_boards (List): List to append important moves.
            killer_moves (List): List to append killer moves.
        """
        boards = []
        board.handle_capture()
        turn = board.turn
        killerMoves, pruningMoves, histHeuristic, captMoves = [], [], [], []

        for i in range(9):
            for j in range(9):
                if board.board[i, j] == turn:
                    for move in board.possible_moves[(i, j)]:
                        if board.possible_moves[(i, j)][move]:
                            newBoardObj = board.create_new_board(i, j, move[0], move[1])
                            newBoardObj.zobrist = self.zobrist_hash(newBoardObj)

                            if (
                                ORDENING["killer_moves"]
                                and board.depth in self.killerMoves
                                and (board.zobrist, newBoardObj.zobrist)
                                in self.killerMoves[board.depth]
                            ):
                                killerMoves.append(
                                    (newBoardObj, i, j, move[0], move[1])
                                )
                            elif ORDENING["captures"] and newBoardObj.capture_available:
                                captMoves.append((newBoardObj, i, j, move[0], move[1]))
                            elif (
                                ORDENING["history_heuristic"]
                                and (i, j, move[0], move[1])
                            ) in self.histHeuristic:
                                histHeuristic.append(
                                    (newBoardObj, i, j, move[0], move[1])
                                )
                            elif (
                                ORDENING["pruning_moves"]
                                and (board.zobrist, newBoardObj.zobrist)
                                in self.pruningMoves
                            ):
                                pruningMoves.append(
                                    (newBoardObj, i, j, move[0], move[1])
                                )
                            else:
                                boards.append((newBoardObj, i, j, move[0], move[1]))
        if ORDENING["killer_moves"]:
            self.sort_killer_moves(killerMoves, board, self.killerMoves[board.depth])
        if ORDENING["history_heuristic"]:
            self.sort_hist_moves(histHeuristic, board, self.histHeuristic)

        return killerMoves + captMoves + pruningMoves + histHeuristic + boards

    def sort_killer_moves(self, move_list, board, move_dict):
        if move_list:
            move_list.sort(
                key=lambda item: move_dict.get(
                    (board.zobrist, item[0].zobrist), float("-inf")
                ),
                reverse=True,
            )

    def sort_hist_moves(self, move_list, board, move_dict):
        if move_list:
            move_list.sort(
                key=lambda item: move_dict.get(item[1], float("-inf")),
                reverse=True,
            )

    def add_pruning_move(self, move):  # add move to important moves
        if move not in self.pruningMoves:
            if len(self.pruningMoves) >= self.max_size:
                self.trim_pruning_moves()
            self.pruningMoves[move] = 1
        else:
            self.pruningMoves[move] += 1

    def trim_pruning_moves(self):  # trim important moves
        pmkeys = list(self.pruningMoves.keys())
        mid_index = len(pmkeys) // 2
        self.pruningMoves = {key: self.pruningMoves[key] for key in pmkeys[mid_index:]}
        print("Trimming important moves")

    def add_killer_move(self, depth, move):  # add killer move
        if depth not in self.killerMoves:
            self.killerMoves[depth] = {}

        if move in self.killerMoves[depth]:
            self.killerMoves[depth][move] += 1
        else:
            self.killerMoves[depth][move] = 1
        if len(self.killerMoves[depth]) > 10:
            self.killerMoves[depth] = OrderedDict(
                sorted(
                    self.killerMoves[depth].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[
                    :10
                ]  # keep only the best 10 moves for depth
            )

    def add_history_heuristic(self, move, depth):  # add history heuristic
        if move in self.histHeuristic:
            self.histHeuristic[move] += 2 * depth
        else:
            if len(self.histHeuristic) >= self.max_size:
                self.trim_history_heuristic()

                ("Trimming history")

            self.histHeuristic[move] = 2 * depth

    def trim_history_heuristic(self):  # trim history heuristic
        sorted_history = sorted(
            self.histHeuristic.items(), key=lambda x: x[1], reverse=True
        )

        mid_index = len(sorted_history) // 2
        self.histHeuristic = dict(sorted_history[:mid_index])

        print("Trimming history")

    def zobrist_hash(self, board: Board):  # zobrist hash
        zobrist_value = 0
        for row in range(9):
            for col in range(9):
                if board.board[row, col] != 0:
                    value = board.board[row, col]
                    zobrist_value ^= self.zobrist_table[row, col, value]

        return zobrist_value

    def hash_index(self, zobrist_value):
        return zobrist_value % self.size

    def insert(self, board: Board):

        # board.zobrist = self.zobrist_hash(board)
        index = self.hash_index(board.zobrist)
        if self.t_table[index]["depth"] != 0:
            self.collisions += 1
            if self.t_table[index]["depth"] > board.depth:

                self.t_table[index] = np.array(
                    [
                        (
                            board.score,
                            board.flag,
                            board.upper_bound,
                            board.lower_bound,
                            board.depth,
                            board.best_move,
                        )
                    ],
                    dtype=self.t_table.dtype,
                )

                self.num_elements += 1

                return

        self.t_table[index] = np.array(
            [
                (
                    board.score,
                    board.flag,
                    board.upper_bound,
                    board.lower_bound,
                    board.depth,
                    board.best_move,
                )
            ],
            dtype=self.t_table.dtype,
        )

        self.num_elements += 1

    def get(self, key):
        index = self.hash_index(key)
        entry = self.t_table[index]
        if entry["depth"] == -1:
            return {"depth": -1}
        return entry

    def change_table(self):
        new_table = np.zeros(self.size, dtype=self.t_table.dtype)
        print("Optimizing table")
        all_elements = []
        for i in range(self.size):
            entry = self.t_table[i]
            if entry["depth"] != -1:
                all_elements.append((entry))

        largest_elements = heapq.nlargest(
            int(self.size * self.percentage), all_elements, key=lambda x: x[1]["depth"]
        )

        for zobrist, entry in largest_elements:
            new_index = self.hash_index(zobrist) % self.size
            new_table[new_index] = entry

        self.table = new_table

    def clear_table(self):
        self.t_table = np.zeros(self.size, dtype=self.t_table.dtype)
        self.num_elements = 0

    def think(self, board: Board, depth, alpha, beta):
        start_time = time.time()
        board.zobrist = self.zobrist_hash(board)
        if TT:
            score, bestBoard = self.alpha_beta_Negamax_TT(board, depth, alpha, beta)

        elif MULTICUT:
            score, bestBoard = self.multi_cut(2, 3, board, depth, alpha, beta)

        elif AS:
            score, bestBoard = self.aspirational_search(board, depth, alpha, beta)
        else:
            score, bestBoard = self.alpha_beta_Negamax(board, depth, alpha, beta)

        best_move = board.best_move
        board = copy.deepcopy(bestBoard)

        if self.reset_table:

            self.clear_table()

        self.pruningMoves = dict()
        elapsed_time = time.time() - start_time

        print(f"Time taken by alpha_beta_Negamax: {elapsed_time:.4f} seconds")
        print(f"Number of moves: {board.move_number}")
        print(f"Score: {score}")
        print(f"depth: {depth}")
        print(f"Prunings: {self.pruning_numbers}")
        print(f"Best move: {best_move}")
        print(f"Numbers of Collision: {self.collisions}")
        print("\n")
        print(self.histHeuristic)
        self.collisions = 0
        self.pruning_numbers = 0

        return board
