from states import Board
import numpy as np
import math
import time
import copy
import heapq
from collections import defaultdict, OrderedDict
from parameters import IMP_MOVES_SIZE


class Engine:  # class for the engine
    def __init__(self, size: int = 4000, p: float = 0.75, reset_table=True) -> None:
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
                ("move", object),
            ]
        )
        self.t_table = np.zeros(self.size, dtype=dtype)
        self.percentage = p
        self.num_elements = 0
        self.important_moves = dict()
        self.killer_moves = defaultdict(lambda: OrderedDict())
        self.max_size = IMP_MOVES_SIZE
        self.zobrist_table = np.random.randint(
            0, 2**63 - 1, size=(9, 9, 3), dtype=np.int64
        )

    def alpha_beta_Negamax(self, board: Board, depth, alpha, beta):
        old_alpha = alpha
        zobrist_key = board.zobrist
        board.depth = depth

        ttEntry = self.get(zobrist_key)

        if ttEntry != {"depth": -1} and ttEntry["depth"] >= depth:

            if ttEntry["flag"] == "EXACT":
                new_board = board.create_new_board(ttEntry)
                new_board.zobrist = self.zobrist_hash(new_board)

                return ttEntry["score"], new_board

            else:
                if ttEntry["flag"] == "LOWER_BOUND":
                    alpha = max(alpha, ttEntry["score"])
                    board.lower_bound = alpha
                if ttEntry["flag"] == "UPPER_BOUND":
                    beta = min(beta, ttEntry["score"])
                    board.upper_bound = beta

                if alpha >= beta:

                    return

        if depth == 0:
            board.utility_function()
            board.score = board.utility
            return board.score, board

        score = -math.inf
        boards = self.next_moves(board)
        for b, piece, move in boards:

            value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)

            value = -value
            if value > score:
                score = value
                board.best_board = b
                board.best_move = (piece, move)

            alpha = max(alpha, score)

            if alpha >= beta:
                self.add_move((board.zobrist, b.zobrist))
                self.add_killer_move(depth, (board.zobrist, b.zobrist))
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
        self.insert(board, board.best_move)

        return score, board.best_board

    def next_moves(self, board: Board):
        boards = []
        board.handle_capture()
        turn = board.turn
        imp_boards = []
        killer_moves = []
        for piece in board.pieces:

            piece.is_selected = True
            if piece.team == board.turn:
                for move in piece.possible_moves:
                    if piece.possible_moves[move] == True:

                        new_board_obj = Board(team=turn)
                        new_board_obj.pieces = copy.deepcopy(board.pieces)
                        new_board_obj.change_board()
                        new_board_obj.move_pieces(move[0], move[1])
                        new_board_obj.zobrist = self.zobrist_hash(new_board_obj)
                        new_board_obj.turn = 1 if board.turn == 2 else 2

                        if (
                            board.depth in self.killer_moves
                            and (board.zobrist, new_board_obj.zobrist)
                            in self.killer_moves[board.depth]
                        ):
                            killer_moves.append((new_board_obj, piece, move))

                        elif (
                            board.zobrist,
                            new_board_obj.zobrist,
                        ) in self.important_moves:
                            imp_boards.append((new_board_obj, piece, move))

                        else:
                            boards.append((new_board_obj, piece, move))

            piece.is_selected = False
            imp_boards = sorted(
                imp_boards,
                key=lambda item: self.important_moves.get(
                    (board.zobrist, item[0].zobrist), float("-inf")
                ),
                reverse=True,
            )
        # print(killer_moves + imp_boards + boards)
        return killer_moves + imp_boards + boards

    def add_move(self, move):
        if move not in self.important_moves:
            if len(self.important_moves) >= self.max_size:
                self.trim_important_moves()
            self.important_moves[move] = 0  # Aggiungi la mossa se non esiste
        else:
            self.important_moves[move] += 1  # Incrementa il contatore se esiste già

    def trim_important_moves(self):
        important_moves_keys = list(self.important_moves.keys())
        mid_index = len(important_moves_keys) // 2
        self.important_moves = {
            key: self.important_moves[key] for key in important_moves_keys[mid_index:]
        }
        print("Trimming important moves")

    def add_killer_move(self, depth, move):
        if depth not in self.killer_moves:
            self.killer_moves[depth] = {}

        if move in self.killer_moves[depth]:
            self.killer_moves[depth][move] += 1
        else:
            self.killer_moves[depth][move] = 1
        if len(self.killer_moves[depth]) > self.max_size:
            self.killer_moves[depth] = OrderedDict(
                sorted(
                    self.killer_moves[depth].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:4]
            )

    def zobrist_hash(self, board: Board):
        zobrist_value = 0
        for row in range(9):
            for col in range(9):
                if board.board[row, col] != 0:
                    value = board.board[row, col]
                    zobrist_value ^= self.zobrist_table[row, col, value]

        return zobrist_value

    def hash_index(self, zobrist_value):
        return zobrist_value % self.size

    def insert(self, board: Board, best_move: Board):
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

    """
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
    """

    def think(self, board: Board, depth, alpha, beta):

        old_pieces = copy.deepcopy(board.pieces)
        start_time = time.time()
        board.zobrist = self.zobrist_hash(board)
        _, best_board = self.alpha_beta_Negamax(board, depth, alpha, beta)
        best_board.old_pieces = old_pieces
        board = copy.deepcopy(best_board)

        if self.reset_table:
            self.clear_table()
        elapsed_time = time.time() - start_time

        print(f"Tempo impiegato da alpha_beta_Negamax: {elapsed_time:.4f} secondi")

        return board
