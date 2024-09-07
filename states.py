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
            # Movimento verso l'alto
            if board[self.i - 1][self.j] == 0:
                self.possible_moves[(self.i - 1, self.j)] = True

            # Movimento verso sinistra
            if self.j - 1 >= 0 and board[self.i][self.j - 1] == 0:
                self.possible_moves[(self.i, self.j - 1)] = True

            # Movimento verso destra
            if self.j + 1 <= 8 and board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True

        # Controllo delle catture obbligatorie
        if self.i - 2 >= 0:
            # Salto diagonale a sinistra
            if (
                self.j - 2 >= 0
                and board[self.i - 1][self.j - 1] == self.opp_team
                and board[self.i - 2][self.j - 2] == 0
            ):
                self.possible_moves[(self.i - 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i - 2, self.j - 2)] = True

            # Salto diagonale a destra
            if (
                self.j + 2 <= 8
                and board[self.i - 1][self.j + 1] == self.opp_team
                and board[self.i - 2][self.j + 2] == 0
            ):
                self.possible_moves[(self.i + 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i - 2, self.j + 2)] = True

        # Se non è obbligatorio catturare, mantieni solo le mosse di movimento ordinario

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
        # Reset delle mosse possibili

        # Controllo dei movimenti di base
        if self.i + 1 <= 8:
            # Movimento verso il basso
            if board[self.i + 1][self.j] == 0:

                self.possible_moves[(self.i + 1, self.j)] = True

            # Movimento verso sinistra
            if self.j - 1 >= 0 and board[self.i][self.j - 1] == 0:

                self.possible_moves[(self.i, self.j - 1)] = True

            # Movimento verso destra
            if self.j + 1 <= 8 and board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True

        # Controllo delle catture obbligatorie

        if self.i + 2 <= 8:
            # Salto diagonale a sinistra
            if (
                self.j - 2 >= 0
                and board[self.i + 1][self.j - 1] == self.opp_team
                and board[self.i + 2][self.j - 2] == 0
            ):
                self.possible_moves[(self.i + 1, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i + 2, self.j - 2)] = True

            # Salto diagonale a destra
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
        self.old_i = self.i
        self.old_j = self.j
        self.i = i
        self.j = j


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

    def utility_function(
        self,
    ):
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
    def __init__(self) -> None:
        self.proof = 3

    def alpha_beta_Negamax(self, board: Board, depth, alpha, beta):
        if depth == 0:
            board.utility_function()
            return (
                board.utility,
                board,
            )

        score = -math.inf
        best_board = None
        boards = self.next_moves(board)

        for b in boards:
            # print(b.board, "board", b.utility_function())

            value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)

            value = -value
            # print(value, "value", b.board, "board")
            if value > score:

                score = value
                # print(b.board, "board")
                best_board = copy.deepcopy(b)
                # print(best_board.board, "board migliore fino ad ora")
                # print(
                #     score, best_board.board, depth, "score aggiornato"
                # )
            alpha = max(alpha, score)

            if alpha >= beta:
                break

        return (
            score,
            best_board,
        )

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
                b.turn = 2 if b.turn == 1 else 1

                piece.is_selected = False
        return b

    def next_moves(self, board: Board):
        boards = []

        for piece in board.pieces:

            piece.is_selected = True
            # print(
            #     piece.i,
            #     piece.j,
            #     piece.team,
            #     "piece",
            #     piece.is_selected,
            #     board.turn,
            #     "turno",
            # )
            if piece.team == board.turn:
                if piece.team == board.team:
                    piece.possible_moves_up(board.board)
                else:
                    piece.possible_moves_down(board.board)

                for move in piece.possible_moves:
                    if piece.possible_moves[move] == True:

                        new_board_obj = Board(
                            board.player, copy.deepcopy(board.pieces), board.turn
                        )
                        new_board_obj.board = copy.deepcopy(board.board)
                        # print(new_board_obj.board, "new_board")
                        new_board_obj = self.move_pieces(
                            new_board_obj, move[0], move[1]
                        )
                        # print(new_board_obj.board, "new_board_mossa")

                        boards.append(new_board_obj)

            piece.is_selected = False

        return boards


class PygameEnviroment:
    def __init__(
        self,
        board_obj: Board,
        player: Player,
        player1: str = "automatic",
        player2: str = "manually",
    ) -> None:
        self.board_obj = board_obj
        self.player = player
        self.player1 = player1
        self.player2 = player2

    def show(self, screen, screen_size, cell_size):
        pieces = self.board_obj.pieces
        font = pygame.font.Font(None, 36)
        letters = "abcdefghi"
        numbers_team_1 = "987654321"  # team 1
        numbers_team_2 = "123456789"  # team 2
        numbers = numbers_team_1 if self.board_obj.team == 1 else numbers_team_2
        # print(self.board)
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
