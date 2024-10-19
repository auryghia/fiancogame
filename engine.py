from states import Board
import numpy as np
import math
import time
import copy
import heapq
from collections import defaultdict, OrderedDict
from parameters import (
    ORDENING,
    TT,
    AS,
    MULTICUT,
    VARIABLE_DEPTH,
    R,
    C,
    M,
    DELTA,
    MAX_DEPTH,
    RESET_TABLE,
)


class Engine:
    """
    A class representing the game engine responsible for handling the game state,
    performing alpha-beta pruning using Negamax, and managing transposition tables.
    """

    def __init__(
        self, size: int = 4000, p: float = 0.75, reset_table: bool = True
    ) -> None:
        """
        Initialize the Engine with transposition table settings, zobrist hashing,
        and move-tracking structures like killer moves and important moves.

        Parameters:
            size (int): Size of the transposition table.
            p (float): Percentage of table to retain during optimization.
            reset_table (bool): Whether to reset the transposition table after each move.
        """
        # Transposition table and pruning structures
        self.size = size
        self.percentage = p
        self.reset_table = reset_table
        self.killerMoves = defaultdict(lambda: OrderedDict())
        self.histHeuristic = dict()

        # Collision and pruning stats
        self.collisions = 0
        self.pruning_numbers = 0

        # Zobrist hashing and transposition table setup
        self.zobrist_table = np.random.randint(
            0, 2**63 - 1, size=(9, 9, 3), dtype=np.int64
        )
        self.num_elements = 0

        # Transposition table structure
        dtype = np.dtype(
            [
                ("score", np.int32),
                ("flag", "U10"),
                ("upper_bound", np.int32),
                ("lower_bound", np.int32),
                ("depth", np.int8),
                ("best_move", object),
            ]
        )
        self.t_table = np.zeros(self.size, dtype=dtype)

    def aspirational_search(
        self, delta: int, max_depth: int, board: Board, d: int, alpha: int, beta: int
    ):
        """
        Performs aspirational search using the Alpha-Beta pruning algorithm with an initial guess and a window (alpha, beta) that adapts based on previous results.

        This method incrementally deepens the search by iterating through increasing depths until the given maximum depth is reached or a time limit is exceeded.
        It adjusts the search window (alpha, beta) dynamically based on fail-low and fail-high outcomes.

        Parameters:
            delta (int): Margin of error to adjust the search window around the current guess.
            max_depth (int): Maximum search depth for the algorithm.
            board (Board): Current game state or board configuration.
            d (int): Current depth to start the iterative deepening.
            alpha (int): Lower bound of the alpha-beta search window.
            beta (int): Upper bound of the alpha-beta search window.

        Returns:
            tuple: Best score and board state found by the search at the given depth.
        """
        guess = 0
        start_time = time.time()

        for d in range(1, max_depth + 1):

            alpha = guess - delta
            beta = guess + delta
            if TT:
                score, bestBoard = self.alpha_beta_Negamax_TT(board, d, alpha, beta)
                self.clear_table()
            else:
                score, bestBoard = self.alpha_beta_Negamax(board, d, alpha, beta)

            score = -score
            if score <= alpha:
                print("fail low, ", "score: ", score, "beta: ", alpha, "depth:", d)
                alpha = -math.inf
                beta = score

                if TT:  # Check if transposition table is enabled
                    score, bestBoard = self.alpha_beta_Negamax_TT(board, d, alpha, beta)
                    self.clear_table()
                else:
                    score, bestBoard = self.alpha_beta_Negamax(board, d, alpha, beta)
                self.pruning_numbers = 0
                score = -score

            elif score >= beta:
                print("fail high, ", "score: ", score, "beta: ", beta, "depth:", d)
                beta = math.inf
                if TT:  # Check if transposition table is enabled
                    score, bestBoard = self.alpha_beta_Negamax_TT(board, d, alpha, beta)
                    self.clear_table()
                else:
                    score, bestBoard = self.alpha_beta_Negamax(board, d, alpha, beta)
                self.pruning_numbers = 0
                score = -score

            guess = score

        return score, bestBoard

    def multi_cut(self, C, M, board: Board, depth: int, alpha: float, beta: float):
        """
        Implements the Multi-Cut pruning strategy for reducing the search tree in a two-player zero-sum game.

        Parameters:
            C (int): The cut threshold. If `C` or more moves are found that exceed the beta cutoff, the function will stop further search and return beta.
            M (int): The number of initial moves to be evaluated for multi-cut pruning.
            board (Board): The current state of the game board.
            depth (int): The depth of the search.
            alpha (float): The current lower bound of the search window.
            beta (float): The current upper bound of the search window.

        Returns:
            (float, Board): A tuple containing the best score and the corresponding board state.

        This method works in two main phases:

        1. **Multi-Cut Phase**:
        - Evaluate up to `M` moves.
        - For each move, if its negamax value exceeds beta, increment the cut counter `c`.
        - If `c` reaches `C` (i.e., enough moves are proven to be bad for the opponent), the search is cut off early and the method immediately returns `beta`, indicating a fail-high.

        2. **Regular Search Phase**:
        - If the multi-cut phase does not trigger early pruning, the function proceeds with a regular Alpha-Beta Negamax search,
            similar to the `alpha_beta_Negamax_TT` method.
        - For each remaining move, it calls the alpha-beta negamax search recursively to evaluate the board state.
        - If a move's value exceeds the current best score, it updates the score and records the best move and board state.

        """

        boards = self.next_moves(board)
        c = 0
        m = 0
        while len(boards) > 0 and m < M:
            b, oi, oj, i, j = boards.pop(0)

            value, _ = self.alpha_beta_Negamax_TT(b, depth - 1 - R, -beta, -alpha)
            value = -value

            if value >= beta:
                c += 1
                self.pruning_numbers += 1

                if c >= C:
                    return beta, b

            m += 1
        self.clear_table()
        return self.alpha_beta_Negamax_TT(board, depth, alpha, beta)

    def alpha_beta_Negamax(self, board: Board, depth: int, alpha: float, beta: float):
        """
        Perform the Negamax algorithm with alpha-beta pruning on the given game board.

        Parameters:
            board (Board): The current state of the game board.
            depth (int): The maximum depth to search in the game tree.
            alpha (float): The best score that the maximizing player can guarantee at that level
                        or above. It is initialized to negative infinity.
            beta (float): The best score that the minimizing player can guarantee at that level
                        or above. It is initialized to positive infinity.

        Returns:
            tuple: A tuple containing:
                - score (float): The evaluated utility score for the current board state.
                - bestBoard (Board): The best board state resulting from the evaluated moves.

        """
        if depth == 0:
            if board.turn == board.team:
                board.utility_function()

            else:
                board.utility_function()
                board.utility = -board.utility

            return board.utility, board

        score = -math.inf
        boards = self.next_moves(board)

        for b, oi, oj, i, j in boards:
            if VARIABLE_DEPTH:
                if abs(oi - i) > 1:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth, -beta, -alpha)

                else:
                    value, _ = self.alpha_beta_Negamax_TT(b, depth - 1, -beta, -alpha)

            else:
                value, _ = self.alpha_beta_Negamax(b, depth - 1, -beta, -alpha)

            value = -value
            if value > score:
                score = value
                bestBoard = b
                bestMove = (oi, oj, i, j)

            alpha = max(alpha, score)

            if alpha >= beta:
                if ORDENING["killer_moves"]:
                    self.add_killer_move(depth, (board.zobrist, b.zobrist))
                self.pruning_numbers += 1
                break
        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((bestMove), depth)
        return score, bestBoard

    def alpha_beta_Negamax_TT(
        self, board: Board, depth: int, alpha: float, beta: float
    ):
        """
        Implements the Alpha-Beta pruning algorithm with Negamax search and transposition table (TT) lookup.
        This method efficiently searches for the best move in a two-player zero-sum game.

        Parameters:
            board (Board): The current state of the game board.
            depth (int): The maximum depth for the search.
            alpha (float): The current lower bound of the search window.
            beta (float): The current upper bound of the search window.

        Returns:
            (float, Board): A tuple containing the best score evaluated and the corresponding board state after the best move.

        """

        old_alpha = alpha
        zobrist_key = board.zobrist
        board.depth = depth
        ttEntry = self.get(zobrist_key)
        if ttEntry["depth"] != 0:
            if ttEntry["flag"] == "EXACT":
                oi, oj, i, j = ttEntry["best_move"]
                newBoard = board.create_new_board(oi, oj, i, j)
                newBoard.zobrist = self.zobrist_hash(newBoard)
                return ttEntry["score"], newBoard

            elif ttEntry["flag"] == "LOWER_BOUND":
                alpha = max(alpha, ttEntry["score"])
                board.lower_bound = alpha
            elif ttEntry["flag"] == "UPPER_BOUND":
                beta = min(beta, ttEntry["score"])
                board.upper_bound = beta

            if alpha >= beta:
                return ttEntry["score"], board

        if depth == 0:
            if board.turn == board.team:
                board.utility_function()

            else:
                board.utility_function()
                board.utility = -board.utility

            return board.utility, board

        score = -math.inf
        boards = self.next_moves(board)
        for b, oi, oj, i, j in boards:
            value, _ = self.alpha_beta_Negamax_TT(b, depth - 1, -beta, -alpha)

            value = -value
            if value > score:
                score = value
                bestMove = (oi, oj, i, j)
                bestBoard = b

            alpha = max(alpha, score)

            if alpha >= beta:
                if ORDENING["killer_moves"]:
                    self.add_killer_move(depth, (board.zobrist, b.zobrist))
                self.pruning_numbers += 1

                break
        board.flag = "EXACT"
        if score <= old_alpha:
            board.flag = "UPPER_BOUND"
        elif score >= beta:
            board.flag = "LOWER_BOUND"
        board.upper_bound = beta
        board.lower_bound = alpha
        board.best_move = bestMove
        board.score = score
        board.bestBoard = bestBoard

        if ORDENING["history_heuristic"]:
            self.add_history_heuristic((bestMove), depth)

        self.insert(board)

        return score, bestBoard

    def next_moves(self, board: Board):
        """
        Generates and classifies all possible moves for the current player's turn, applying move ordering
        heuristics to prioritize moves and optimize the search process.

        Parameters:
            board (Board): The current state of the game board.

        Returns:
            List[Tuple]: A list of possible board states after each move, prioritized by the following heuristics:
                1. **Killer Moves**: Moves that have previously caused beta-cutoffs at the same depth, thus likely strong moves.
                2. **Capture Moves**: Moves where the opponent's piece is captured.
                3. **History Heuristic Moves**: Moves that have historically led to better outcomes in similar positions.
                4. **Pruning Moves**: Moves that were previously pruned during search due to being unlikely to improve the current position.
                5. **Regular Moves**: All remaining legal moves that do not fall into the above categories.

        Move Classification:
        - The method uses different heuristics from the `ORDENING` dictionary to classify and prioritize moves:
            - **Killer Moves**: Stored in `self.killerMoves` for each depth. These moves caused a beta-cutoff earlier at the same depth and are sorted and evaluated first.
            - **Capture Moves**: These moves involve capturing an opponent's piece, marked by `capture_available` in the new board state.
            - **History Heuristic Moves**: Moves that have a good history of success in previous searches, stored in `self.histHeuristic`.
            - **Pruning Moves**: Moves that were pruned during earlier searches but are still legal and evaluated here.
        """

        boards = []
        board.handle_capture()
        turn = board.turn
        killerMoves, pruningMoves, histHeuristic, captMoves = [], [], [], []

        for i in range(9):
            for j in range(9):
                if board.board[i, j] == turn:
                    for move in board.possible_moves[(i, j)]:
                        if board.possible_moves[(i, j)][move]:
                            newBoardObj = board.create_new_board(i, j, move[0], move[1])
                            newBoardObj.zobrist = self.zobrist_hash(newBoardObj)

                            if (
                                ORDENING["killer_moves"]
                                and board.depth in self.killerMoves
                                and (board.zobrist, newBoardObj.zobrist)
                                in self.killerMoves[board.depth]
                            ):
                                killerMoves.append(
                                    (newBoardObj, i, j, move[0], move[1])
                                )

                            elif (
                                ORDENING["history_heuristic"]
                                and (i, j, move[0], move[1])
                            ) in self.histHeuristic:
                                histHeuristic.append(
                                    (newBoardObj, i, j, move[0], move[1])
                                )
                            else:
                                boards.append((newBoardObj, i, j, move[0], move[1]))
        if ORDENING["killer_moves"]:
            self.sort_killer_moves(killerMoves, board, self.killerMoves[board.depth])

        if ORDENING["history_heuristic"]:
            histHeuristic = self.sort_hist_moves(
                histHeuristic, board, self.histHeuristic
            )

        return killerMoves + captMoves + pruningMoves + histHeuristic + boards

    def sort_killer_moves(self, move_list: list, board, move_dict: dict):
        move_list.sort(
            key=lambda item: move_dict.get(
                (board.zobrist, item[0].zobrist), float("-inf")
            ),
            reverse=True,
        )
        return move_list

    def sort_hist_moves(self, move_list: list, board, move_dict: dict):

        move_list.sort(
            key=lambda item: move_dict.get(
                (item[1], item[2], item[3], item[4]), float("-inf")
            ),
            reverse=True,
        )

        return move_list

    def add_killer_move(self, depth, move):
        """
        Adds a move to the killer moves table for a specific search depth.

        Parameters:
            depth (int): The current depth of the search where the killer move was found.
            move (Tuple): The move that resulted in a beta-cutoff, represented as a tuple containing board state information.

        Optimizations:
        - To maintain efficiency, the function stores only the top 10 most effective killer moves per depth.
        - If more than 10 killer moves are recorded at a given depth, it sorts the killer moves by their frequency of success and retains only the top 10 moves using an `OrderedDict`.
        - Sorting is done in descending order, so the most frequently successful moves are prioritized and kept in the list.

        """
        if depth not in self.killerMoves:
            self.killerMoves[depth] = {}

        if move in self.killerMoves[depth]:
            self.killerMoves[depth][move] += 1
        else:
            self.killerMoves[depth][move] = 1
        if len(self.killerMoves[depth]) > 10:
            self.killerMoves[depth] = OrderedDict(
                sorted(
                    self.killerMoves[depth].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[
                    :100
                ]  # keep only the best 10 moves for depth
            )

    def add_history_heuristic(self, move, depth):
        """
        Adds or updates the history heuristic score for a given move.

        Parameters:
            move (Tuple): The move to be updated in the history heuristic, typically represented by
                          the coordinates or state change on the board.
            depth (int): The depth at which the move was made in the current search. This determines
                         the weight of the update to the heuristic.
        """
        if move in self.histHeuristic:
            self.histHeuristic[move] += 2 * depth
        else:
            self.histHeuristic[move] = 2 * depth

    def zobrist_hash(self, board: Board):
        """
        Computes the Zobrist hash for the given board state.

        Parameters:
            board (Board): The current board state, represented as a 2D array where each cell contains a piece or is empty.

        Returns:
            int: The Zobrist hash value, a unique integer representing the current board configuration.

        """

        zobrist_value = 0
        for row in range(9):
            for col in range(9):
                if board.board[row, col] != 0:
                    value = board.board[row, col]
                    zobrist_value ^= self.zobrist_table[row, col, value]

        return zobrist_value

    def hash_index(self, zobrist_value):
        """
        Computes the index for the Zobrist hash value to access the transposition table.

        Parameters:
            zobrist_value (int): The Zobrist hash value of the current board state.

        Returns:
            int: The index corresponding to the Zobrist hash in the transposition table, determined by taking the modulo
                 of the Zobrist value with the size of the table.
        """
        return zobrist_value % self.size

    def insert(self, board: Board):
        """
        Inserts the given board state into the transposition table (TT) based on its Zobrist hash,
        storing key information about the board and the search results to optimize future lookups.

        Parameters:
            board (Board): The board state to be inserted into the transposition table, containing information
                           such as score, flag (for alpha-beta pruning), depth, bounds, and the best move.

        Collision Handling:
        - If a collision occurs (i.e., two different board states hash to the same index), the function only overwrites
          the existing entry if the new board has been searched at a greater depth, as deeper searches provide more
          accurate evaluations.

        """

        index = self.hash_index(board.zobrist)
        if self.t_table[index]["depth"] != 0:
            self.collisions += 1
            if self.t_table[index]["depth"] > board.depth:

                self.t_table[index] = np.array(
                    [
                        (
                            board.score,
                            board.flag,
                            board.upper_bound,
                            board.lower_bound,
                            board.depth,
                            board.best_move,
                        )
                    ],
                    dtype=self.t_table.dtype,
                )

                self.num_elements += 1

                return

        self.t_table[index] = np.array(
            [
                (
                    board.score,
                    board.flag,
                    board.upper_bound,
                    board.lower_bound,
                    board.depth,
                    board.best_move,
                )
            ],
            dtype=self.t_table.dtype,
        )

        self.num_elements += 1

    def get(self, key):
        """
        Retrieves an entry from the transposition table (TT) based on the given Zobrist hash key.

        Parameters:
            key (int): The Zobrist hash key of the current board state.

        Returns:
            dict: The entry from the transposition table at the computed index. If no valid entry exists
                  (i.e., depth is -1), it returns a dictionary with {"depth": -1}, indicating an invalid entry.
        """

        index = self.hash_index(key)
        entry = self.t_table[index]
        if entry["depth"] == -1:
            return {"depth": -1}
        return entry

    def change_table(self):
        """
        Optimizes the transposition table (TT) by retaining only the most relevant entries, based on search depth.
        The function clears old entries and resizes the TT, keeping only a percentage of the most useful entries.
\
        Purpose:
        - This method reduces memory usage and improves lookup performance by retaining only the most important entries, 
          which are those corresponding to deeper searches.
        """

        new_table = np.zeros(self.size, dtype=self.t_table.dtype)
        print("Optimizing table")
        all_elements = []
        for i in range(self.size):
            entry = self.t_table[i]
            if entry["depth"] != -1:
                all_elements.append((entry))

        largest_elements = heapq.nlargest(
            int(self.size * self.percentage), all_elements, key=lambda x: x[1]["depth"]
        )

        for zobrist, entry in largest_elements:
            new_index = self.hash_index(zobrist) % self.size
            new_table[new_index] = entry

        self.table = new_table

    def clear_table(self):
        """
        Clears the transposition table (TT), resetting all entries and setting the number of stored elements to zero.

        Purpose:
        - This method is used to reset the transposition table, which can be useful when starting a new search or
          when optimizing the table after it becomes too large or filled with outdated data.
        """
        self.t_table = np.zeros(self.size, dtype=self.t_table.dtype)
        self.num_elements = 0

    def think(self, board: Board, depth, alpha, beta):
        """
        Executes the main search algorithm, selecting the optimal move from the given board state.
        This method supports various search optimizations such as Transposition Table (TT), Aspirational Search (AS),
        and Multi-Cut Pruning, and prints detailed performance statistics after the search.

        Parameters:
            board (Board): The current board state.
            depth (int): The maximum search depth.
            alpha (float): The alpha value for alpha-beta pruning (initially set to -infinity).
            beta (float): The beta value for alpha-beta pruning (initially set to +infinity).

        Returns:
            Board: The updated board state after evaluating the best move.
        """

        # Start timer to measure search time
        start_time = time.time()

        # Compute the Zobrist hash for the current board state
        board.zobrist = self.zobrist_hash(board)

        # Select the search method based on enabled flags (TT, AS, MULTICUT)
        if TT and AS:
            score, bestBoard = self.aspirational_search(
                DELTA, MAX_DEPTH, board, depth, alpha, beta
            )
        elif TT:
            score, bestBoard = self.alpha_beta_Negamax_TT(board, depth, alpha, beta)
        elif MULTICUT:
            score, bestBoard = self.multi_cut(C, M, board, depth, alpha, beta)
        elif AS:
            score, bestBoard = self.aspirational_search(
                1200, 5, board, depth, alpha, beta
            )
        else:
            score, bestBoard = self.alpha_beta_Negamax(board, depth, alpha, beta)

        # Extract the best move found during the search
        best_move = board.best_move

        # Deep copy the best board state to ensure no references are shared
        board = copy.deepcopy(bestBoard)

        # Reset pruning moves dictionary and statistics
        self.pruningMoves = {}

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Improved and detailed print statements for performance metrics
        print(f"Search completed in {elapsed_time:.4f} seconds")
        print(f"Depth searched: {depth}")
        print(f"Score of the best move: {score}")
        print(f"Number of moves evaluated: {board.move_number}")
        print(f"Number of prunings during search: {self.pruning_numbers}")
        print(f"Best move: {best_move}")
        if TT:
            print(f"Number of transposition table elements: {self.num_elements}")
            print(f"Number of transposition table collisions: {self.collisions}")
        print("-" * 50)

        # Reset collision and pruning statistics for the next search
        self.collisions = 0
        self.pruning_numbers = 0
        if RESET_TABLE:
            self.clear_table()
            self.num_elements = 0

        return board
