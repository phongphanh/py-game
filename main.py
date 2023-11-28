
# import pygame
# import pygame_menu
from Controller.GameController import GameController

#build window
# pygame.init()
# clock = pygame.time.Clock()
# (width, height) = (600, 400)
# screen = pygame.display.set_mode((width, height))
# background_colour = (255,255,255)
# screen.fill(background_colour)
# pygame.display.flip()
# pygame.display.set_caption('GST Codefest 2023')

# menu = pygame_menu.Menu()

serverUrl = input('Server: ')
if serverUrl == '':
  serverUrl = 'http://localhost'
playerId = input('Player Id: ')
if playerId == '':
  playerId = 'player1-xxx'
elif playerId == '2':
  playerId = 'player2-xxx'

gameId = input('Game Id: ')

gameContrl = GameController(serverUrl)
gameContrl.connect()
gameContrl.joinGame(gameId, playerId)
running = True
