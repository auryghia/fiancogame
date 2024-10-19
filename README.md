**Intelligent Player for "Fianco" using Alpha-Beta Pruning and Negamax**

This project implements an intelligent player for the Italian game "Fianco"(http://www.di.fc.ul.pt/~jpn/gv/fianco.htm) using the Alpha-Beta Pruning algorithm with Negamax notation. The implementation leverages Pygame for visualizing the game and Zobrist hashing for efficient board state evaluation. The goal of this project is to participate in the Intelligence and Search Games competition at Maastricht University.

## Features

- **Negamax with Alpha-Beta Pruning**: Efficient move searching.
- **Transposition Table**: To store previously evaluated boards.
- **Ordening**: Optimizes search using: Killer Moves and History Heuristic.
- **Dynamic Deepening when Capturing**: Adjusts search depth based on the game state.
- **Forward Pruning**: with Multi-Cut algorithm.
- **Aspirational Search**: To improve the pruning.

## Instructions

To start the automatic player, press **N** when it’s their turn.
