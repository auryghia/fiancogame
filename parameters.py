import math

GAME_TITLE, SCREEN_COLOUR = "Fianco", (255, 255, 255)

GAME_RES = WIDTH, HEIGHT = 900, 720
GRID_SIZE = 720
CELL_SIZE = GRID_SIZE // 9


TT = False
PVS = False
SIZE = int(2**19)
IMP_MOVES_SIZE = 4000
PERCENTAGE = 0.75
DEPTH = 4
MIN = -32000
MAX = 32000
RESET_TABLE = True
ORDENING = {
    "killer_moves": True,
    "pruning_moves": False,
    "history_heuristic": False,
    "captures": False,
}


TEAM = 1
TURN = 1
PLAYERS = ["manually", "automatic"]
