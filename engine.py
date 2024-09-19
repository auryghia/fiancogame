from states import Board
import numpy as np
import math
import time
import copy
import heapq
from parameters import IMP_MOVES_SIZE


class Engine:  # class for the engine
    def __init__(self, size: int = 4000, p: float = 0.75, reset_table=True) -> None:
        self.proof = 3
        self.dictionary = {}
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
            ]
        )
        self.t_table = np.zeros(self.size, dtype=dtype)
        self.percentage = p
        self.num_elements = 0
        self.important_moves = dict()
        self.max_size = IMP_MOVES_SIZE

    def add_move(self, move):
        if len(self.important_moves) >= self.max_size:
            self.trim_important_moves()
        self.important_moves[move] = 0

    def trim_important_moves(self):
        important_moves_keys = list(self.important_moves.keys())
        mid_index = len(important_moves_keys) // 2
        self.important_moves = {
            key: self.important_moves[key] for key in important_moves_keys[mid_index:]
        }
        print("Trimming important moves")

    def zobrist_hash(self, board: Board):
        zobrist_value = 0

        for piece in board.pieces:
            zobrist_value ^= board.dictionary[(piece.id, piece.i, piece.j)]

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

    def alpha_beta_Negamax(self, board: Board, depth, alpha, beta):
        old_alpha = alpha
        # board.zobrist = self.zobrist_hash(board)
        zobrist_key = board.zobrist
        ttEntry = self.get(zobrist_key)
        # print("inizio", board.board, alpha, beta, board.turn)

        if ttEntry != {"depth": -1} and ttEntry["depth"] >= depth:

            if ttEntry["flag"] == "EXACT":
                return ttEntry["score"], board
            elif ttEntry["flag"] == "LOWER_BOUND":
                alpha = max(alpha, ttEntry["score"])
                board.lower_bound = alpha
            elif ttEntry["flag"] == "UPPER_BOUND":
                beta = min(beta, ttEntry["score"])
                board.upper_bound = beta

            if alpha >= beta:
                return ttEntry["score"], board

        if depth == 0:

            board, _ = self.handle_capture(board)
            board.utility_function()
            board.score = board.utility
            return board.score, board

        score = -math.inf
        best_board = None
        boards = self.next_moves(board)
        for b, capture in boards:

            value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)

            value = -value
            if value > score:
                # print(b.board, alpha, beta, b.turn)
                score = value
                board.best_move = b

            alpha = max(alpha, score)

            if alpha >= beta:
                # print(b.board, alpha, beta, b.turn)
                if (board.zobrist, b.zobrist) not in self.important_moves:
                    self.add_move((board.zobrist, b.zobrist))

                else:
                    self.important_moves[(board.zobrist, b.zobrist)] += 1

                print(self.important_moves)
                break

        if score <= old_alpha:
            board.flag = "UPPER_BOUND"  # fail low
        elif score >= beta:
            board.flag = "LOWER_BOUND"  # fail high
        else:
            board.flag = "EXACT"

        board.score = score
        board.upper_bound = alpha
        board.lower_bound = beta
        board.depth = depth
        self.insert(board)

        return score, board.best_move

    def move_pieces(self, b: Board, i, j):
        for piece in b.pieces:

            if piece.is_selected:

                b.board[piece.i, piece.j] = 0

                piece.old_i, piece.old_j = piece.i, piece.j

                piece.move(i, j)

                if abs(i - piece.old_i) == 2:

                    mid_i = (i + piece.old_i) // 2
                    mid_j = (j + piece.old_j) // 2

                    b.board[mid_i, mid_j] = 0

                    for p in b.pieces:
                        if p.i == mid_i and p.j == mid_j:
                            b.pieces.remove(p)
                            break
                b.board[piece.i, piece.j] = piece.team

                piece.is_selected = False
        return b

    def handle_capture(self, board: Board):
        capture_available = False

        for piece in board.pieces:
            if piece.team == board.turn:
                if piece.team == board.team:
                    piece.possible_moves_f(board.board, -1)
                else:
                    piece.possible_moves_f(board.board, +1)

                if (
                    (
                        piece.i - 2 >= 0
                        and piece.j - 2 >= 0
                        and piece.possible_moves[(piece.i - 2, piece.j - 2)] == True
                    )
                    or (
                        piece.i - 2 >= 0
                        and piece.j + 2 < 9
                        and piece.possible_moves[(piece.i - 2, piece.j + 2)] == True
                    )
                    or (
                        piece.i + 2 < 9
                        and piece.j - 2 >= 0
                        and piece.possible_moves[(piece.i + 2, piece.j - 2)] == True
                    )
                    or (
                        piece.i + 2 < 9
                        and piece.j + 2 < 9
                        and piece.possible_moves[(piece.i + 2, piece.j + 2)] == True
                    )
                ):
                    capture_available = True
            if capture_available:
                for p in board.pieces:
                    if p.team == board.turn:

                        for move in p.possible_moves:
                            if abs(move[0] - p.i) != 2 or abs(move[1] - p.j) != 2:
                                p.possible_moves[move] = False

        return board, capture_available

    def next_moves(self, board: Board):
        boards = []
        board, capture = self.handle_capture(board)
        turn = board.turn
        imp_boards = []
        for piece in board.pieces:

            piece.is_selected = True
            if piece.team == board.turn:
                for move in piece.possible_moves:
                    if piece.possible_moves[move] == True:

                        new_board_obj = Board(team=turn)
                        new_board_obj.pieces = copy.deepcopy(board.pieces)
                        new_board_obj.change_board()
                        new_board_obj.dictionary = board.dictionary
                        new_board_obj = self.move_pieces(
                            new_board_obj, move[0], move[1]
                        )
                        new_board_obj.zobrist = self.zobrist_hash(new_board_obj)
                        new_board_obj.turn = 1 if board.turn == 2 else 2

                        if (
                            board.zobrist,
                            new_board_obj.zobrist,
                        ) in self.important_moves:
                            imp_boards.append((new_board_obj, capture))

                        else:

                            boards.append((new_board_obj, capture))

            piece.is_selected = False
            imp_boards = sorted(
                imp_boards,
                key=lambda item: self.important_moves.get(
                    (board.zobrist, item[0].zobrist), float("-inf")
                ),
                reverse=True,
            )

        return imp_boards + boards

    def think(self, board: Board, depth, alpha, beta):

        old_pieces = copy.deepcopy(board.pieces)
        start_time = time.time()
        board.zobrist = self.zobrist_hash(board)
        best_score, best_move = self.alpha_beta_Negamax(board, depth, alpha, beta)
        best_move.old_pieces = old_pieces
        board = copy.deepcopy(best_move)
        if self.reset_table:
            self.clear_table()
        elapsed_time = time.time() - start_time

        print(f"Tempo impiegato da alpha_beta_Negamax: {elapsed_time:.4f} secondi")

        return board
