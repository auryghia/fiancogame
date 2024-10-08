from states import Board
import numpy as np
import math
import time
import copy
import heapq
from collections import defaultdict, OrderedDict
from parameters import IMP_MOVES_SIZE, ORDENING


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
        self.zobrist_keys = []
        self.size = size
        self.reset_table = reset_table
        self.percentage = p

        dtype = np.dtype(
            [
                ("zobrist", np.int64),
                ("score", np.float64),
                ("flag", "U10"),
                ("upper_bound", np.float64),
                ("lower_bound", np.float64),
                ("depth", np.int32),
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

    def hash_function(self, key):
        return hash(int(str(abs(key))[:6])) % self.size

    def alpha_beta_Negamax(self, board: Board, depth: int, alpha: float, beta: float):
        """
        Implements the alpha-beta pruning algorithm with Negamax for move search and evaluation.

        Parameters:
            board (Board): The current board state.
            depth (int): The depth of the search.
            alpha (float): Alpha value for pruning.
            beta (float): Beta value for pruning.

        Returns:
            (float, Board): The best score and the corresponding board state.
        """

        old_alpha = alpha
        zobrist_key = board.zobrist
        board.depth = depth
        ttEntry = self.get(zobrist_key)
        if ttEntry["depth"] != -1:
            if ttEntry["flag"] == "EXACT":
                # print("Transposition table hit")

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
            board.turn = 2 if board.turn == 1 else 1
            board.utility_function()
            board.turn = 2 if board.turn == 1 else 1
            board.utility = -board.utility
            return board.utility, board

        score = -math.inf
        boards = self.next_moves(board)

        for b, oi, oj, i, j in boards:

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

                break

        board.flag = (
            "EXACT"
            if old_alpha < score < beta
            else ("UPPER_BOUND" if score <= old_alpha else "LOWER_BOUND")
        )

        board.upper_bound = alpha
        board.lower_bound = beta
        board.best_move = bestMove
        board.score = score
        board.bestBoard = bestBoard
        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((board.zobrist, board.bestBoard.zobrist), score)

        self.insert(board)

        return score, board.bestBoard

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

        for piece in board.pieces:

            if piece.team == turn:
                for move in piece.possibleMoves:
                    if piece.possibleMoves[move]:
                        i, j = piece.i, piece.j
                        newBoardObj = board.create_new_board(i, j, move[0], move[1])
                        newBoardObj.zobrist = self.zobrist_hash(newBoardObj)

                        if (
                            ORDENING["killer_moves"]
                            and board.depth in self.killerMoves
                            and (board.zobrist, newBoardObj.zobrist)
                            in self.killerMoves[board.depth]
                        ):
                            killerMoves.append((newBoardObj, i, j, move[0], move[1]))
                        elif ORDENING["captures"] and newBoardObj.capture_available:
                            captMoves.append((newBoardObj, i, j, move[0], move[1]))
                        elif (
                            ORDENING["history_heuristic"] and board.zobrist,
                            newBoardObj.zobrist,
                        ) in self.histHeuristic:
                            histHeuristic.append((newBoardObj, i, j, move[0], move[1]))
                        elif (
                            ORDENING["pruning_moves"]
                            and (board.zobrist, newBoardObj.zobrist)
                            in self.pruningMoves
                        ):
                            pruningMoves.append((newBoardObj, i, j, move[0], move[1]))
                        else:
                            boards.append((newBoardObj, i, j, move[0], move[1]))

        self.sort_moves(histHeuristic, board, self.histHeuristic)
        self.sort_moves(pruningMoves, board, self.pruningMoves)

        return killerMoves + captMoves + pruningMoves + histHeuristic + boards

    def sort_moves(self, move_list, board, move_dict):
        if move_list:
            move_list.sort(
                key=lambda item: move_dict.get(
                    (board.zobrist, item[0].zobrist), float("-inf")
                ),
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

    def add_history_heuristic(self, move, score):  # add history heuristic
        if move in self.histHeuristic:
            self.histHeuristic[move] += score
        else:
            if len(self.histHeuristic) >= self.max_size:
                self.trim_history_heuristic()
                print("Trimming history")

            self.histHeuristic[move] = score

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
        if self.num_elements == self.size:
            self.change_table()

        # board.zobrist = self.zobrist_hash(board)
        index = self.hash_index(board.zobrist)

        self.t_table[index] = np.array(
            [
                (
                    board.zobrist,
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
        all_elements = []
        for i in range(self.size):
            entry = self.t_table[i]
            if entry["depth"] != -1:
                key = self.hash_index(entry["zobrist"])
                all_elements.append((key, entry))

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
        old_pieces = copy.deepcopy(board.pieces)
        start_time = time.time()
        board.zobrist = self.zobrist_hash(board)
        score, bestBoard = self.alpha_beta_Negamax(board, depth, alpha, beta)
        bestBoard.old_pieces = old_pieces
        board = copy.deepcopy(bestBoard)
        if self.reset_table:
            self.clear_table()

        self.pruningMoves = dict()
        elapsed_time = time.time() - start_time

        print(f"Time taken by alpha_beta_Negamax: {elapsed_time:.4f} seconds")
        print(f"Number of moves: {board.move_number}")
        print(f"Score: {score}")

        return board
