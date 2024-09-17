import pygame
import sys
import random
import time
import numpy as np
from states import Board, PygameEnviroment, Engine
import copy

pygame.init()

screen_size = (900, 720)
grid_size = 720
cell_size = grid_size // 9
screen = pygame.display.set_mode((screen_size[0], screen_size[1]))
pygame.display.set_caption("Scacchiera 9x9")

background_color = (255, 255, 255)

board_obj = Board(turn=1, team=1)

env = PygameEnviroment(board_obj)
env.board_obj.create_boards()
env.board_obj.number_creation()

engine = Engine()


running = True
click_time = 0
while running:

    screen.fill(background_color)
    env.show(screen, screen_size, grid_size, cell_size)
    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:
                env.board_obj.turn = 1 if env.board_obj.turn == 2 else 2
                print("redu")

                pieces = copy.deepcopy(env.board_obj.pieces)
                env.board_obj.pieces = copy.deepcopy(env.board_obj.old_pieces)
                env.board_obj.old_pieces = pieces

                env.board_obj.change_board()

            if event.key == pygame.K_n:
                if env.board_obj.turn == env.board_obj.team:

                    old_pieces = copy.deepcopy(env.board_obj.pieces)

                    best_score, best_move = engine.alpha_beta_Negamax(
                        env.board_obj, 3, -250, 250
                    )
                    best_move.old_pieces = old_pieces
                    env.board_obj = copy.deepcopy(best_move)
                    # engine.t_table = [[] for _ in range(engine.size)]

        else:
            if env.player1 == "manually" and env.player2 == "manually":
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

                                    (
                                        piece.possible_moves_up(env.board_obj.board)
                                        if piece.team == env.board_obj.team
                                        else piece.possible_moves_down(
                                            env.board_obj.board
                                        )
                                    )

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

                                    env.board_obj = engine.move_pieces(row, col)
                                    if event.type == pygame.KEYDOWN:
                                        if event.key == pygame.K_k:
                                            print("redu")
                                            env.board_obj.pieces = copy.deepcopy(
                                                env.board_obj.old_pieces
                                            )
                                            env.board_obj.change_board()

                                    env.board_obj.turn = (
                                        2 if env.board_obj.turn == 1 else 1
                                    )
                                    piece.is_selected = False

            elif env.player1 == "automatic" and env.player2 == "manually":

                if env.board_obj.turn != env.board_obj.team:

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
                                        env.board_obj, _ = engine.handle_capture(
                                            env.board_obj
                                        )
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
                                    if 0 <= row < grid_size and 0 <= col < grid_size:
                                        old_pieces = copy.deepcopy(env.board_obj.pieces)
                                        env.board_obj = engine.move_pieces(
                                            env.board_obj, row, col
                                        )

                                        env.board_obj.turn = (
                                            2 if env.board_obj.turn == 1 else 1
                                        )
                                        piece.is_selected = False
                                        env.board_obj.old_pieces = old_pieces


pygame.quit()
