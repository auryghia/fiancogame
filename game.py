import pygame
from pygame.locals import *
from states import Board, PygameEnviroment
from engine import Engine
from parameters import *


pygame.init()
pygame.display.set_caption(GAME_TITLE)
screen = pygame.display.set_mode(GAME_RES, pygame.HWSURFACE | pygame.DOUBLEBUF)
board_obj = Board(turn=TURN, team=TEAM)
env = PygameEnviroment(board_obj)
env.board_obj.create_boards()
engine = Engine(size=SIZE, reset_table=RESET_TABLE, p=PERCENTAGE)
current_selection = None
running = True
click_time = 0
while running:

    screen.fill(SCREEN_COLOUR)
    env.show(screen, GAME_RES, GRID_SIZE, CELL_SIZE, COLOR)
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
                print("Automatic Player")
                if PLAYERS[env.board_obj.turn - 1] == "automatic":

                    if env.board_obj.turn == env.board_obj.team:
                        print("Thinking...")
                        env.board_obj = engine.think(env.board_obj, DEPTH, MIN, MAX)

            if event.key == K_UP:

                DEPTH += 1
                print(f"New Depth level: {DEPTH}")

            if event.key == K_DOWN:
                DEPTH -= 1
                print(f"New Depth Level: {DEPTH}")

        else:
            # Manual player
            if PLAYERS[env.board_obj.turn - 1] == "manually":
                env.board_obj.handle_capture()

            if event.type == MOUSEBUTTONDOWN:
                # Manual Move
                pos = pygame.mouse.get_pos()
                x, y = pos
                x = x // CELL_SIZE
                y = y // CELL_SIZE

                if y > 8 or y < 0 or x > 8 or x < 0:
                    continue

                new_selection = (y, x)

                if current_selection is not None:
                    if current_selection in env.board_obj.possible_moves:

                        if (
                            new_selection
                            in env.board_obj.possible_moves[
                                (current_selection[0], current_selection[1])
                            ]
                        ):
                            if env.board_obj.possible_moves[
                                (current_selection[0], current_selection[1])
                            ][new_selection]:

                                env.board_obj.move_pieces(
                                    current_selection[0], current_selection[1], y, x
                                )

                    current_selection = None
                    env.selected_piece = None
                else:
                    if env.board_obj.board[y, x] == env.board_obj.turn:
                        current_selection = (y, x)
                        env.selected_piece = [y, x]


pygame.quit()
