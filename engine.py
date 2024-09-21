from states import Board
import numpy as np
import math
import time
import copy
import heapq
from collections import defaultdict, OrderedDict
from typing import List, Tuple
from states import Piece
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

        # Transposition table dtype definition
        dtype = np.dtype(
            [
                ("zobrist", np.int64),
                ("score", np.float64),
                ("flag", "U10"),
                ("upper_bound", np.float64),
                ("lower_bound", np.float64),
                ("depth", np.int32),
                ("move", object),
            ]
        )

        self.t_table = np.zeros(self.size, dtype=dtype)
        self.num_elements = 0
        self.pruning_moves = dict()
        self.killer_moves = defaultdict(lambda: OrderedDict())
        self.history_heuristic = dict()
        self.max_size = IMP_MOVES_SIZE
        self.zobrist_table = np.random.randint(
            0, 2**63 - 1, size=(9, 9, 3), dtype=np.int64
        )

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

        # Retrieve transposition table entry if it exists and is deep enough
        if ttEntry["depth"] != -1 and ttEntry["depth"] >= depth:
            if ttEntry["flag"] == "EXACT":
                print(ttEntry["move"], ttEntry["move"][0].i, ttEntry["move"][0].j)
                new_board = board.create_new_board(ttEntry)
                new_board.zobrist = self.zobrist_hash(new_board)

                return ttEntry["score"], new_board
            elif ttEntry["flag"] == "LOWER_BOUND":
                alpha = max(alpha, ttEntry["score"])
                board.lower_bound = alpha
            elif ttEntry["flag"] == "UPPER_BOUND":
                beta = min(beta, ttEntry["score"])
                board.upper_bound = beta

            if alpha >= beta:
                return ttEntry["score"], board

        # Base case: if depth is zero, evaluate the board
        if depth == 0:
            board.turn = 2 if board.turn == 1 else 1
            board.utility_function()
            board.turn = 2 if board.turn == 1 else 1
            board.utility = -board.utility
            # print(board.board, board.win, board.game_over, board.utility)
            return board.utility, board

        # Search deeper using Negamax
        score = -math.inf
        boards = self.next_moves(board)

        for b, piece, move in boards:

            value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)

            value = -value
            # print(
            #     value,
            #     "value",
            #     score,
            #     "score",
            #     alpha,
            #     "alpha",
            #     beta,
            #     "beta",
            #     depth,
            #     "depth",
            # )

            if value > score:

                score = value
                board.best_board = b
                board.best_move = (piece, move)

            alpha = max(alpha, score)

            if alpha >= beta:
                if ORDENING["killer_moves"]:
                    self.add_killer_move(depth, (board.zobrist, b.zobrist))
                if ORDENING["pruning_moves"]:
                    self.add_pruning_move((board.zobrist, b.zobrist))

                break

        # Store result in the transposition table

        board.flag = (
            "EXACT"
            if old_alpha < score < beta
            else ("UPPER_BOUND" if score <= old_alpha else "LOWER_BOUND")
        )
        board.upper_bound = alpha
        board.lower_bound = beta
        board.score = score

        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((board.zobrist, board.best_board.zobrist), score)
        self.insert(board)

        return score, board.best_board

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
        killer_moves, pruning_moves, hist_h, captures = [], [], [], []

        for piece in board.pieces:

            if piece.team == turn:
                piece.is_selected = True
                for move in piece.possible_moves:
                    if piece.possible_moves[move]:
                        new_board_obj = Board(team=board.turn)
                        new_board_obj.pieces = copy.deepcopy(board.pieces)
                        new_board_obj.move_number = board.move_number
                        new_board_obj.win = board.win
                        new_board_obj.game_over = board.game_over
                        new_board_obj.change_board()
                        new_board_obj.move_pieces(move[0], move[1])
                        new_board_obj.handle_capture()
                        new_board_obj.turn = 2 if board.turn == 1 else 1
                        new_board_obj.zobrist = self.zobrist_hash(new_board_obj)
                        if (
                            ORDENING["killer_moves"]
                            and board.depth in self.killer_moves
                            and (board.zobrist, new_board_obj.zobrist)
                            in self.killer_moves[board.depth]
                        ):
                            killer_moves.append((new_board_obj, piece, move))
                        elif ORDENING["captures"] and new_board_obj.capture_available:
                            captures.append((new_board_obj, piece, move))
                        elif (
                            ORDENING["history_heuristic"] and board.zobrist,
                            new_board_obj.zobrist,
                        ) in self.history_heuristic:
                            hist_h.append((new_board_obj, piece, move))
                        elif (
                            ORDENING["pruning_moves"]
                            and (board.zobrist, new_board_obj.zobrist)
                            in self.pruning_moves
                        ):
                            pruning_moves.append((new_board_obj, piece, move))
                        else:
                            boards.append((new_board_obj, piece, move))

                piece.is_selected = False

        if ORDENING["history_heuristic"]:
            hist_h = sorted(
                hist_h,
                key=lambda item: self.history_heuristic.get(
                    (board.zobrist, item[0].zobrist), float("-inf")
                ),
                reverse=True,
            )

        if ORDENING["pruning_moves"]:
            pruning_moves = sorted(
                pruning_moves,
                key=lambda item: self.pruning_moves.get(
                    (board.zobrist, item[0].zobrist), float("-inf")
                ),
                reverse=True,
            )

        return killer_moves + captures + pruning_moves + hist_h + boards

    def add_pruning_move(self, move):  # add move to important moves
        if move not in self.pruning_moves:
            if len(self.pruning_moves) >= self.max_size:
                self.trim_important_moves()
            self.pruning_moves[move] = 0
        else:
            self.pruning_moves[move] += 1

    def trim_important_moves(self):  # trim important moves
        pruning_moves_keys = list(self.pruning_moves.keys())
        mid_index = len(pruning_moves_keys) // 2
        self.pruning_moves = {
            key: self.pruning_moves[key] for key in pruning_moves_keys[mid_index:]
        }
        print("Trimming important moves")

    def add_killer_move(self, depth, move):  # add killer move
        if depth not in self.killer_moves:
            self.killer_moves[depth] = {}

        if move in self.killer_moves[depth]:
            self.killer_moves[depth][move] += 1
        else:
            self.killer_moves[depth][move] = 1
        if len(self.killer_moves[depth]) > 10:
            self.killer_moves[depth] = OrderedDict(
                sorted(
                    self.killer_moves[depth].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[
                    :10
                ]  # keep only the best 100 moves
            )

    def add_history_heuristic(self, move, score):  # add history heuristic
        if move in self.history_heuristic:
            self.history_heuristic[move] += score
        else:
            if len(self.history_heuristic) >= self.max_size:
                self.trim_history_heuristic()
                print("Trimming history")

            self.history_heuristic[move] = score

    def trim_history_heuristic(self):  # trim history heuristic
        sorted_history = sorted(
            self.history_heuristic.items(), key=lambda x: x[1], reverse=True
        )

        mid_index = len(sorted_history) // 2
        self.history_heuristic = dict(sorted_history[:mid_index])

        print("Trimming history")

    def zobrist_hash(self, board: Board):  # zobrist hash
        zobrist_value = 0
        for row in range(9):
            for col in range(9):
                if board.board[row, col] != 0:
                    value = board.board[row, col]
                    zobrist_value ^= self.zobrist_table[row, col, value]

        return zobrist_value

    def hash_index(self, zobrist_value):  # hash index
        return zobrist_value % self.size

    def insert(self, board: Board):  # insert into table
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
                    (copy.deepcopy(board.best_move[0]), board.best_move[1]),
                )
            ],
            dtype=self.t_table.dtype,
        )

        self.num_elements += 1

    def get(self, key):  # get from table
        index = self.hash_index(key)
        entry = self.t_table[index]
        if entry["depth"] == -1:
            return {"depth": -1}
        return entry

    def change_table(self):  # change table
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
        score, best_board = self.alpha_beta_Negamax(board, depth, alpha, beta)
        best_board.old_pieces = old_pieces
        board = copy.deepcopy(best_board)

        if self.reset_table:
            self.clear_table()
        self.pruning_moves = dict()
        elapsed_time = time.time() - start_time

        print(f"Tempo impiegato da alpha_beta_Negamax: {elapsed_time:.4f} secondi")
        print(f"Numero di mosse: {board.move_number}")
        print(f"score: {score}")

        return board
