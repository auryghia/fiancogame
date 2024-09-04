import pygame
import sys
import random
import time
import numpy as np
from states import Piece, Board, PygameEnviroment

pygame.init()

screen_size = 720  # Cambia la dimensione della finestra
cell_size = screen_size // 9  # Calcola la dimensione della cella in base alla finestra
screen = pygame.display.set_mode((screen_size, screen_size))
pygame.display.set_caption("Scacchiera 9x9")


# Definisci il colore di sfondo
background_color = (255, 255, 255)

board_obj = Board()
board_obj.create_boards()  # initialize the board
env = PygameEnviroment(board_obj)  # initialize the enviroment


# Ciclo principale
running = True
click_time = 0
while running:
    # Riempi lo schermo con il colore di sfondo
    screen.fill(background_color)
    env.show(screen, screen_size, cell_size)
    # Aggiorna lo schermo
    pygame.display.flip()
    # mouse_x, mouse_y = pygame.mouse.get_pos()
    # col = mouse_x // cell_size
    # row = mouse_y // cell_size
    # if env.board_obj.board[row, col] == 1:

    #     for piece in env.pieces:
    #         if piece.i == row and piece.j == col:
    #             piece.is_selected = True
    #         else:
    #             piece.is_selected = False

    # Gestione degli eventi (es. chiusura finestra)
    for event in pygame.event.get():
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     mouse_x, mouse_y = event.pos
        #     print(piece.possible_moves, row, col)
        #     if (row, col) in piece.possible_moves:
        #         if piece.possible_moves[(row, col)]:
        #             print(row, col)
        #             col = mouse_x // cell_size
        #             row = mouse_y // cell_size
        #             if 0 <= row < screen_size and 0 <= col < screen_size:
        #                 env.move_pieces(row, col)

        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Quando clicchi per selezionare un pezzo
            mouse_x, mouse_y = event.pos
            col = mouse_x // cell_size
            row = mouse_y // cell_size
            for piece in env.pieces:
                if piece.team == 1:
                    if piece.i == row and piece.j == col:
                        # Se il pezzo non è selezionato, selezionalo
                        if not piece.is_selected:
                            for p in env.pieces:
                                p.is_selected = False

                            piece.is_selected = True
                            piece.possible_moves_f(env.board_obj.board)
                            print(f"Pezzo selezionato: {piece.i}, {piece.j}")
                            print(f"Mosse possibili: {piece.possible_moves}")
                        else:
                            # Se è già selezionato, deselezionalo
                            piece.is_selected = False
                            print("Pezzo deselezionato.")

        elif event.type == pygame.MOUSEBUTTONUP:
            # Quando rilasci il mouse per muovere il pezzo
            mouse_x, mouse_y = event.pos
            col = mouse_x // cell_size
            row = mouse_y // cell_size
            for piece in env.pieces:
                # Muove solo se il pezzo è selezionato e appartiene al team corretto
                if piece.team == 1 and piece.is_selected:
                    # Controllo se la cella rilasciata è in una delle mosse consentite
                    if (row, col) in piece.possible_moves and piece.possible_moves[
                        (row, col)
                    ]:
                        if 0 <= row < screen_size and 0 <= col < screen_size:
                            # Sposta il pezzo nella nuova posizione
                            env.move_pieces(row, col)
                            piece.is_selected = False  # Deseleziona dopo il movimento
                            print(f"Pezzo spostato a: ({row}, {col})")
                    else:
                        print("Mossa non valida.")

        # elif event.type == pygame.MOUSEBUTTONDOWN:
        #     mouse_x, mouse_y = event.pos
        #     col = mouse_x // cell_size
        #     row = mouse_y // cell_size
        #     for piece in env.pieces:
        #         print(piece.is_selected)
        #         if piece.team == 1:
        #             if piece.i == row and piece.j == col:
        #                 if piece.is_selected == False:
        #                     piece.is_selected = True
        #                     piece.possible_moves_f(env.board_obj.board)
        #                     print(piece.possible_moves)

        #                 else:
        #                     piece.is_selected = False

        # elif event.type == pygame.MOUSEBUTTONUP:
        #     mouse_x, mouse_y = event.pos
        #     col = mouse_x // cell_size
        #     row = mouse_y // cell_size
        #     for piece in env.pieces:
        #         if piece.team == 1:
        #             if piece.is_selected:
        #                 if (row, col) in piece.possible_moves:
        #                     if piece.possible_moves[(row, col)]:
        #                         if 0 <= row < screen_size and 0 <= col < screen_size:
        #                             env.move_pieces(row, col)
        #                             piece.is_selected = False

        # Reset the color

        # elif event.type == pygame.MOUSEBUTTONDOWN:
        #     mouse_x, mouse_y = event.pos
        #     col = mouse_x // cell_size
        #     row = mouse_y // cell_size

        #     for piece in env.pieces:
        #         if piece.i == row and piece.j == col:
        #             piece.is_selected = True
        #             if piece.i == row and piece.j == col:
        #                 dragging = True
        #                 offset_x = mouse_x - (piece.i * cell_size + cell_size // 2)
        #                 offset_y = mouse_y - (piece.j * cell_size + cell_size // 2)
        #                 if event.type == pygame.MOUSEBUTTONUP:
        #                     if dragging:
        #                         dragging = False
        #                         mouse_x, mouse_y = event.pos
        #                         col = mouse_x // cell_size
        #                         row = mouse_y // cell_size
        #                         if (row, col) in piece.possible_moves:
        #                             if piece.possible_moves[(row, col)]:
        #                                 if (
        #                                     0 <= row < screen_size
        #                                     and 0 <= col < screen_size
        #                                 ):
        #                                     env.move_pieces(row, col)

        #                 elif event.type == pygame.MOUSEMOTION:
        #                     if dragging:
        #                         mouse_x, mouse_y = event.pos
        #                         piece.update_position(
        #                             (mouse_y - offset_y) // cell_size,
        #                             (mouse_x - offset_x) // cell_size,
        #                         )
        #         else:
        #             piece.is_selected = False


# Termina Pygame
pygame.quit()
