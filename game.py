import pygame
from pygame.locals import *
from states import Board, PygameEnviroment
from engine import Engine
from parameters import *
import copy
import cProfile
import pstats
import io


pygame.init()
pygame.display.set_caption(GAME_TITLE)
screen = pygame.display.set_mode(GAME_RES, pygame.HWSURFACE | pygame.DOUBLEBUF)
board_obj = Board(turn=TURN, team=TEAM, players=PLAYERS)
env = PygameEnviroment(board_obj)
env.board_obj.create_boards()
engine = Engine(size=SIZE, reset_table=RESET_TABLE, p=PERCENTAGE)


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

            # automatic player
            if event.key == pygame.K_n:
                if env.board_obj.players[env.board_obj.turn] == "automatic":
                    if env.board_obj.turn == env.board_obj.team:
                        pr = cProfile.Profile()
                        pr.enable()  # Inizia a profilare

                        env.board_obj = engine.think(env.board_obj, DEPTH, MIN, MAX)
                        pr.disable()  # Ferma la profilazione

                        # Cattura i risultati in un oggetto StringIO
                        s = io.StringIO()
                        sortby = (
                            pstats.SortKey.CUMULATIVE
                        )  # Puoi cambiare il criterio di ordinamento
                        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
                        ps.print_stats()
                        print(s.getvalue())

            elif event.key == K_UP:

                DEPTH += 1
                print(f"New Depth level: {DEPTH}")

            elif event.key == K_DOWN:
                DEPTH -= 1
                print(f"New Depth Level: {DEPTH}")

        else:
            # Manual player
            if env.board_obj.players[env.board_obj.turn] == "manually":
                env.board_obj.handle_capture()

                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_x, mouse_y = event.pos
                    env.handle_click((mouse_x, mouse_y), CELL_SIZE)
                elif event.type == pygame.MOUSEBUTTONUP:
                    mouse_x, mouse_y = event.pos
                    col = mouse_x // CELL_SIZE
                    row = mouse_y // CELL_SIZE
                    for i in range(9):
                        for j in range(9):
                            if row == i and col == j:
                                if env.board_obj.selected_piece:

                                    if (
                                        row,
                                        col,
                                    ) in env.board_obj.possible_moves[
                                        (i, j)
                                    ] and env.board_obj.possible_moves[(i, j)][
                                        (row, col)
                                    ]:
                                        env.board_obj.move_pieces(i, j, row, col)

                                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                                    env.board_obj.move_pieces(i, j, row, col)

pygame.quit()
