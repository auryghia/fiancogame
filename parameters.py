import math

GAME_TITLE, SCREEN_COLOUR = "Fianco", (255, 255, 255)

GAME_RES = WIDTH, HEIGHT = 900, 720
GRID_SIZE = 720
CELL_SIZE = GRID_SIZE // 9

SIZE = 4000
IMP_MOVES_SIZE = 40000
PERCENTAGE = 0.75
DEPTH = 5
MIN = -math.inf
MAX = math.inf
RESET_TABLE = True
ORDENING = {
    "killer_moves": False,
    "pruning_moves": False,
    "history_heuristic": False,
    "captures": True,
}


TEAM = 1
TURN = 1
PLAYERS = ["manually", "automatic"]
