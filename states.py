from typing import List
import numpy as np
import pygame
import math
import copy


class Player:

    def __init__(self, team: int = 1) -> None:

        self.team = team


class Piece:

    def __init__(self, i, j, team) -> None:
        self.i = i
        self.j = j
        self.old_i = None
        self.old_j = None
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
        # Verifica che l'indice superiore e laterale non siano fuori dai limiti
        if self.i - 2 >= 0 and self.j - 2 >= 0 and self.j + 2 <= 8:

            if (
                board[self.i - 1][self.j - 1] == self.opp_team
                and board[self.i - 2][self.j - 2] == 0
            ):
                self.possible_moves[(self.i - 2, self.j - 2)] = True
            if (
                board[self.i - 1][self.j + 1] == self.opp_team
                and board[self.i - 2][self.j + 2] == 0
            ):
                self.possible_moves[(self.i - 2, self.j + 2)] = True

        # Controlla se è possibile muovere a sinistra, destra o in avanti senza saltare
        if self.i - 1 >= 0:
            # Muovi a sinistra se la cella è vuota
            if self.j - 1 >= 0 and board[self.i - 1][self.j - 1] == 0:
                self.possible_moves[(self.i - 1, self.j - 1)] = True
            # Muovi a destra se la cella è vuota
            if self.j + 1 <= 8 and board[self.i - 1][self.j + 1] == 0:
                self.possible_moves[(self.i - 1, self.j + 1)] = True
            # Muovi in avanti se la cella è vuota
            if board[self.i - 1][self.j] == 0:
                self.possible_moves[(self.i - 1, self.j)] = True

    def possible_moves_down(self, board):
        if self.i + 1 <= 8 and self.j - 1 >= 0 and self.j + 1 <= 8:
            if (
                board[self.i + 1][self.j - 1] == self.opp_team
                and board[self.i + 2][self.j - 2] == 0
            ) or (
                board[self.i + 1][self.j + 1] == self.opp_team
                and board[self.i + 2][self.j + 2] == 0
            ):
                if (
                    board[self.i + 1][self.j - 1] == self.opp_team
                    and board[self.i + 2][self.j - 2] == 0
                ):
                    self.possible_moves[(self.i + 2, self.j - 2)] = True
                if (
                    board[self.i + 1][self.j + 1] == self.opp_team
                    and board[self.i + 2][self.j + 2] == 0
                ):
                    self.possible_moves[(self.i + 2, self.j + 2)] = True
        else:
            if self.i + 1 <= 8 and self.j - 1 >= 0 and self.j + 1 <= 8:
                if board[self.i][self.j + 1] == 0 and self.j + 1 <= 8:
                    self.possible_moves[(self.i, self.j + 1)] = True
                if board[self.i][self.j - 1] == 0 and self.j - 1 >= 0:
                    self.possible_moves[(self.i, self.j - 1)] = True
                if board[self.i + 1][self.j] == 0 and self.i + 1 <= 8:

                    self.possible_moves[(self.i + 1, self.j)] = True

    def move(self, i, j):
        self.i = i
        self.j = j
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


class Board:
    def __init__(self, player: Player, pieces: List[Piece] = [], turn: int = 1) -> None:
        self.team = player.team
        self.player = player
        self.pieces = pieces
        self.board = np.zeros((9, 9), dtype=int)
        self.turn = turn
        self.score = -math.inf
        self.best_move = None
        self.utility = 0

    def create_boards(
        self,
    ):
        l = 1

        for i in range(4):
            if i == 0:
                self.board[0, 0:9] = 2 if self.team == 1 else 1
                for col in range(9):
                    piece = Piece(0, col, 2 if self.team == 1 else 1)
                    self.pieces.append(piece)
            else:
                j, m = l, 9 - l - 1
                self.board[i, j] = 2 if self.team == 1 else 1
                self.board[i, m] = 2 if self.team == 1 else 1
                piece = Piece(i, j, 2 if self.team == 1 else 1)
                self.pieces.append(piece)
                piece = Piece(i, m, 2 if self.team == 1 else 1)
                self.pieces.append(piece)
                l += 1
        l = 3
        for i in range(5, 9):
            if i == 8:
                self.board[8, 0:9] = 1 if self.team == 1 else 2
                for col in range(9):
                    piece = Piece(8, col, 1 if self.team == 1 else 2)
                    self.pieces.append(piece)
            else:
                p, f = l, 9 - l - 1
                self.board[i, p] = 1 if self.team == 1 else 2
                self.board[i, f] = 1 if self.team == 1 else 2
                piece = Piece(i, p, 1 if self.team == 1 else 2)
                self.pieces.append(piece)
                piece = Piece(i, f, 1 if self.team == 1 else 2)
                self.pieces.append(piece)
                l -= 1

    def move_pieces(self, i, j):
        for piece in self.pieces:
            if piece.is_selected:
                self.board[piece.i, piece.j] = 0

                self.old_i, self.old_j = piece.i, piece.j

                piece.move(i, j)

                if abs(i - self.old_i) == 2:

                    mid_i = (i + self.old_i) // 2
                    mid_j = (j + self.old_j) // 2

                    self.board[mid_i, mid_j] = 0

                    for p in self.pieces:
                        if p.i == mid_i and p.j == mid_j:
                            self.pieces.remove(p)
                            break
                self.board[piece.i, piece.j] = piece.team

    def next_moves(self):  # trova la combinazione di mosse possibili
        boards = []

        for piece in self.pieces:
            piece.is_selected = True
            if piece.team == self.turn:
                if piece.team == self.team:
                    piece.possible_moves_up(self.board)
                else:
                    piece.possible_moves_down(self.board)

                for move in piece.possible_moves:

                    if piece.possible_moves[move] == True:

                        new_board = Board(
                            self.player, copy.deepcopy(self.pieces), self.turn
                        )

                        new_board.board = copy.deepcopy(self.board)

                        new_board.move_pieces(move[0], move[1])

                        boards.append(new_board)
            piece.is_selected = False

        return boards

    def utility_function(
        self,
    ):  # calcola la funzione di utilitá per ogni board sia dal punto di vista del giocatore che dell' avversario
        utility = 0
        if self.turn == self.team:  # se é il mio turno
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

        else:  # if it's the opponent's turn
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


class AlphaBeta:
    def __init__(self, board: Board, depth: int, alpha, beta) -> None:
        self.board = board
        self.depth = depth
        self.alpha = alpha
        self.beta = beta

    def alpha_beta_Negamax(self, board):

        if self.depth == 0:
            board.utility_function()
            return board.utility
        score = -math.inf
        boards = self.board.next_moves()

        # return the utility function
        for b in boards:
            # board é un oggetto di tipo Board
            alpha_beta = AlphaBeta(b, self.depth - 1, -self.beta, -self.alpha)
            value = -alpha_beta.alpha_beta_Negamax()
            if value > self.beta:
                self.score = value
                self.board = self.board
            if score > self.alpha:
                self.alpha = self.score

            if self.alpha >= self.beta:
                break

        return score


class PygameEnviroment(Board):
    def __init__(
        self,
        board_obj: Board,
        player,
        player1: str = "automatic",
        player2: str = "manually",
    ) -> None:
        super().__init__(player)
        self.board_obj = board_obj
        self.player1 = player1
        self.player2 = player2

    def show(self, screen, screen_size, cell_size):
        pieces = self.board_obj.pieces
        font = pygame.font.Font(None, 36)
        letters = "abcdefghi"
        numbers_team_1 = "987654321"  # team 1
        numbers_team_2 = "123456789"  # team 2
        numbers = numbers_team_1 if self.team == 1 else numbers_team_2

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

        for x in range(0, screen_size, cell_size):
            for y in range(0, screen_size, cell_size):
                rect = pygame.Rect(x, y, cell_size, cell_size)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

                col = x // cell_size
                row = y // cell_size
                notation = f"{letters[col]}{numbers[row]}"

                text = font.render(notation, True, (0, 0, 0))
                text_rect = text.get_rect(
                    center=(x + cell_size // 2, y + cell_size // 2)
                )
                screen.blit(text, text_rect)
