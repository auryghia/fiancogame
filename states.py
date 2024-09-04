from typing import List
import numpy as np
import pygame


class Piece:

    def __init__(self, i, j, team) -> None:
        self.i = i
        self.j = j
        self.team = team
        self.is_king = False
        self.is_selected = False
        self.possible_moves = {
            (self.i - 1, self.j - 1): False,
            (self.i - 1, self.j + 1): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - 1, self.j): False,
        }

    # def deselect(self):
    #     self.is_selected = False

    def possible_moves_f(self, board):  # select possible moves
        if (
            board[self.i - 1][self.j - 1] == 2 and board[self.i - 2][self.j - 2] == 0
        ) or (
            board[self.i - 1][self.j + 1] == 2 and board[self.i - 2][self.j + 2] == 0
        ):
            if (
                board[self.i - 1][self.j - 1] == 2
                and board[self.i - 2][self.j - 2] == 0
            ):
                self.possible_moves[(self.i - 2, self.j - 2)] = True
            if (
                board[self.i - 1][self.j + 1] == 2
                and board[self.i - 2][self.j + 2] == 0
            ):
                self.possible_moves[(self.i - 2, self.j + 2)] = True
        else:
            # Esegui se nessuno dei precedenti blocchi è vero
            if board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True
            if board[self.i][self.j - 1] == 0:
                self.possible_moves[(self.i, self.j - 1)] = True
            if board[self.i - 1][self.j] == 0:
                self.possible_moves[(self.i - 1, self.j)] = True

    # def select(self):
    #     self.is_selected = True

    def move(self, i, j):
        self.i = i
        self.j = j
        self.possible_moves = {
            (self.i - 1, self.j - 1): False,
            (self.i - 1, self.j + 1): False,
            (self.i, self.j - 1): False,
            (self.i, self.j + 1): False,
            (self.i - 1, self.j): False,
        }


class Board:
    def __init__(self, pieces: List[Piece] = []) -> None:

        self.pieces = pieces
        self.board = np.zeros((9, 9), dtype=int)

    def create_boards(
        self,
    ):
        l = 1
        for i in range(4):
            if i == 0:
                self.board[0, 0:9] = 2
                for col in range(9):
                    piece = Piece(
                        0, col, 2
                    )  # x=0 (riga 0), y=col (colonna corrente), valore 2
                    self.pieces.append(piece)
            else:
                j, m = l, 9 - l - 1
                self.board[i, j] = 2
                self.board[i, m] = 2
                piece = Piece(i, j, 2)
                self.pieces.append(piece)
                piece = Piece(i, m, 2)
                self.pieces.append(piece)
                l += 1
        l = 3
        for i in range(5, 9):
            if i == 8:
                self.board[8, 0:9] = 1
                for col in range(9):
                    piece = Piece(8, col, 1)  # x=8, y=col, valore 1
                    self.pieces.append(piece)
            else:
                p, f = l, 9 - l - 1
                self.board[i, p] = 1
                self.board[i, f] = 1
                piece = Piece(i, p, 1)
                self.pieces.append(piece)
                piece = Piece(i, f, 1)
                self.pieces.append(piece)
                l -= 1

    def move_pieces(self, i, j):
        for piece in self.pieces:
            if piece.is_selected:
                self.board[piece.i, piece.j] = 0
                piece.move(i, j)
                self.board[piece.i, piece.j] = piece.team


class PygameEnviroment(Board):
    def __init__(self, board_obj: Board) -> None:
        super().__init__()
        self.board_obj = board_obj
        self.board = self.board_obj.board

    def show(self, screen, screen_size, cell_size):
        pieces = self.board_obj.pieces

        for piece in pieces:
            if piece.team == 1:
                pygame.draw.circle(
                    screen,
                    (0, 0, 0),
                    (
                        piece.j * cell_size + cell_size // 2,
                        piece.i * cell_size + cell_size // 2,
                    ),
                    cell_size // 2 - 5,
                    4,
                )
            if piece.is_selected:

                for move in piece.possible_moves:
                    if piece.possible_moves[move]:
                        center = (
                            move[1] * cell_size + cell_size // 2,
                            move[0] * cell_size + cell_size // 2,
                        )
                        pygame.draw.circle(screen, (0, 255, 0), center, 15)

            elif piece.team == 2:
                pygame.draw.circle(
                    screen,
                    (0, 0, 0),
                    (
                        piece.j * cell_size + cell_size // 2,
                        piece.i * cell_size + cell_size // 2,
                    ),
                    cell_size // 2 - 5,
                )

        # for i in range(9): # Draw pieces
        #     for j in range(9):
        #         if self.board[i, j] == 1:

        #             pygame.draw.circle(
        #                 screen,
        #                 (0, 0, 0),
        #                 (j * cell_size + cell_size // 2, i * cell_size + cell_size // 2),
        #                 cell_size // 2 - 5,
        #                 4,
        #             )

        #         elif self.board[i, j] == 2:

        #             pygame.draw.circle(
        #                 screen,
        #                 (0, 0, 0),
        #                 (j * cell_size + cell_size // 2, i * cell_size + cell_size // 2),
        #                 cell_size // 2 - 5,
        #             )

        for x in range(0, screen_size, cell_size):  # draw grid
            for y in range(0, screen_size, cell_size):
                rect = pygame.Rect(x, y, cell_size, cell_size)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)
