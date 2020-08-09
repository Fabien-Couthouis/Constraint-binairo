# Constraint-binairo

Takuzu, also known as Binairo, is a logic puzzle involving placement of two symbols, often 1s and 0s, on a rectangular grid. The objective is to fill the grid with 1s and 0s, where there is an equal number of 1s and 0s in each row and column and no more than two of either number adjacent to each other. Additionally, there can be no identical rows or columns. Similar to Sudoku, each puzzle begins with several squares in the grid already filled.


This repository contains [a script](binairo.py) to generate binero grids with solution thanks to contraint programming and SAT solver built in [OR-TOOLS](https://developers.google.com/optimization).


# Requirements
```
pip install ortools
```
