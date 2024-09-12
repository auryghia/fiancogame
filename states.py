from typing import List
import numpy as np
import pygame
import math
import copy
import random


class Piece:

    def __init__(self, i, j, team) -> None:
        self.i = i
        self.j = j
        self.old_i = None
        self.old_j = None
        self.id = None
        self.team = team
        self.opp_team = 1 if team == 2 else 2
        self.is_king = False
        self.is_selected = False
        self.possible_moves = {
            (self.i - 2, self.j - 2): False,
            (self.i - 2, self.j + 2): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - 1, self.j): False,
            (self.i + 2, self.j + 2): False,
            (self.i + 2, self.j - 2): False,
            (self.i + 1, self.j): False,
        }

    def possible_moves_up(self, board):
        # Reset delle mosse possibili

        # Controllo dei movimenti di base
        self.possible_moves = {
            (self.i - 2, self.j - 2): False,
            (self.i - 2, self.j + 2): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - 1, self.j): False,
            (self.i + 2, self.j + 2): False,
            (self.i + 2, self.j - 2): False,
            (self.i + 1, self.j): False,
        }
        if self.i - 1 >= 0:

            if board[self.i - 1][self.j] == 0:
                self.possible_moves[(self.i - 1, self.j)] = True

            if self.j - 1 >= 0 and board[self.i][self.j - 1] == 0:
                self.possible_moves[(self.i, self.j - 1)] = True

            if self.j + 1 <= 8 and board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True

        if self.i - 2 >= 0:
            if (
                self.j - 2 >= 0
                and board[self.i - 1][self.j - 1] == self.opp_team
                and board[self.i - 2][self.j - 2] == 0
            ):

                self.possible_moves[(self.i - 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i - 2, self.j - 2)] = True

            if (
                self.j + 2 <= 8
                and board[self.i - 1][self.j + 1] == self.opp_team
                and board[self.i - 2][self.j + 2] == 0
            ):

                self.possible_moves[(self.i - 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i - 2, self.j + 2)] = True

        if self.i - 1 == 0 and board[self.i - 1][self.j] == 0:

            self.possible_moves[(self.i - 1, self.j)] = True
            for move in self.possible_moves:
                if move != (self.i - 1, self.j):
                    self.possible_moves[move] = False

    def possible_moves_down(self, board):
        self.possible_moves = {
            (self.i - 2, self.j - 2): False,
            (self.i - 2, self.j + 2): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - 1, self.j): False,
            (self.i + 2, self.j + 2): False,
            (self.i + 2, self.j - 2): False,
            (self.i + 1, self.j): False,
        }

        if self.i + 1 <= 8:
            if board[self.i + 1][self.j] == 0:

                self.possible_moves[(self.i + 1, self.j)] = True

            if self.j - 1 >= 0 and board[self.i][self.j - 1] == 0:

                self.possible_moves[(self.i, self.j - 1)] = True

            if self.j + 1 <= 8 and board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True

        if self.i + 2 <= 8:
            if (
                self.j - 2 >= 0
                and board[self.i + 1][self.j - 1] == self.opp_team
                and board[self.i + 2][self.j - 2] == 0
            ):
                self.possible_moves[(self.i + 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i + 2, self.j - 2)] = True

            if (
                self.j + 2 <= 8
                and board[self.i + 1][self.j + 1] == self.opp_team
                and board[self.i + 2][self.j + 2] == 0
            ):
                self.possible_moves[(self.i + 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i + 2, self.j + 2)] = True
        """
        if self.i + 1 == 8 and board[self.i + 1][self.j] == 0:
            self.possible_moves[(self.i + 1, self.j)] = True
            for move in self.possible_moves:
                if move != (self.i + 1, self.j):
                    self.possible_moves[move] = False
        """

    def move(self, i, j):

        self.i = i
        self.j = j


class Board:
    def __init__(self, team, pieces: List[Piece] = [], turn: int = 1) -> None:
        self.team = team
        self.pieces = pieces
        self.old_pieces = []
        self.board = np.zeros((9, 9), dtype=int)
        self.turn = turn
        self.score = -math.inf
        self.best_move = None
        self.dictionary = {}
        self.utility = 0
        self.zobrist = 0
        self.score = -math.inf
        self.upper_bound = math.inf
        self.lower_bound = -math.inf
        self.flag = None
        self.depth = 0

        self.old_moves_piece = None

    def number_creation(
        self,
    ):  # creation of all the possible random numbers for the zobrist hash
        for piece in self.pieces:
            for i in range(9):
                for j in range(9):

                    self.dictionary[(piece.id, i, j)] = random.randint(
                        0, 2**32 - 1
                    )  # controlla che questo numero sia abbastanza grande e che tutti i numeri siano effettivamente diversi

    def create_boards(
        self,
    ):  # initialize the board with the pieces and creation of the pieces
        l = 1
        number = 1
        for i in range(4):
            if i == 0:
                self.board[0, 0:9] = 2 if self.team == 1 else 1
                for col in range(9):
                    piece = Piece(0, col, 2 if self.team == 1 else 1)
                    self.pieces.append(piece)
                    piece.id = number
                    number += 1
            else:
                j, m = l, 9 - l - 1
                self.board[i, j] = 2 if self.team == 1 else 1
                self.board[i, m] = 2 if self.team == 1 else 1
                piece = Piece(i, j, 2 if self.team == 1 else 1)
                piece.id = number
                number += 1
                self.pieces.append(piece)
                piece = Piece(i, m, 2 if self.team == 1 else 1)
                piece.id = number
                number += 1
                self.pieces.append(piece)
                l += 1
        l = 3
        for i in range(5, 9):
            if i == 8:
                self.board[8, 0:9] = 1 if self.team == 1 else 2
                for col in range(9):
                    piece = Piece(8, col, 1 if self.team == 1 else 2)
                    piece.id = number
                    number += 1
                    self.pieces.append(piece)
            else:
                p, f = l, 9 - l - 1
                self.board[i, p] = 1 if self.team == 1 else 2
                self.board[i, f] = 1 if self.team == 1 else 2
                piece = Piece(i, p, 1 if self.team == 1 else 2)
                piece.id = number
                number += 1
                self.pieces.append(piece)
                piece = Piece(i, f, 1 if self.team == 1 else 2)
                piece.id = number
                number += 1
                self.pieces.append(piece)
                l -= 1

    def change_board(self):  # change the board with the new pieces
        self.board = np.zeros((9, 9), dtype=int)
        for piece in self.pieces:
            self.board[piece.i, piece.j] = piece.team

    def utility_function(
        self,
    ):  # utility function for the board
        if self.turn == self.team:  # if it's the turn of the player down
            num_opponent_pieces = 0
            num_pieces = 0
            position_score = 0
            opponent_team = 1 if self.team == 2 else 2
            for piece in self.pieces:
                if piece.team == opponent_team:
                    num_opponent_pieces += 1

                else:
                    num_pieces += 1
                    position_score -= 8 - piece.i

                    self.utility = position_score - num_opponent_pieces + num_pieces

        else:  # if it's the turn of the player up
            num_opponent_pieces = 0
            num_pieces = 0
            position_score = 0
            opponent_team = 1 if self.team == 2 else 2
            for piece in self.pieces:
                if piece.team == self.team:
                    num_opponent_pieces += 1

                else:
                    num_pieces += 1
                    position_score += piece.i
                    self.utility = position_score - num_opponent_pieces + num_pieces


class Engine:  # class for the engine
    def __init__(self) -> None:
        self.proof = 3
        self.dictionary = {}
        self.zobrist_keys = []
        self.size = 4000
        self.t_table = [[] for _ in range(self.size)]
        self.num_elements = 0

    def zobrist_hash(self, board: Board):
        zobrist_value = 0

        for piece in board.pieces:
            zobrist_value ^= board.dictionary[(piece.id, piece.i, piece.j)]

        return zobrist_value

    def hash_index(self, zobrist_value):
        return zobrist_value % self.size

    def insert(self, board: Board):
        if self.num_elements / self.size > 0.75:
            self._resize()
        board.zobrist = self.zobrist_hash(board)
        index = self.hash_index(board.zobrist)
        self.t_table[index].append(
            (
                board.zobrist,
                {
                    "score": board.score,
                    "flag": board.flag,
                    "upper_bound": board.upper_bound,
                    "lower_bound": board.lower_bound,
                    "depth": board.depth,
                    "board": board,
                },
            )
        )
        self.num_elements += 1

    def get(self, key):
        index = self.hash_index(key)

        for k, v in self.t_table[index]:
            if k == key:
                return v
        return {"depth": -1}

    def _resize(self):
        new_size = self.size * 2
        new_table = [[] for _ in range(new_size)]
        for bucket in self.t_table:
            for key, value in bucket:
                new_index = hash(key) % new_size
                new_table[new_index].append((key, value))
        self.table = new_table
        self.size = new_size

    def alpha_beta_Negamax(self, board: Board, depth, alpha, beta):
        old_alpha = alpha
        zobrist_key = board.zobrist
        ttEntry = self.get(zobrist_key)

        if ttEntry and ttEntry["depth"] >= depth:
            if ttEntry["flag"] == "EXACT":
                return ttEntry["score"], ttEntry["board"]
            elif ttEntry["flag"] == "LOWER_BOUND":
                alpha = max(alpha, ttEntry["score"])
                board.lower_bound = alpha
            elif ttEntry["flag"] == "UPPER_BOUND":
                beta = min(beta, ttEntry["score"])
                board.upper_bound = beta

            if alpha >= beta:
                return ttEntry["score"], board

        if depth == 0:
            board.utility_function()
            board.score = board.utility
            return board.score, board

        score = -math.inf
        best_board = None
        boards = self.next_moves(board)

        for b in boards:
            value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)
            value = -value

            if value > score:
                score = value
                best_board = copy.deepcopy(b)
                best_board.score = value
                best_board.upper_bound = alpha
                best_board.lower_bound = beta
                best_board.depth = depth

            alpha = max(alpha, score)

            if alpha >= beta:
                break

        if score <= old_alpha:
            board.flag = "UPPER_BOUND"
        elif score >= beta:
            board.flag = "LOWER_BOUND"
        else:
            board.flag = "EXACT"

        board.best_move = best_board
        self.insert(board)

        return score, best_board

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
                    piece.possible_moves_up(board.board)
                else:
                    piece.possible_moves_down(board.board)

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
                    if p.team == board.team:
                        p.possible_moves_up(board.board)
                    else:
                        p.possible_moves_down(board.board)

                    for move in p.possible_moves:
                        if abs(move[0] - p.i) != 2 or abs(move[1] - p.j) != 2:
                            p.possible_moves[move] = False

        return board

    def next_moves(self, board: Board):
        boards = []

        for piece in board.pieces:

            piece.is_selected = True

            if piece.team == board.turn:

                board = self.handle_capture(board)

                for move in piece.possible_moves:
                    if piece.possible_moves[move] == True:

                        new_board_obj = copy.deepcopy(board)
                        new_board_obj = self.move_pieces(
                            new_board_obj, move[0], move[1]
                        )

                        new_board_obj.turn = 1 if board.turn == 2 else 2

                        boards.append(new_board_obj)

            piece.is_selected = False

        return boards


class PygameEnviroment:  # class for the pygame enviroment
    def __init__(
        self,
        board_obj: Board,
        player1: str = "automatic",
        player2: str = "manually",
    ) -> None:
        self.board_obj = board_obj
        self.player1 = player1
        self.player2 = player2

    def show(self, screen, screen_size, grid_size, cell_size):
        pieces = self.board_obj.pieces
        font = pygame.font.Font(None, 36)
        letters = "abcdefghi"
        numbers_team_1 = "987654321"  # team 1
        numbers_team_2 = "123456789"  # team 2
        pink_color = (255, 105, 180)

        numbers = numbers_team_1 if self.board_obj.team == 1 else numbers_team_2
        for piece in pieces:

            color = (0, 0, 0)
            if piece.team == 1 or piece.team == 2:
                pygame.draw.circle(
                    screen,
                    color,
                    (
                        piece.j * cell_size + cell_size // 2,
                        piece.i * cell_size + cell_size // 2,
                    ),
                    cell_size // 2 - 5,
                    4 if piece.team == 1 else 0,
                )

            if piece.is_selected:
                for move in piece.possible_moves:
                    if piece.possible_moves[move]:
                        center = (
                            move[1] * cell_size + cell_size // 2,
                            move[0] * cell_size + cell_size // 2,
                        )
                        pygame.draw.circle(screen, (0, 255, 0), center, 15)

        for x in range(0, grid_size, cell_size):
            for y in range(0, grid_size, cell_size):
                rect = pygame.Rect(x, y, cell_size, cell_size)
                pygame.draw.rect(screen, pink_color, rect, 1)

                col = x // cell_size
                row = y // cell_size
                notation = f"{letters[col]}{numbers[row]}"

                text = font.render(notation, True, (0, 0, 0))
                text_rect = text.get_rect(
                    center=(x + cell_size // 2, y + cell_size // 2)
                )
                screen.blit(text, text_rect)

        player_text = "White's Turn" if self.board_obj.turn == 1 else "Black's Turn"
        player_text_rendered = font.render(player_text, True, (0, 0, 0))
        player_text_rect = player_text_rendered.get_rect(
            center=(screen_size[0] - 80, screen_size[1] - 20)
        )
        screen.blit(player_text_rendered, player_text_rect)
