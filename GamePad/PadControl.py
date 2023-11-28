from cProfile import run
from datetime import datetime
import math
import copy
from operator import truediv
import numpy as np
from Entity.Bot import Bot
from GamePad.PadTool import PadTool
from threading import Timer

class PadControl:
    gridMatrix = []
    gridKeys = []
    rows = 0
    cols = 0
    bombs = []
    explosedBombs = []
    bombPosition = []
    walls = []
    balks = []
    hiddenCells = []
    goodEggs = []
    mysticEggs = []
    targetPosition = []
    bombExplodedTime = 700  # miliseconds
    bombPrepareExplodedTime = 200
    myBot = None
    playerId = None
    enemyBot = None
    enemyEgg = []
    playerEgg = []
    currentPosition = []
    lastMovingTime = None
    bombBlastCells = []
    startBombExplosedTime = 0
    bombTimerCells = []
    nextBombBlastCells = []
    explodedTimeOfBombs = {}
    currentBlastCelss = []

    # constant
    NODE_VALUE_SPACE = 0
    NODE_VALUE_WALL = 1
    NODE_VALUE_BALK = 2

    NODE_VALUE_TELE = 3
    NODE_VALUE_QUARANTINE = 4
    NODE_VALUE_DRA_EGG = 5

    SPOIL_VALUE_EGG_SPEED = 3
    SPOIL_VALUE_EGG_ATT = 4
    SPOIL_VALUE_EGG_DELAY = 5
    SPOIL_VALUE_EGG_MYSTIC = 6

    NODE_VALUE_PLAYER_EGG = 100

    MOVE_UP = '3'
    MOVE_DOWN = '4'
    MOVE_LEFT = '1'
    MOVE_RIGHT = '2'
    STOP_MOVING = 'x'
    DROP_BOMB = 'b'

    def __init__(self):
        # self.gridMatrix = [[0] * cols] * rows
        # self.rows = rows
        # self.cols = cols
        # self.playerId = playerId
        # self.tool = PadTool(rows, cols)
        pass

    def setGridSize(self, rows, cols):
        self.cols = cols
        self.rows = rows
        if len(self.gridMatrix) == 0:
            self.gridMatrix = [[0] * cols] * rows
            self.tool = PadTool(rows, cols)

    def matchingMatrix(self, matrix):
        self.gridMatrix = copy.deepcopy(matrix)
        self.rows = len(self.gridMatrix)
        self.cols = len(self.gridMatrix[0])
        self.balks = []
        for y, row in enumerate(matrix):
            for x, cellValue in enumerate(row):
                self.gridKeys.append([y, x])
                if cellValue == self.NODE_VALUE_SPACE:
                    self.hiddenCells.append([y, x])
                if cellValue == self.NODE_VALUE_BALK:
                    self.balks.append([y, x])
        # rematch blast of bomb
        for cell in self.currentBlastCelss:
            self.gridMatrix[cell[0]][cell[1]] = self.NODE_VALUE_WALL

    # reset data to empty
    def resetData(self):
        self.bombs = []
        self.explosedBombs = []
        self.walls = []
        self.balks = []
        self.goodEggs = []
        self.mysticEggs = []
        self.bombPosition = []
        self.hiddenCells = []

    def syncBombPosition(self, bombs):
        self.nextBombBlastCells = []
        for bomb in bombs:
            # self.gridMatrix[bomb['row']][bomb['col']] = self.NODE_VALUE_WALL
            # If bomb prepare to be explode - set blast treated as wall
            if bomb['playerId'] == self.myBot.playerId:
                blast = self.myBot.power
            else:
                blast = self.enemyBot.power
            bomb['blast'] = blast
            if bomb['remainTime'] <= self.bombPrepareExplodedTime:
                # if self.myBot.currentPosition != [bomb['row'], bomb['col']]:
                #     self.gridMatrix[bomb['row']][bomb['col']
                #                              ] = self.NODE_VALUE_WALL
                self.bombBlastCells += self.setBombBlast(bomb, bomb['blast'], False)
            else:
                self.nextBombBlastCells += self.setBombBlast(bomb, bomb['blast'], True)
        # get exploded bombs
        # explosedBombs = []
        # if len(self.bombs) > 0:
        #     explodedTime = datetime.now()
        #     totalBombCells = []
        #     for bomb in self.bombs:
        #         if bomb in bombs:
        #             pass
        #         else:
        #             if bomb['playerId'] == self.myBot.playerId:
        #                 blast = self.myBot.power
        #             else:
        #                 blast = self.enemyBot.power
        #             totalBombCells += self.setBombBlast(bomb, blast)
        #             bomb['blast'] = blast
        #             explosedBombs.append(bomb)
        #     # processed add Time exploded
        #     for cb in totalBombCells:
        #         key = str(cb[0]) + '_' + str(cb[1])
        #         if key not in self.explodedTimeOfBombs.keys():
        #             self.explodedTimeOfBombs[key] = [explodedTime, cb] # [time, position]
        #         else:
        #             pass
        #     # end set
        # self.explosedBombs = explosedBombs
        # reassign
        self.bombs = bombs[:]
    
    def syncPlayers(self, players):
        # process players
        for p in players:
            bot = Bot(p['id'])
            bot.initData(p)
            if self.playerId == bot.playerId:
                self.myBot = bot
                # print('Current Bot Position ', self.myBot.currentPosition)
                self.currentPosition = self.myBot.currentPosition
            else:
                self.enemyBot = bot
    
    def syncSpoils(self, spoils):
        for spoil in spoils:
            self.gridMatrix[spoil['row']][spoil['col']
                                          ] = self.NODE_VALUE_DRA_EGG
            if spoil['spoil_type'] == self.SPOIL_VALUE_EGG_MYSTIC:
                self.mysticEggs.append([spoil['row'], spoil['col']])
            else:
                self.goodEggs.append([spoil['row'], spoil['col']])
    
    def syncDragonEgg(self, draEggs):
        for item in draEggs:
            # self.gridMatrix[item['row']][item['col']] = self.NODE_VALUE_WALL
            if item['id'] != self.playerId:
                self.enemyEgg = [item['row'], item['col']]
            else:
                self.playerEgg = [item['row'], item['col']]
            # remove hidden space of player
            if [item['row'], item['col']] in self.hiddenCells:
                self.hiddenCells.remove([item['row'], item['col']])
    
    # Init data in Map
    def initData(self, map, spoils, bombs, players, draEggs):
        self.resetData()
        self.matchingMatrix(map)
        # process players
        self.syncPlayers(players)
        # dragon eggs
        self.syncDragonEgg(draEggs)
        # spoils
        self.syncSpoils(spoils)
        # process bombs
        self.syncBombPosition(bombs)

    # def setBlastToRock(self, bomb, blast):
    #     blastCells = []
    #     for i in range(blast):
    #         if [bomb['row'] + i + 1, bomb['col']] in self.gridKeys:
    #             blastCells.append([bomb['row'] + i + 1, bomb['col']])
                
    #             self.gridMatrix[bomb['row'] + i +
    #                             1][bomb['col']] = self.NODE_VALUE_WALL
    #         if [bomb['row'], bomb['col'] + i + 1] in self.gridKeys:
    #             blastCells.append([bomb['row'], bomb['col'] + i + 1])
    #             self.gridMatrix[bomb['row']][bomb['col'] +
    #                                          i + 1] = self.NODE_VALUE_WALL
    #         if [bomb['row'], bomb['col'] - i - 1] in self.gridKeys:
    #             blastCells.append([bomb['row'], bomb['col'] - i - 1])
    #             self.gridMatrix[bomb['row']][bomb['col'] -
    #                                          i - 1] = self.NODE_VALUE_WALL
    #         if [bomb['row'] - i - 1, bomb['col']] in self.gridKeys:
    #             blastCells.append([bomb['row'] - i - 1, bomb['col']])
    #             self.gridMatrix[bomb['row'] - i -
    #                             1][bomb['col']] = self.NODE_VALUE_WALL
        # Add timer return to Space
        # calculateTime = (self.bombPrepareExplodedTime + 69) /1000
        # t = Timer(calculateTime, self.setBlastToSpace(bomb, blast))
        # t.start()
        # return blastCells
    
    def setBlastToSpace(self, bomb, blast):
        for i in range(blast):
            if [bomb['row'] + i + 1, bomb['col']] in self.gridKeys:
                self.gridMatrix[bomb['row'] + i +
                                1][bomb['col']] = self.NODE_VALUE_SPACE
                cell = [bomb['row'] + i + 1, bomb['col']]
                if cell in self.currentBlastCelss:
                    self.currentBlastCelss.remove(cell)
            if [bomb['row'], bomb['col'] + i + 1] in self.gridKeys:
                self.gridMatrix[bomb['row']][bomb['col'] +
                                             i + 1] = self.NODE_VALUE_SPACE
                cell = [bomb['row'], bomb['col'] + i + 1]
                if cell in self.currentBlastCelss:
                    self.currentBlastCelss.remove(cell)
            if [bomb['row'], bomb['col'] - i - 1] in self.gridKeys:
                self.gridMatrix[bomb['row']][bomb['col'] -
                                             i - 1] = self.NODE_VALUE_SPACE
                cell = [bomb['row'], bomb['col'] - i - 1]
                if cell in self.currentBlastCelss:
                    self.currentBlastCelss.remove(cell)
            if [bomb['row'] - i - 1, bomb['col']] in self.gridKeys:
                self.gridMatrix[bomb['row'] - i -
                                1][bomb['col']] = self.NODE_VALUE_SPACE
                cell = [bomb['row'] - i - 1, bomb['col']]
                if cell in self.currentBlastCelss:
                    self.currentBlastCelss.remove(cell)
            

    # Set bomb and blast to wall
    def setBombBlast(self, bomb, blast, isSetBomb = False):
        blastCells = []
        for i in range(blast):
            if [bomb['row'] + i + 1, bomb['col']] in self.gridKeys:
                blastCells.append([bomb['row'] + i + 1, bomb['col']])
                if [bomb['row'] + i + 1, bomb['col']] in self.hiddenCells:
                    self.hiddenCells.remove([bomb['row'] + i + 1, bomb['col']])
                if isSetBomb == False:
                    self.gridMatrix[bomb['row'] + i +
                                1][bomb['col']] = self.NODE_VALUE_WALL
            if [bomb['row'], bomb['col'] + i + 1] in self.gridKeys:
                blastCells.append([bomb['row'], bomb['col'] + i + 1])
                if [bomb['row'], bomb['col'] + i + 1] in self.hiddenCells:
                    self.hiddenCells.remove([bomb['row'], bomb['col'] + i + 1])
                if isSetBomb == False:
                    self.gridMatrix[bomb['row']][bomb['col'] +
                                             i + 1] = self.NODE_VALUE_WALL
            if [bomb['row'], bomb['col'] - i - 1] in self.gridKeys:
                blastCells.append([bomb['row'], bomb['col'] - i - 1])
                if [bomb['row'], bomb['col'] - i - 1] in self.hiddenCells:
                    self.hiddenCells.remove([bomb['row'], bomb['col'] - i - 1])
                if isSetBomb == False:
                    self.gridMatrix[bomb['row']][bomb['col'] -
                                             i - 1] = self.NODE_VALUE_WALL
            if [bomb['row'] - i - 1, bomb['col']] in self.gridKeys:
                blastCells.append([bomb['row'] - i - 1, bomb['col']])
                if [bomb['row'] - i - 1, bomb['col']] in self.hiddenCells:
                    self.hiddenCells.remove([bomb['row'] - i - 1, bomb['col']])
                if isSetBomb == False:
                    self.gridMatrix[bomb['row'] - i -
                                1][bomb['col']] = self.NODE_VALUE_WALL
        # Set to Space
        # calculateTime = (self.bombPrepareExplodedTime + 100) /1000
        # t = Timer(calculateTime, self.setBlastToSpace(bomb, blast))
        # t.start()
        return blastCells

    # Reassign bomb and blast to wall
    def regenerateBombs(self):
        self.bombPosition = []
        self.bombBlastCells = []
        self.nextBombBlastCells = []
        for bomb in self.bombs:
            if bomb['remainTime'] <= self.bombPrepareExplodedTime:
                self.bombPosition.append([bomb['row'], bomb['col']])
                self.bombBlastCells += self.setBombBlast(bomb, bomb['blast'], False)
            else:
                self.nextBombBlastCells += self.setBombBlast(bomb, bomb['blast'], True)

        # for bomb in self.explosedBombs:
        #     self.bombPosition.append([bomb['row'], bomb['col']])
        #     self.bombBlastCells.append([bomb['row'], bomb['col']])
        #     self.bombBlastCells += self.setBombBlast(bomb, bomb['blast'], False)

        currentBlastCells = self.bombBlastCells
        # currentTime = datetime.now()
        # for key in list(self.explodedTimeOfBombs):
        #     diffTime = currentTime - self.explodedTimeOfBombs[key][0]
        #     # End time exploded
        #     pos = self.explodedTimeOfBombs[key][1]
        #     if diffTime.total_seconds() * 1000 > self.bombExplodedTime:
        #         self.gridMatrix[pos[0]][pos[1]] = self.NODE_VALUE_SPACE
        #         del self.explodedTimeOfBombs[key]
        #     else: # add to current blast
        #         currentBlastCells.append(pos)
        #         self.gridMatrix[pos[0]][pos[1]] = self.NODE_VALUE_WALL
        # end for
        self.currentBlastCelss = currentBlastCells

    # Define way to go
    def makeDecision(self):
        if self.myBot == None:
            # print('Init data have not done -- waiting')
            return
        if self.isDangerousZone():
            return self.runToHide()
        return self.runToEat()

    # Check if in blast of bomb
    def isDangerousZone(self):
        self.regenerateBombs()
        if self.currentPosition in self.bombPosition:
            return True
        if self.myBot.currentPosition in self.bombBlastCells:
            return True
        if self.myBot.currentPosition in self.currentBlastCelss:
            return True
        if self.myBot.currentPosition in self.nextBombBlastCells:
            return True
        return False
    # Check if around cell is teleport
    def isNearTeleport(self, position):
        aroundCells = self.getAreaAroundPosition(position, 1)
        for cell in aroundCells:
            if self.gridMatrix[cell[0]][cell[1]] == self.NODE_VALUE_TELE:
                return True
        return False

    def getNearestItem(self, fromItem, eggArr):
        distance = 0
        if len(eggArr) == 0:
            return None
        nearest = eggArr[0]
        for des in eggArr:
            total = math.pow(des[0] - fromItem[0], 2) + \
                math.pow(des[1] - fromItem[1], 2)
            itemDistance = math.sqrt(total)
            if distance == 0 or itemDistance <= distance:
                nearest = des
                distance = itemDistance
        return nearest

    def findAvaiableCell(self, eggArr, newPosition=None, allowBalk=False, withoutBlast=False):
        # TODO need to find with blast 1st
        # If dont have any way find without blast care
        if len(eggArr) == 0:
            return None
        if withoutBlast:
            blastCells = []
        else:
            blastCells = self.currentBlastCelss[:]
        item = self.getNearestItem(self.myBot.currentPosition, eggArr)
        path = self.tool.findPath(
            self.gridMatrix, self.myBot.currentPosition, item, self.rows, self.cols, allowBalk, blast=blastCells)
        if len(path) > 1:
            newPosition = item
            return path
        elif len(eggArr) > 1:
            eggArr.remove(item)
            return self.findAvaiableCell(eggArr, newPosition, allowBalk)
        return []

    def runToEat(self):
        newPosition = None
        # find nearest Egg with posible path
        if len(self.goodEggs):
            print('Finding good Eggs')
            runningPath = self.findAvaiableCell(self.goodEggs[:], newPosition)
            if len(runningPath) > 1:
                print('Running to goodEggs ', newPosition)
                return self.getDirectionCommand(runningPath, False)
        # Mystic
        if len(self.mysticEggs):
            print('Finding Mystic Eggs')
            runningPath = self.findAvaiableCell(
                self.mysticEggs[:], newPosition)
            if len(runningPath) > 1:
                print('Running to mysticEggs ', newPosition)
                return self.getDirectionCommand(runningPath, False)
        # Destroy balk
        if len(self.balks):
            print('Finding Balk')
            runningPath = self.findAvaiableCell(
                self.balks[:], newPosition, allowBalk=True)
            if len(runningPath) > 1:
                print('Running to balk ', newPosition)
                return self.getDirectionCommand(runningPath, True)
        # find dragon
        print('Finding Dragon')
        # blastCells = np.concatenate(self.currentBlastCelss[:], self.bombBlastCells[:])
        path = self.tool.findPath(
            self.gridMatrix, self.myBot.currentPosition, self.enemyEgg, self.rows, self.cols, allowBalk=True, blast=self.currentBlastCelss[:])
        if len(path) > 1:
            print('Running to dragon ', newPosition)
            return self.getDirectionCommand(path, True)
        # Default stop
        return self.STOP_MOVING

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
        # Remove dangerous cell
        # for cell in cells:
        #     if cell not in self.hiddenCells:
        #         cells.remove(cell)
        #     if cell in self.bombBlastCells or cell in self.bombPosition:
        #         cells.remove(cell)
        return cells

    def runToHide(self, pos=None, isSetBomb = True, distance = 0, isLoop = False):
        if pos == None:
            pos = self.myBot.currentPosition
        # calculate blast of new bomb
        if distance == 0:
            distance = self.myBot.power + 1
        aroundCells = self.hiddenCells[:] #self.getAreaAroundPosition(pos, distance)
        if isSetBomb:
            newBlastCells = self.setBombBlast({
                'row': pos[0], 'col': pos[1]}, self.myBot.power, True)
            safeCells = [item for item in aroundCells if item not in newBlastCells]
        else:
            safeCells = aroundCells
        # restrict bomb explosed cells
        safeCells2 = [item for item in safeCells if item not in self.bombBlastCells \
            and item not in self.nextBombBlastCells
            and item not in self.currentBlastCelss]
        runningPath = self.findAvaiableCell(safeCells2)
        if len(runningPath) > 1:
            return self.getDirectionCommand(runningPath, allowBalk=False, isLoop=isLoop) + self.STOP_MOVING
        else:
            # go more and more
            # return self.runToHide(pos, isSetBomb, distance + 1)
            return self.STOP_MOVING
    
    def getSafeCell(self, pos, distance = 0, isSetBomb = False):
        if pos == None:
            pos = self.myBot.currentPosition
        # calculate blast of new bomb
        if distance == 0:
            distance = self.myBot.power + 1
        aroundCells = self.getAreaAroundPosition(pos, distance)
        if isSetBomb:
            newBlastCells = self.setBombBlast({
                'row': pos[0], 'col': pos[1]}, self.myBot.power, True)
            safeCells = [item for item in aroundCells if item not in newBlastCells]
        else:
            safeCells = aroundCells
        # restrict bomb explosed cells
        safeCells2 = [item for item in safeCells if item not in self.bombBlastCells and item not in self.nextBombBlastCells]
        runningPath = self.findAvaiableCell(safeCells2)

    def reversePathCmd(self, path):
        reversePath = np.flip(path)
        cmd = self.getDirectionCommand(reversePath)
        return cmd
    
    def getDirectionCommand(self, path, allowBalk=False, isLoop = False):
        strMove = None
        # Path is (y, x) -> y = row x = col
        if (len(path) <= 1):
            return strMove
        else:
            strMove = ''
        currentCell = path[0]
        path2 = copy.deepcopy(path[1:])
        for cell in path2:
            if self.gridMatrix[cell.y][cell.x] == self.NODE_VALUE_BALK:
                if isLoop:
                    strMove += self.STOP_MOVING
                else:
                    strMove += self.DROP_BOMB + self.runToHide(pos=[currentCell.y, currentCell.x], isSetBomb=True)
                return strMove
            if cell.x > currentCell.x:
                strMove += self.MOVE_RIGHT
                currentCell = cell
            elif cell.x < currentCell.x:
                strMove += self.MOVE_LEFT
                currentCell = cell
            elif cell.y > currentCell.y:
                strMove += self.MOVE_DOWN
                currentCell = cell
            elif cell.y < currentCell.y:
                strMove += self.MOVE_UP
                currentCell = cell
            # if isLoop == False:
            #     strMove += self.STOP_MOVING
            if self.isNearTeleport([cell.y, cell.x]):
                strMove += self.STOP_MOVING
        print('Next move direction: ' + strMove)
        return strMove
