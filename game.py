import pygame
import time
from pygame.locals import *
from states import Board, PygameEnviroment
from engine import Engine
from parameters import *
import copy

pygame.init()
pygame.display.set_caption(GAME_TITLE)
screen = pygame.display.set_mode(GAME_RES, pygame.HWSURFACE | pygame.DOUBLEBUF)
board_obj = Board(turn=TURN, team=TEAM, players=PLAYERS)
env = PygameEnviroment(board_obj)
env.board_obj.create_boards()
env.board_obj.number_creation()
engine = Engine(size=SIZE, reset_table=RESET_TABLE, percentage=PERCENTAGE)


running = True
click_time = 0
while running:

    screen.fill(SCREEN_COLOUR)
    env.show(screen, GAME_RES, GRID_SIZE, CELL_SIZE)
    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:
                # undo move
                env.board_obj.undo_move()

            if event.key == pygame.K_r:
                # reset game
                env.board_obj = Board(turn=TURN, team=TEAM, players=PLAYERS)
                env.board_obj.create_boards()
                env.board_obj.number_creation()

            # automatic player
            if event.key == pygame.K_n:
                if env.board_obj.players[env.board_obj.turn] == "automatic":
                    if env.board_obj.turn == env.board_obj.team:

                        env.board_obj = engine.think(env.board_obj, DEPTH, MIN, MAX)

            elif event.key == K_UP:
                DEPTH += 1
                print(f"New Depth level: {DEPTH}")

            elif event.key == K_DOWN:
                DEPTH -= 1
                print(f"New Depth Level: {DEPTH}")

        else:
            # Manual player
            if env.board_obj.players[env.board_obj.turn] == "manually":

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    col = mouse_x // CELL_SIZE
                    row = mouse_y // CELL_SIZE
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
                    col = mouse_x // CELL_SIZE
                    row = mouse_y // CELL_SIZE
                    for piece in env.board_obj.pieces:
                        if piece.is_selected and piece.team == env.board_obj.turn:
                            if (
                                row,
                                col,
                            ) in piece.possible_moves and piece.possible_moves[
                                (row, col)
                            ]:
                                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
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
