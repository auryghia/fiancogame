import pygame
import sys
import random
import time
import numpy as np
from states import Player, Piece, Board, PygameEnviroment, AlphaBeta
import copy

pygame.init()

screen_size = 720
cell_size = screen_size // 9
screen = pygame.display.set_mode((screen_size, screen_size))
pygame.display.set_caption("Scacchiera 9x9")


background_color = (255, 255, 255)
player = Player(team=2)
board_obj = Board(turn=1, player=player)
env = PygameEnviroment(board_obj, player)
env.board_obj.create_boards()
abeta = AlphaBeta()
# initialize the board
# initialize the enviroment


# Ciclo principale
running = True
click_time = 0
while running:

    screen.fill(background_color)
    env.show(screen, screen_size, cell_size)
    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False
        if env.player1 == "manually" and env.player2 == "manually":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                col = mouse_x // cell_size
                row = mouse_y // cell_size
                for piece in env.pieces:
                    if piece.team == env.turn:
                        if piece.i == row and piece.j == col:

                            if not piece.is_selected:

                                for p in env.pieces:
                                    p.is_selected = False

                                piece.is_selected = True

                                (
                                    piece.possible_moves_up(env.board)
                                    if piece.team == 1
                                    else piece.possible_moves_down(env.board)
                                )

                            else:

                                piece.is_selected = False

            elif event.type == pygame.MOUSEBUTTONUP:

                mouse_x, mouse_y = event.pos
                col = mouse_x // cell_size
                row = mouse_y // cell_size

                for piece in env.pieces:

                    if piece.is_selected and piece.team == env.turn:

                        if (row, col) in piece.possible_moves and piece.possible_moves[
                            (row, col)
                        ]:
                            if 0 <= row < screen_size and 0 <= col < screen_size:

                                env.board_obj = abeta.move_pieces(row, col)

                                env.board_obj.turn = 2 if env.board_obj.turn == 1 else 1
                                piece.is_selected = False

        elif env.player1 == "automatic" and env.player2 == "manually":
            if (
                env.board_obj.turn == env.board_obj.team
            ):  # se è il turno del giocatore automatico
                print(env.board_obj.turn, "TURNO")
                aba = AlphaBeta()
                best_score, best_move = aba.alpha_beta_Negamax(
                    env.board_obj, 3, -np.inf, np.inf
                )
                env.board_obj = copy.deepcopy(best_move)

            else:
                # Gestione del turno del giocatore manuale
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    col = mouse_x // cell_size
                    row = mouse_y // cell_size
                    for piece in env.board_obj.pieces:
                        if piece.team == env.board_obj.turn:
                            if piece.i == row and piece.j == col:
                                if not piece.is_selected:
                                    for p in env.board_obj.pieces:
                                        p.is_selected = False
                                    piece.is_selected = True
                                    piece.possible_moves_down(env.board_obj.board)

                                else:
                                    piece.is_selected = False

                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse_x, mouse_y = event.pos
                    col = mouse_x // cell_size
                    row = mouse_y // cell_size
                    for piece in env.board_obj.pieces:
                        if piece.is_selected and piece.team == env.board_obj.turn:
                            if (
                                row,
                                col,
                            ) in piece.possible_moves and piece.possible_moves[
                                (row, col)
                            ]:
                                if 0 <= row < screen_size and 0 <= col < screen_size:
                                    env.board_obj = abeta.move_pieces(
                                        env.board_obj, row, col
                                    )


pygame.quit()
