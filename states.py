from typing import List
import numpy as np
import pygame
import math
import copy


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
        self.move_number = 0
        self.old_pieces = []
        self.old_moves_piece = None
        self.capture_available = False
        self.possible_moves = {}
        self.win = False
        self.game_over = False
        self.moves = []
        # Game board
        self.board = np.zeros((9, 9), dtype=int)
        # Score and utility
        self.score = -math.inf
        self.utility = 0
        self.best_move = None
        self.bestBoard = None

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
        # Black
        board = self.board
        board[0, :] = 2
        board[1, 1] = 2
        board[1, 7] = 2
        board[2, 2] = 2
        board[2, 6] = 2
        board[3, 3] = 2
        board[3, 5] = 2

        # White
        board[8, :] = 1
        board[7, 1] = 1
        board[7, 7] = 1
        board[6, 2] = 1
        board[6, 6] = 1
        board[5, 3] = 1
        board[5, 5] = 1

    def possible_moves_f(self, i, j) -> None:
        """Calculate possible moves for the piece based on its current position."""

        # Initialize possible moves dictionary
        direction = -1 if self.board[i, j] == self.team else 1
        moves_dict = {
            (i + direction, j): False,  # Simple forward move
            (i + 2 * direction, j - 2): False,  # Capture move (left)
            (i + 2 * direction, j + 2): False,  # Capture move (right)
            (i, j - 1): False,  # Move left
            (i, j + 1): False,  # Move right
            (i - direction, j): False,  # Backward move
            (i - 2 * direction, j + 2): False,  # Backward capture (right)
            (i - 2 * direction, j - 2): False,  # Backward capture (left)
        }

        # Check simple forward move
        if 0 <= i + direction < 9:
            if self.board[i + direction][j] == 0:  # Check if the cell is empty
                moves_dict[(i + direction, j)] = True

        # Check horizontal moves
        if j - 1 >= 0 and self.board[i][j - 1] == 0:
            moves_dict[(i, j - 1)] = True
        if j + 1 < 9 and self.board[i][j + 1] == 0:
            moves_dict[(i, j + 1)] = True

        # Check capture moves
        if 0 <= i + 2 * direction < 9:
            # Check left capture
            if j - 2 >= 0:
                if self.board[i, j] == 1:
                    if (
                        self.board[i + direction][j - 1] == 2
                        and self.board[i + 2 * direction][j - 2] == 0
                    ):
                        moves_dict[(i + 2 * direction, j - 2)] = True
                elif self.board[i, j] == 2:
                    if (
                        self.board[i + direction][j - 1] == 1
                        and self.board[i + 2 * direction][j - 2] == 0
                    ):
                        moves_dict[(i + 2 * direction, j - 2)] = True

        # Check right capture
        if 0 <= i + 2 * direction < 9:
            if j + 2 < 9:
                if self.board[i, j] == 1:
                    if (
                        self.board[i + direction][j + 1] == 2
                        and self.board[i + 2 * direction][j + 2] == 0
                    ):
                        moves_dict[(i + 2 * direction, j + 2)] = True
                elif self.board[i, j] == 2:
                    if (
                        self.board[i + direction][j + 1] == 1
                        and self.board[i + 2 * direction][j + 2] == 0
                    ):
                        moves_dict[(i + 2 * direction, j + 2)] = True

        return moves_dict

    def create_new_board(self, oi, oj, i, j):
        new_board = Board(team=self.team, turn=self.turn)
        new_board.board = copy.deepcopy(self.board)
        new_board.move_number = self.move_number
        new_board.win = self.win
        new_board.game_over = self.game_over
        new_board.move_pieces(oi, oj, i, j)
        return new_board

    def count_threats(self, i, j) -> int:
        num_threats = 0
        direction = -1 if self.board[i, j] == self.team else 1
        if i + direction < 9 and i + direction >= 0 and j - 1 >= 0 and j + 1 < 9:
            if self.board[i + direction, j + 1] == 0:
                num_threats += 1

            if self.board[i + direction, j - 1] == 0:

                num_threats += 1
        return num_threats

    def move_pieces(self, oi, oj, i, j):
        self.board[i, j] = self.board[oi, oj]
        self.board[oi, oj] = 0
        self.moves.append((oi, oj, i, j))
        if abs(i - oi) == 2:
            mid_i = (i + oi) // 2
            mid_j = (j + oj) // 2
            self.board[mid_i, mid_j] = 0

        self.turn = 2 if self.turn == 1 else 1
        self.move_number += 1

    def handle_capture(self):
        """Handles the capture logic for available pieces."""
        self.capture_available = False
        capture_pieces = []
        for i in range(9):
            for j in range(9):
                if self.board[i, j] == self.turn:
                    direction = -1 if self.board[i, j] == self.team else 1
                    possible_moves = self.possible_moves_f(i, j)
                    self.possible_moves[(i, j)] = possible_moves

                    if self.is_capture_possible(i, j):
                        self.capture_available = True

        if self.capture_available:
            self.disable_non_capture_moves()

    def is_capture_possible(self, i, j):
        """Checks if a piece can make a capture."""
        for di in [-2, 2]:
            for dj in [-2, 2]:
                new_i = i + di
                new_j = j + dj
                if (
                    (0 <= new_i < 9)
                    and (0 <= new_j < 9)
                    and self.possible_moves[(i, j)][(new_i, new_j)]
                ):
                    return True
        return False

    def disable_non_capture_moves(self):
        for i in range(9):
            for j in range(9):
                if self.board[i, j] == self.turn:
                    for move in list(self.possible_moves[(i, j)].keys()):
                        if abs(move[0] - i) != 2 or abs(move[1] - j) != 2:
                            self.possible_moves[(i, j)][move] = False

    def utility_function(self) -> None:
        POSITION_WEIGHT = 200
        PIECE_WEIGHT = 200
        VULNERABILITY_PENALTY = 150
        num_opponent_pieces = 0
        num_pieces = 0
        position_score = 0
        for i in range(9):
            for j in range(9):
                if self.board[i, j] != 0:

                    # Se il giocatore corrente è sulla casella
                    if self.board[i, j] == self.turn:

                        # Caso in cui il turno e la squadra coincidono e il pezzo è in cima
                        if self.turn == self.team and i == 0:
                            self.utility += 1000000

                        # Caso in cui il turno e la squadra NON coincidono e il pezzo è in fondo
                        if self.turn != self.team and i == 8:
                            self.utility += 1000000

                    # Se il giocatore corrente NON è sulla casella
                    if self.board[i, j] != self.turn:

                        # Caso in cui il turno e la squadra coincidono e il pezzo è in fondo (sconfitta)
                        if self.turn == self.team and i == 8:
                            self.utility -= 1000000

                        # Caso in cui il turno e la squadra NON coincidono e il pezzo è in cima (sconfitta)
                        if self.turn != self.team and i == 0:
                            self.utility -= 1000000

                    if self.board[i, j] == self.turn:

                        num_threats = self.count_threats(i, j)
                        if num_threats > 0:
                            vulnerability = VULNERABILITY_PENALTY * num_threats
                            position_score -= vulnerability

                    if self.board[i, j] == self.turn:

                        position_score += (
                            (i**2) * POSITION_WEIGHT
                            if self.turn != self.team
                            else ((i - 8) ** 2) * POSITION_WEIGHT
                        )

                    if self.board[i, j] == self.turn:
                        num_pieces += 1
                    elif self.board[i, j] != self.turn:
                        num_opponent_pieces += 1

        reduction_factor = max(0, 1 - (1 / self.move_number))
        self.utility += position_score
        self.utility += (num_pieces - num_opponent_pieces) * PIECE_WEIGHT

    def undo_move(self):
        self.turn = 1 if self.turn == 2 else 2
        move = self.moves.pop()
        self.move_pieces(move[2], move[3], move[0], move[1])
        self.turn = 1 if self.turn == 2 else 2

        if abs(move[2] - move[0]) == 2:
            print("Undoing capture")
            mid_i = (move[2] + move[0]) // 2
            mid_j = (move[3] + move[1]) // 2
            self.board[mid_i, mid_j] = 1 if self.turn == 2 else 2


class PygameEnviroment:  # class for the pygame enviroment
    def __init__(self, board_obj: Board) -> None:
        self.board_obj = board_obj
        self.selected_piece = (
            None  # Aggiungi l'attributo per tenere traccia del pezzo selezionato
        )

    def show(self, screen, screen_size, grid_size, cell_size, color):
        font = pygame.font.Font(None, 36)
        letters = "abcdefghi"
        if color == 1:
            numbers_team_1 = "987654321"
            numbers_team_2 = "123456789"

        else:
            numbers_team_1 = "123456789"
            numbers_team_2 = "987654321"
        purple_color = (128, 0, 128)

        numbers = numbers_team_1 if self.board_obj.team == 1 else numbers_team_2
        for i in range(9):
            for j in range(9):
                square = self.board_obj.board[i, j]

                color = (0, 0, 0)
                if square == 1 or square == 2:
                    if color == 1:
                        pygame.draw.circle(
                            screen,
                            color,
                            (
                                j * cell_size + cell_size // 2,
                                i * cell_size + cell_size // 2,
                            ),
                            cell_size // 2 - 5,
                            4 if square == 1 else 0,
                        )

                    else:
                        pygame.draw.circle(
                            screen,
                            color,
                            (
                                j * cell_size + cell_size // 2,
                                i * cell_size + cell_size // 2,
                            ),
                            cell_size // 2 - 5,
                            0 if square == 1 else 4,
                        )

        if self.selected_piece is not None:
            pygame.draw.circle(
                screen,
                purple_color,
                (
                    self.selected_piece[1] * cell_size + cell_size / 2,
                    self.selected_piece[0] * cell_size + cell_size / 2,
                ),
                cell_size // 5 - 5 + 4,
            )
            if (
                self.selected_piece[0],
                self.selected_piece[1],
            ) in self.board_obj.possible_moves:
                for move in self.board_obj.possible_moves[
                    (self.selected_piece[0], self.selected_piece[1])
                ]:

                    if self.board_obj.possible_moves[
                        (self.selected_piece[0], self.selected_piece[1])
                    ][move]:
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
        if color == 1:

            player_text = "White's Turn" if self.board_obj.turn == 1 else "Black's Turn"
        else:
            player_text = "Black's Turn" if self.board_obj.turn == 1 else "White's Turn"
        player_text_rendered = font.render(player_text, True, (0, 0, 0))
        player_text_rect = player_text_rendered.get_rect(
            center=(screen_size[0] - 80, screen_size[1] - 20)
        )
        screen.blit(player_text_rendered, player_text_rect)
