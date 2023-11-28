import numpy as np
import copy
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.finder.dijkstra import DijkstraFinder
from pathfinding.core.diagonal_movement import DiagonalMovement


class PadTool:
    graph = []
    MOVE_UP = '3'
    MOVE_DOWN = '4'
    MOVE_LEFT = '1'
    MOVE_RIGHT = '2'
    STOP_MOVING = 'x'
    DROP_BOMB = 'b'

    # constant
    NODE_VALUE_SPACE = 0
    NODE_VALUE_WALL = 1
    NODE_VALUE_BALK = 2

    NODE_VALUE_TELE = 3
    NODE_VALUE_QUARANTINE = 4
    NODE_VALUE_DRA_EGG = 5

    finder = None

    def __init__(self, rows, cols, method='Dijkstra'):
        self.grid = np.array([[0] * cols] * rows)
        self.cols = cols
        self.rows = rows
        self.graph = []
        if method == 'Astar':
            self.finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
        else:
            self.finder = DijkstraFinder(
                diagonal_movement=DiagonalMovement.never)

    def getAreaAroundPosition(self, position, distance):
        cells = []
        for i in range(distance):
            # process for rows
            # keep row
            for y in range(distance):
                if position[1] + y + 1 < self.cols:
                    cells.append([position[0], position[1] + y + 1])
                if position[1] - y - 1 >= 0:
                    cells.append([position[0], position[1] - y - 1])
            if (position[0] + i + 1) < self.rows:
                # keep cols
                cells.append([position[0] + i + 1, position[1]])
                # process cols
                for y in range(distance):
                    if position[1] + y + 1 < self.cols:
                        cells.append(
                            [position[0] + i + 1, position[1] + y + 1])
                    if position[1] - y - 1 >= 0:
                        cells.append(
                            [position[0] + i + 1, position[1] - y - 1])
            if (position[0] - i - 1) >= 0:
                cells.append([position[0] - i - 1, position[1]])
                # process cols
                for y in range(distance):
                    if position[1] + y + 1 < self.cols:
                        cells.append(
                            [position[0] - i - 1, position[1] + y + 1])
                    if position[1] - y - 1 > 0:
                        cells.append(
                            [position[0] - i - 1, position[1] - y - 1])
            # end process
        self.aroundCells = cells
        return cells

    def convertToGraphValue(self, values, allowBalk = False):
        self.graph = copy.deepcopy(values)
        if allowBalk == False:
            self.convertValueFromTo([
                            self.NODE_VALUE_BALK,
                            self.NODE_VALUE_WALL,
                            self.NODE_VALUE_QUARANTINE,
                            self.NODE_VALUE_TELE
                ], -1)
            self.convertValueFromTo([
                            self.NODE_VALUE_SPACE, 
                            self.NODE_VALUE_DRA_EGG
                ], 2)
        else:
            self.convertValueFromTo([
                            self.NODE_VALUE_WALL,
                            self.NODE_VALUE_QUARANTINE,
                            self.NODE_VALUE_TELE
                ], -1)
            self.convertValueFromTo([
                            self.NODE_VALUE_SPACE, 
                            self.NODE_VALUE_DRA_EGG,
                            self.NODE_VALUE_BALK,
                ], 2)

    def convertValueFromTo(self, fromArray, toValue):
        for y, row in enumerate(self.graph):
            for x, cellValue in enumerate(row):
                if cellValue in fromArray:
                    self.graph[y][x] = toValue
    
    def convertValueFromPositionTo(self, fromPos, toValue, previousValue = []):
        index = 0
        for y, row in enumerate(self.graph):
            for x, cellValue in enumerate(row):
                if [y, x] in fromPos and toValue != None:
                    self.graph[y][x] = toValue
                    previousValue.append(cellValue)
                    index += 1
                elif [y, x] in fromPos and toValue == None:
                    self.graph[y][x] = previousValue[index]
                    index += 1
        

    def findPath(self, values, fromPos, toPos, rows, cols, allowBalk = False, blast = []):
        if fromPos == toPos or toPos == None or fromPos == None:
            return []
        self.graph = [[0] * cols] * rows
        self.convertToGraphValue(values, allowBalk)
        grid = Grid(matrix=self.graph[:])
        # print('Finding way:::: ', fromPos, toPos)
        try:
            # Path is (y, x) -> y = row x = col node(self, x, y) -> GridNode:
            start = grid.node(fromPos[1], fromPos[0])
            end = grid.node(toPos[1], toPos[0])
            # Check with blast
            previousValue = []
            if len(blast) > 0:
                self.convertValueFromPositionTo(blast, -2, previousValue)
                path, runs = self.finder.find_path(start, end, grid)
                # Revert to find
                if len(path) < 1:
                    return [fromPos]
                    # self.convertValueFromPositionTo(blast, None, previousValue)
                    # path, runs = self.finder.find_path(start, end, grid)
            else:
                path, runs = self.finder.find_path(start, end, grid)
        except Exception as e:
            print('findPath errorrr -------:', e, fromPos, toPos)
            return []
        path = np.array(path)
        # self.printGraphPath(fromPos, toPos, path)
        return path

    def printGraphPath(self, fromPos, toPos, path):
        # print('Start print map in grid')
        pathArr = []
        for item in path:
            pathArr.append([item.y, item.x])
        # print(self.graph)
        for x, row in enumerate(self.graph):
            for y, col in enumerate(row):
                if [x, y] == fromPos:
                    print('S', end=' ')
                elif [x, y] == toPos:
                    print('E', end=' ')
                elif [x, y] in pathArr:
                    print('.', end=' ')
                elif col <= 0:
                    print('0', end=' ')
                else:
                    print(col, end=' ')
            print('')

