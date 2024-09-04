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
        self.is_possible = {
            (self.i - 1, self.j): False,
            (self.i - 1, self.j - 1): False,
            (self.i - 1, self.j + 1): False,
        }

    def select(self):
        self.is_selected = True

    def deselect(self):
        self.is_selected = False

    def is_possible(self, board):  # select possible moves

        if board[self.i - 1][self.j] == 0:
            self.is_possible[(self.i - 1, self.j)] = True
        if board[self.i - 1][self.j - 1] == 0:
            self.is_possible[(self.i - 1, self.j)] = True
        if board[self.i - 1][self.j + 1] == 0:
            self.is_possible[(self.i - 1, self.j)] = True


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


class PygameEnviroment(Board):
    def __init__(self, board: Board) -> None:
        super().__init__()
        self.board = board

    def show(self, screen, screen_size, cell_size):
        pieces = self.board.pieces
        print(pieces, "hii")
        for piece in pieces:
            print(piece.i, piece.j, piece.team)
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
