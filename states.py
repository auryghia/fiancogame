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
            (self.i - 1, self.j): False,
            (self.i - 2, self.j + 2): False,
            (self.i - 2, self.j - 2): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i + 1, self.j): False,
            (self.i + 2, self.j - 2): False,
            (self.i + 2, self.j + 2): False,
        }

    def possible_moves_f(self, board, direction):

        # direction = -1 for 'up', 1 for 'down'
        self.possible_moves = {
            (self.i + direction, self.j): False,
            (self.i + 2 * direction, self.j - 2): False,
            (self.i + 2 * direction, self.j + 2): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - direction, self.j): False,
            (self.i - 2 * direction, self.j + 2): False,
            (self.i - 2 * direction, self.j - 2): False,
        }

        # Check simple forward move
        if 0 <= self.i + direction <= 8:
            if board[self.i + direction][self.j] == 0:
                self.possible_moves[(self.i + direction, self.j)] = True

            if self.j - 1 >= 0 and board[self.i][self.j - 1] == 0:
                self.possible_moves[(self.i, self.j - 1)] = True

            if self.j + 1 <= 8 and board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True

        # Check capture moves
        if 0 <= self.i + 2 * direction <= 8:
            if (
                self.j - 2 >= 0
                and board[self.i + direction][self.j - 1] == self.opp_team
                and board[self.i + 2 * direction][self.j - 2] == 0
            ):
                self.possible_moves[(self.i + direction, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i + 2 * direction, self.j - 2)] = True

            if (
                self.j + 2 <= 8
                and board[self.i + direction][self.j + 1] == self.opp_team
                and board[self.i + 2 * direction][self.j + 2] == 0
            ):
                self.possible_moves[(self.i + direction, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i + 2 * direction, self.j + 2)] = True

        # Special case for edge of the board
        if direction == -1 and self.i - 1 == 0 and board[self.i - 1][self.j] == 0:
            self.possible_moves[(self.i - 1, self.j)] = True
            for move in self.possible_moves:
                if move != (self.i - 1, self.j):
                    self.possible_moves[move] = False

    def move(self, i, j):
        self.i = i
        self.j = j


class Board:
    def __init__(
        self,
        team,
        turn: int = 1,
        players: dict = {1: "automatic", 2: "manually"},
    ) -> None:
        self.team = team
        self.pieces: List[Piece] = []
        self.old_pieces = []
        self.board = np.zeros((9, 9), dtype=int)
        self.turn = turn
        self.players = players
        self.score = -math.inf
        self.best_move = None
        self.best_board = None
        self.dictionary = {}
        self.utility = 0
        self.zobrist = 0
        self.score = -math.inf
        self.upper_bound = math.inf
        self.lower_bound = -math.inf
        self.flag = None
        self.depth = 0
        self.old_moves_piece = None

    """
    def order_pieces(self):
        self.pieces = sorted(self.pieces, key=lambda x: x.i, reverse=True)
    """

    def number_creation(
        self,
    ):  # creation of all the possible random numbers for the zobrist hash
        for piece in self.pieces:
            for i in range(9):
                for j in range(9):

                    self.dictionary[(piece.id, i, j)] = random.randint(0, 2**32 - 1)

    def create_boards(
        self,
    ):
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

    def change_board(self):
        self.board = np.zeros((9, 9), dtype=int)
        for piece in self.pieces:
            self.board[piece.i, piece.j] = piece.team

    def utility_function(self):
        num_opponent_pieces = 0
        num_pieces = 0
        position_score = 0
        progress_weight = 10
        pieces_weight = 2
        advanced_position_weight = 3
        advanced_count = 0
        for piece in self.pieces:
            if (
                piece.i == 0
                and piece.team == self.team
                or piece.i == 8
                and piece.team != self.team
            ):
                self.utility = 100000 if piece.team == self.team else -100000
                return

            if piece.team == self.team:
                num_pieces += 1
                position_score += piece.i if self.turn != self.team else -8 + piece.i

            else:
                num_opponent_pieces += 1

        self.utility = position_score * progress_weight
        self.utility -= (num_opponent_pieces + num_pieces) * pieces_weight

    def undo_move(self):
        self.turn = 1 if self.turn == 2 else 2
        pieces = copy.deepcopy(self.pieces)
        self.pieces = copy.deepcopy(self.old_pieces)
        self.old_pieces = pieces
        self.change_board()


class PygameEnviroment:  # class for the pygame enviroment
    def __init__(self, board_obj: Board) -> None:
        self.board_obj = board_obj

    def show(self, screen, screen_size, grid_size, cell_size):
        pieces = self.board_obj.pieces
        font = pygame.font.Font(None, 36)
        letters = "abcdefghi"
        numbers_team_1 = "987654321"
        numbers_team_2 = "123456789"
        purple_color = (128, 0, 128)

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
                pygame.draw.rect(screen, purple_color, rect, 1)

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
