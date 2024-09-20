from typing import List
import numpy as np
import pygame
import math
import copy
import random


class Piece:

    def __init__(self, i, j, team) -> None:
        """
        Initialize a game piece.

        :param i: Row position of the piece.
        :param j: Column position of the piece.
        :param team: Team number (1 or 2) the piece belongs to.
        """
        self.i: int = i  # Current row position
        self.j: int = j  # Current column position
        self.old_i: int = None  # Previous row position
        self.old_j: int = None  # Previous column position
        self.id: int = None  # Unique identifier for the piece
        self.team: int = team  # Team number
        self.opp_team: int = 1 if team == 2 else 2  # Opponent's team
        self.is_king: bool = False  # Flag for king status
        self.is_selected: bool = False  # Flag for selection status

        # Possible moves dictionary, initialized based on current position
        self.possible_moves: dict = self.initialize_possible_moves()

    def initialize_possible_moves(self) -> dict:
        """
        Initialize possible moves based on the current position.

        :return: Dictionary of possible moves with their validity.
        """
        return {
            (self.i - 1, self.j): False,  # Move up
            (self.i - 2, self.j + 2): False,  # Move up-right
            (self.i - 2, self.j - 2): False,  # Move up-left
            (self.i, self.j - 1): False,  # Move left
            (self.i, self.j + 1): False,  # Move right
            (self.i + 1, self.j): False,  # Move down
            (self.i + 2, self.j - 2): False,  # Move down-left
            (self.i + 2, self.j + 2): False,  # Move down-right
        }

    def possible_moves_f(self, board: List[List[int]], direction: int) -> None:
        """
        Calculate possible moves for the piece based on its current position and the direction of movement.

        :param board: The current state of the game board.
        :param direction: The direction of movement (1 for down, -1 for up).
        """
        # Initialize possible moves dictionary
        self.possible_moves = {
            (self.i + direction, self.j): False,  # Simple forward move
            (self.i + 2 * direction, self.j - 2): False,  # Capture move (left)
            (self.i + 2 * direction, self.j + 2): False,  # Capture move (right)
            (self.i, self.j - 1): False,  # Move left
            (self.i, self.j + 1): False,  # Move right
            (self.i - direction, self.j): False,  # Backward move
            (self.i - 2 * direction, self.j + 2): False,  # Backward capture (right)
            (self.i - 2 * direction, self.j - 2): False,  # Backward capture (left)
        }

        # Check simple forward move
        if 0 <= self.i + direction <= 8:
            if board[self.i + direction][self.j] == 0:
                self.possible_moves[(self.i + direction, self.j)] = True

            # Check adjacent horizontal moves
            if self.j - 1 >= 0 and board[self.i][self.j - 1] == 0:
                self.possible_moves[(self.i, self.j - 1)] = True

            if self.j + 1 <= 8 and board[self.i][self.j + 1] == 0:
                self.possible_moves[(self.i, self.j + 1)] = True

        # Check capture moves
        if 0 <= self.i + 2 * direction <= 8:
            # Check left capture
            if (
                self.j - 2 >= 0
                and board[self.i + direction][self.j - 1] == self.opp_team
                and board[self.i + 2 * direction][self.j - 2] == 0
            ):
                self.possible_moves[(self.i + direction, self.j)] = False
                self.possible_moves[(self.i, self.j - 1)] = False
                self.possible_moves[(self.i + 2 * direction, self.j - 2)] = True

            # Check right capture
            if (
                self.j + 2 <= 8
                and board[self.i + direction][self.j + 1] == self.opp_team
                and board[self.i + 2 * direction][self.j + 2] == 0
            ):
                self.possible_moves[(self.i + direction, self.j)] = False
                self.possible_moves[(self.i, self.j + 1)] = False
                self.possible_moves[(self.i + 2 * direction, self.j + 2)] = True

        # Special case for edge of the board
        if direction == -1 and self.i - 1 == 0 and board[self.i - 1][self.j] == 0:
            self.possible_moves[(self.i - 1, self.j)] = True
            # Invalidate all other moves
            for move in self.possible_moves:
                if move != (self.i - 1, self.j):
                    self.possible_moves[move] = False

    def move(self, i: int, j: int) -> None:
        """
        Update the position of the piece.

        :param i: The new row index of the piece.
        :param j: The new column index of the piece.
        :raises ValueError: If the new position is out of bounds or invalid.
        """
        if not (0 <= i < 9) or not (0 <= j < 9):
            raise ValueError(
                "New position must be within the bounds of the board (0-8)."
            )

        self.i = i
        self.j = j


class Board:
    def __init__(
        self,
        team,
        turn: int = 1,
        players: dict = {1: "automatic", 2: "manually"},
    ) -> None:
        # Configuration
        self.team = team
        self.players = players

        # Game state
        self.turn = turn
        self.pieces: List[Piece] = []
        self.old_pieces = []
        self.old_moves_piece = None
        self.capture_available = False

        # Game board
        self.board = np.zeros((9, 9), dtype=int)

        # Score and utility
        self.score = -math.inf
        self.utility = 0
        self.best_move = None
        self.best_board = None

        # Search bounds
        self.upper_bound = math.inf
        self.lower_bound = -math.inf

        # Auxiliary variables
        self.zobrist = 0
        self.flag = None
        self.depth = 0

    """
    def order_pieces(self):
        self.pieces = sorted(self.pieces, key=lambda x: x.i, reverse=True)
    """

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

    def create_new_board(self, ttEntry):

        new_board = Board(team=self.turn)
        new_board.pieces = copy.deepcopy(self.pieces)
        new_board.change_board()
        for piece in new_board.pieces:
            piece_to_move = ttEntry["move"][0]
            if piece.id == piece_to_move.id:
                piece.is_selected = True
                new_board.move_pieces(ttEntry["move"][1][0], ttEntry["move"][1][1])
                piece.is_selected = False
        new_board.turn = 1 if self.turn == 2 else 2
        return new_board

    def count_threats(self, piece):
        num_threats = 0
        direction = -1 if piece.team == self.team else 1

        if (
            self.board[piece.i + direction, piece.j + direction] == 2
            if piece.team == 1
            else 1
        ):
            num_threats += 1
        return num_threats

    def move_pieces(self, i, j):
        for piece in self.pieces:

            if piece.is_selected:

                self.board[piece.i, piece.j] = 0

                piece.old_i, piece.old_j = piece.i, piece.j

                piece.move(i, j)

                if abs(i - piece.old_i) == 2:

                    mid_i = (i + piece.old_i) // 2
                    mid_j = (j + piece.old_j) // 2

                    self.board[mid_i, mid_j] = 0

                    for p in self.pieces:
                        if p.i == mid_i and p.j == mid_j:
                            self.pieces.remove(p)
                            break
                self.board[piece.i, piece.j] = piece.team

                piece.is_selected = False

    def handle_capture(self):
        self.capture_available = False

        for piece in self.pieces:
            if piece.team == self.turn:
                if piece.team == self.team:
                    piece.possible_moves_f(self.board, -1)
                else:
                    piece.possible_moves_f(self.board, +1)

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
                    self.capture_available = True
            if self.capture_available:
                for p in self.pieces:
                    if p.team == self.turn:

                        for move in p.possible_moves:
                            if abs(move[0] - p.i) != 2 or abs(move[1] - p.j) != 2:
                                p.possible_moves[move] = False

    def utility_function(self) -> None:
        """
        Calculate the utility of the current board state.

        This function evaluates the board based on the number of opponent pieces,
        the position of the pieces, and any threats faced by the player's pieces.
        The utility value influences decision-making in the game.

        Attributes:
            utility (int): The calculated utility value for the board.
        """

        POSITION_WEIGHT = 10
        PIECE_WEIGHT = 2
        VULNERABILITY_PENALTY = 700  # Penalty for vulnerability

        num_opponent_pieces = 0
        num_pieces = 0
        position_score = 0

        for piece in self.pieces:
            if (piece.i == 0 and piece.team == self.team) or (
                piece.i == 8 and piece.team != self.team
            ):
                self.utility = 100000 if piece.team == self.team else -100000
                return

            num_threats = self.count_threats(piece)

            if num_threats > 0:
                position_score -= (
                    num_threats * VULNERABILITY_PENALTY
                )  # Penalize for threats

            if piece.team == self.team:
                num_pieces += 1
                position_score += piece.i if self.turn != self.team else -8 + piece.i

            if piece.team == self.team and 1 < piece.j < 7:
                direction = -1 if piece.team == self.team else 1
                if 0 <= piece.i + (3 * direction) < 9:  # Ensure there is space
                    pieces_in_triangle = check_triangle(self, piece, direction)
                    empty_cells_in_triangle = 10 - pieces_in_triangle
                    if empty_cells_in_triangle > 0:
                        position_score += 2500 * (0.5**pieces_in_triangle)
                    else:
                        num_opponent_pieces += 1

        self.utility = position_score * POSITION_WEIGHT
        self.utility -= (num_opponent_pieces + num_pieces) * PIECE_WEIGHT

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


def check_triangle(self, piece, direction):
    pieces_in_triangle = 0

    for row_offset, width in enumerate([4, 3, 2, 1]):
        for col_offset in range(-width // 2, width // 2):
            row = piece.i + (row_offset * direction)
            col = piece.j + col_offset
            if 0 <= row < 9 and 0 <= col < 9 and self.board[row, col] != 0:
                pieces_in_triangle += 1

    return pieces_in_triangle
