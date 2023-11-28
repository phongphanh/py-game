from queue import Queue
import queue
from GamePad.PadControl import PadControl
import socketio
from apscheduler.schedulers.background import BackgroundScheduler
from GamePad.RepeatTimer import RepeatTimer
from multiprocessing import Process
import threading


from datetime import datetime
import copy


class GameController:
    sio = socketio.Client()
    sid = ''
    serverUrl = ''
    isRunningGame = False
    gameStatus = None
    isStartGame = False
    receiveGameId = ''
    receivePlayerId = ''
    mapInfo = {}
    EVENT_JOIN_GAME = 'join game'
    EVENT_DRIVE_PLAYER = 'drive player'
    EVENT_TICKTACK_PLAYER = 'ticktack player'
    currentPath = ''
    nextDestination = []
    previousPosition = []
    gameControl = PadControl()
    isCirclePlay = False
    bombScheduler = None
    isAddBombJob = False
    isAddJob = False
    isDropBomb = False
    timeDropBomb = None
    movingTimeDelay = 3  # for 250 miliseconds
    currentTag = ''
    isStartMoving = False
    PLAYER_TAG_MOVING = 'player:start-moving'
    PLAYER_TAG_STOP = 'player:stop-moving'
    PLAYER_TAG_ISOLATED = 'player:be-isolated'
    PLAYER_TAG_BANNED = 'player:moving-banned'
    PLAYER_TAG_BG = 'player:be-isolated'
    BOMB_TAG_EXPLOSED = 'bomb:explosed'
    timeToSendEmit = 200
    lastSendEmit = None
    numberOfJob = 0
    isJobRunning = False
    
    dataQueue = None

    GAME_TAG_UPDATE = 'update-data'

    def __init__(self, serverUrl):
        self.tag = 'Gamer'
        self.serverUrl = serverUrl
        # self.dataQueue = queue.Queue()
        # threading.Thread(target=self.workerUpdateData, daemon=True).start()

    def connect(self):
        self.__initSocketHandler__()
        self.sio.connect(self.serverUrl)
        pass

    def joinGame(self, gameId, playerId):
        self.sio.emit('join game', {
            'game_id': gameId,
            'player_id': playerId
        })
        self.receivePlayerId = playerId
        print('Connecting to game')
        self.isRunningGame = True
        self.__initEventHandler__()
        while (self.isRunningGame):
            # do smt here
            pass

    def __initSocketHandler__(self):
        @self.sio.event
        def connect():
            print('Connect to server ' + self.serverUrl)

        @self.sio.event
        def connect_error():
            print('Connect to server fail' + self.serverUrl)
            self.endGame()

        @self.sio.event
        def disconnect():
            self.isRunningGame = False
            if self.sio:
                self.sio.disconnect()
            self.isStartGame = False
            self.endGame()
            print('Disconnect from server' + self.serverUrl)
    # Update data to map
    def workerUpdateData(self):
        while True:
            if self.dataQueue.qsize() > 0:
                item = self.dataQueue.get()
                self.syncMapData(item)
                print(f'Working on {item}')
                print(f'Finished {item}')
                self.dataQueue.task_done()
            else:
                print('Nothing in queue......')        
    
    def syncMapData(self, roomInfo):
        self.gameControl.setGridSize(
            roomInfo['map_info']['size']['rows'], roomInfo['map_info']['size']['cols'])
        self.gameControl.initData(roomInfo['map_info']['map'], roomInfo['map_info']['spoils'], roomInfo['map_info']['bombs'],
                                  roomInfo['map_info']['players'], roomInfo['map_info']['dragonEggGSTArray'])

    def initAllJob(self):
        self.jobMovingOut()
        self.initBombScheduler()

    def sendMovingCommand(self, directionCmd):
        currentTime = datetime.now()
        if self.lastSendEmit != None:
            diffTime = currentTime - self.lastSendEmit
            # print('Compare executed time ', diffTime.total_seconds(), self.lastSendEmit, currentTime)
            timeDelayEmit = self.gameControl.myBot.speed * 1.5
            if diffTime.total_seconds() * 1000 < timeDelayEmit \
                    and not self.gameControl.isDangerousZone():
                print('Dont emit ---------> ', directionCmd)
                return
        print('Current Game Tag >>>> ', self.currentTag)
        if directionCmd == None or directionCmd == '':
            print('Nothing to move')
            directionCmd = self.gameControl.runToHide()
        # Send to server
        self.sio.emit(self.EVENT_DRIVE_PLAYER, {
            'direction': directionCmd
        })
        self.lastSendEmit = currentTime
        print('Send move cmd ', directionCmd)

    def dropBomb(self):
        # if self.isStartGame == False:
        #     print('Game is not started -------')
        #     return
        print('Drop bomb & runnning')
        # runningMan = self.gameControl.runningMan()
        # dropCmd = self.gameControl.movingToSpaceOfBalk()
        # self.sendMovingCommand(dropCmd)
        # self.isDropBomb = True
        # self.timeDropBomb = datetime.now()

    def funcTimeOut(self):
        directionCmd = self.gameControl.makeDecision()
        self.sendMovingCommand(directionCmd)
    
    def walkingInTheMoon(self):
        if self.isStartGame == False:
            print('Game is not started -------')
            return
        print('Normal moving - walkingInTheMoon ')
        
        if self.gameControl != None:
            try:
                self.isJobRunning = True
                directionCmd = self.gameControl.makeDecision()
                self.sendMovingCommand(directionCmd)
                # action_process = Process(target=self.funcTimeOut)
                # action_process.start()
                # action_process.join(timeout=1/2)
                # action_process.terminate()
                self.isJobRunning = False
            except Exception as e:
                print('Exception: ', e, e.__traceback__)
        else:
            print(self.gameControl, self.isJobRunning)
            print('Gamecontrol is not ready')

    def endGame(self):
        if self.bombScheduler:
            self.bombScheduler.shutdown()
        if self.sio:
            self.sio.disconnect()

    def jobMovingOut(self):
        # print test play withou scheduler
        # return
        print('Current game status >', self.gameStatus)
        if (self.bombScheduler != None):
            scheduler = self.bombScheduler
        else:
            scheduler = BackgroundScheduler()
            self.bombScheduler = scheduler
        if self.isAddJob == None or self.isAddJob == False:
            scheduler.add_job(self.walkingInTheMoon, 'interval',
                              seconds=0.3, max_instances=8)
            self.isAddJob = True
            scheduler.start()
        self.bombScheduler = scheduler

    def initBombScheduler(self):
        # scheduler = BackgroundScheduler()
        # if (self.bombScheduler != None):
        #     scheduler = self.bombScheduler
        # else:
        #     self.bombScheduler = scheduler
        # if self.isAddBombJob == False:
        #     scheduler.add_job(self.dropBomb, 'interval', seconds=1)
        #     self.isAddBombJob = True
        #     scheduler.start()
        pass

    def __initEventHandler__(self):
        @self.sio.on(self.EVENT_JOIN_GAME)
        def join_game(data):
            self.receiveGameId = data.get('game_id')
            self.receivePlayerId = data.get('player_id')
            if (data.get('player_id') in self.receivePlayerId):
                self.receivePlayerId = data.get('player_id')
                self.gameControl.playerId = self.receivePlayerId
            self.initAllJob()

        @self.sio.on(self.EVENT_TICKTACK_PLAYER)
        def ticktack_player(data):
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("ticktack_player Current Time =", current_time)
            self.mapInfo = data.get('map_info')
            self.syncMapData(data)
            # self.dataQueue.put(data)
            self.isStartGame = True
            self.gameStatus = data.get('gameStatus')
            print('Game Status ', self.gameStatus)
            # self.currentTag = data['tag']
            # if self.currentTag == 'update-data':
            #     self.syncMapData(data)
            # elif self.currentTag in [
            #     'bomb:explosed',
            #     'bomb:setup'
            # ]:
            #     self.gameControl.syncBombPosition(self.mapInfo['bombs'])
            # elif 'player:' in self.currentTag:
            #     self.gameControl.syncPlayers(self.mapInfo['players'])
            #     if self.gameControl.isDangerousZone() and self.currentTag == 'player:start-moving':  # start in a cell
            #         self.gameControl.runToHide()
            # else:
            #     self.syncMapData(data)
           
            # self.walkingInTheMoon()
            # decision to move
            
            # if data.get('gameStatus') == None and self.isStartGame == True:
            #     self.isRunningGame = False
            #     self.endGame()

        @self.sio.on(self.EVENT_DRIVE_PLAYER)
        def drive_player(data):
            # print(data)
            if data['player_id'] == self.receivePlayerId:
                self.gameControl.currentDirection = data['direction']
                print('Drive player receive from server')
                print(data)
                # Check if drop bomb then run
                # if 'b' in data['direction'] or data['direction'] == '':
                #     # run run
                #     runSoFast = self.gameControl.runToHide()
                #     self.sendMovingCommand(runSoFast)
