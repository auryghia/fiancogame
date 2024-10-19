import math

GAME_TITLE, SCREEN_COLOUR = "Fianco", (255, 255, 255)
GAME_RES = WIDTH, HEIGHT = 900, 720
GRID_SIZE = 720
CELL_SIZE = GRID_SIZE // 9

# GAME SETTINGS
TEAM = 1
COLOR = 2
TURN = 1
PLAYERS = ["manually", "automatic"]

# ALPHA-BETA PRUNING
DEPTH = 6
MIN = -3200000
MAX = 3200000
VARIABLE_DEPTH = False
RESET_TABLE = False

ORDENING = {
    "killer_moves": True,
    "pruning_moves": False,
    "history_heuristic": True,
    "captures": False,
}

# ASPIRATIONAL SEARCH
AS = False
DELTA = 1200
MAX_DEPTH = 5

# MULTICUT
MULTICUT = True
R = 2
C = 2
M = 3

# TRASPOSITIONAL TABLE
TT = False
SIZE = int(math.pow(2, 20))
IMP_MOVES_SIZE = 4000
PERCENTAGE = 0.75
RESET_TABLE = False
