import logging
import time

"""Plays the game of battleship.

Public interface
play()
"""
class Player:
    def __init__(self, playerBoard, commandDriver, shotSelector, pauseTime, manualShot):
        """Constructor.

        Arguments
        playerBoard - Player board with ship placements.
        commandDriver - Command driver to issue commands. 
        shotSelector -  Shot selector to select shots to take.
        pauseTime - Time to wait between turns.
        manualShot - Wait for user input to take a shot.
        """
        self.playerBoard = playerBoard
        self.commandDriver = commandDriver
        self.shotSelector = shotSelector
        self.pauseTime = pauseTime
        self.manualShot = manualShot
        
    def start(self):
        """Starts a new game.

        Returns 
        gameId - The id of the game that was just joined.
        """
        self.gameId = self.commandDriver.start(self.playerBoard)
        return self.gameId

    def join(self, gameId):
        """Joins an existing game.
        
        Arguments
        gameId - The id of the game to join.
        """
        self.gameId = self.commandDriver.join(self.playerBoard, gameId)

    def play(self):
        """The gameplay loop:
        while the game is playing
          if it's my turn
            select a shot
            update the enemy's board with the results of the shot
          else
            wait for my turn
        """
        while True:
            gameState, myTurn = self.commandDriver.status(self.gameId)
            if gameState == "won" or gameState == "lost":
                logging.info("I %s!" % gameState)
                break
            if gameState == "playing" and myTurn:
                if self.manualShot:
                    input("take a shot")
                shot = self.shotSelector.selectShot()
                hit, sunk = self.commandDriver.fire(self.gameId, shot)
                self.shotSelector.shotResult(shot, hit, sunk)
            else:
                time.sleep(self.pauseTime)
