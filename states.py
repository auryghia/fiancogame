from typing import List
import numpy as np
import pygame
import math
import copy
import random
import heapq


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

    def possible_moves_up(self, board):

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
            (self.i + 1, self.j): False,
            (self.i + 2, self.j - 2): False,
            (self.i + 2, self.j + 2): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - 1, self.j): False,
            (self.i - 2, self.j + 2): False,
            (self.i - 2, self.j - 2): False,
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

    def move(self, i, j):

        self.i = i
        self.j = j


class Board:
    def __init__(
        self,
        team,
        pieces: List[Piece] = [],
        turn: int = 1,
        players: dict = {1: "automatic", 2: "manually"},
    ) -> None:
        self.team = team
        self.pieces = pieces
        self.old_pieces = []
        self.board = np.zeros((9, 9), dtype=int)
        self.turn = turn
        self.players = players
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
    ):
        # utility function for the board
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

                    self.utility = (
                        position_score * 10 - (num_opponent_pieces + num_pieces) * 2
                    )

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
                    self.utility = (
                        position_score * 10 - (num_opponent_pieces + num_pieces) * 2
                    )


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
