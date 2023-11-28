
class Bot:
  def __init__(self, playerId):
      self.playerId = playerId
  def initData(self, data):
    self.currentPosition = [data['currentPosition']['row'],data['currentPosition']['col']]
    self.score = data['score']
    self.lives = data['lives']
    self.speed = data['speed']
    self.power = data['power']
    self.delay = data['delay']
    self.quarantine = data['quarantine']
    self.dragonEggSpeed = data['dragonEggSpeed']
    self.dragonEggAttack = data['dragonEggAttack']
    self.dragonEggDelay = data['dragonEggDelay']
    self.dragonEggMystic = data['dragonEggMystic']
    # self.gstEggBeingAttacked = data['gstEggBeingAttacked']
    