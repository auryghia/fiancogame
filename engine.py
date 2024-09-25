from states import Board
import numpy as np
import math
import time
import copy
import heapq
from collections import defaultdict, OrderedDict
from parameters import IMP_MOVES_SIZE, ORDENING, TT
from bitstring import BitArray
import sys


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
        self.depth = 0

        dtype = np.dtype(
            [
                ("zobrist", np.str_),  # Se sono stringhe Unicode
                ("score", np.str_),  # Se i punteggi sono numeri
                ("flag", np.int64),  # Flag come intero
                ("upper_bound", np.str_),  # Se i limiti sono numeri
                ("lower_bound", np.str_),  # Se i limiti sono numeri
                ("depth", np.str_),  # Depth come intero
                ("best_move", object),  # Permette oggetti complessi
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
        if TT:
            print(self.t_table)
            old_alpha = alpha
            zobrist_key = board.zobrist
            board.depth = depth
            ttEntry = self.get(zobrist_key)
            default_entry = ("", "", 0, "", "", "", 0)

            if all(
                ttEntry[field] == default_entry[i]
                for i, field in enumerate(ttEntry.dtype.names)
            ):
                pass
            else:
                print("TTENTRY", ttEntry)
                depth_entry = self.binary_to_num(ttEntry["depth"])
                if ttEntry["flag"] == 0:
                    # print("Transposition table hit")
                    bestMove = ttEntry["best_move"]
                    bestMove = tuple(
                        self.binary_to_num(move) for move in (oi, oj, i, j)
                    )
                    newBoard = board.create_new_board(*bestMove)
                    newBoard.zobrist = self.zobrist_hash(newBoard)

                    return ttEntry["score"], newBoard
                elif ttEntry["flag"] == 2:

                    alpha = max(alpha, ttEntry["score"])
                    board.lower_bound = alpha
                elif ttEntry["flag"] == 3:
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
        if TT:
            board.flag = (
                1 if old_alpha < score < beta else (2 if score <= old_alpha else 3)
            )

        board.upper_bound = alpha
        board.lower_bound = beta
        board.best_move = bestMove
        board.score = score
        board.bestBoard = bestBoard

        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((board.zobrist, board.bestBoard.zobrist), score)

        if TT:
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
                                ORDENING["history_heuristic"] and board.zobrist,
                                newBoardObj.zobrist,
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
            self.sort_moves(killerMoves, board, self.killerMoves[board.depth])
        if ORDENING["history_heuristic"]:
            self.sort_moves(histHeuristic, board, self.histHeuristic)

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

                ("Trimming history")

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

    def num_to_binary(self, num):
        sign = "1" if num < 0 else "0"
        num = abs(num)

        # Se è un numero intero
        if num.is_integer():
            return sign + "{0:b}".format(int(num))

        # Parte intera
        integer_part = int(num)
        return sign + "{0:b}".format(integer_part)

    def binary_to_num(self, binary):
        print(binary, type(binary))
        b = BitArray(bin=binary)
        if binary[0] == "1":
            return -b
        else:
            return b

    def insert(self, board: Board):
        if self.num_elements == self.size:
            self.change_table()

        # board.zobrist = self.zobrist_hash(board)

        index = self.hash_index(board.zobrist)

        score = self.num_to_binary(board.score)
        upper_bound = self.num_to_binary(board.upper_bound)
        lower_bound = self.num_to_binary(board.lower_bound)
        best_move = tuple(self.num_to_binary(move) for move in board.best_move)
        depth = self.num_to_binary(board.depth)
        zobrist = self.num_to_binary(board.zobrist)
        # print(
        #     type(zobrist),
        #     type(score),
        #     type(upper_bound),
        #     type(lower_bound),
        #     type(depth),
        #     type(best_move),
        #     board.flag,
        # )

        self.t_table[index] = np.array(
            [
                (
                    zobrist,
                    score,
                    board.flag,
                    upper_bound,
                    lower_bound,
                    depth,
                    best_move,
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
        start_time = time.time()
        board.zobrist = self.zobrist_hash(board)
        score, bestBoard = self.alpha_beta_Negamax(board, depth, alpha, beta)
        board = copy.deepcopy(bestBoard)
        print(sys.getsizeof(self.t_table) / (1024 * 1024), "MB")
        if self.reset_table:
            self.clear_table()

        self.pruningMoves = dict()
        elapsed_time = time.time() - start_time

        print(f"Time taken by alpha_beta_Negamax: {elapsed_time:.4f} seconds")
        print(f"Number of moves: {board.move_number}")
        print(f"Score: {score}")
        print(f"depth: {depth}")

        return board
