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

board = Board()
board.create_boards()  # initialize the board
env = PygameEnviroment(board)  # initialize the enviroment


# Ciclo principale
running = True
while running:
    # Riempi lo schermo con il colore di sfondo
    screen.fill(background_color)
    env.show(screen, screen_size, cell_size)
    # Aggiorna lo schermo
    pygame.display.flip()

    # Gestione degli eventi (es. chiusura finestra)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

# Termina Pygame
pygame.quit()
