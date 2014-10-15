import logging
import time

"""Plays the game of battleship.

Public interface
play()
"""
class Player:
    def __init__(self, playerBoard, commandDriver, shotSelector, pauseTime):
        """Constructor.

        Arguments
        playerBaord - Player board with ship placements.
        commandDriver - Command driver to issue commands. 
        shotSelector -  Shot selector to select shots to take.
        pauseTime - Time to wait between turns.
        """
        self.playerBoard = playerBoard
        self.commandDriver = commandDriver;
        self.shotSelector = shotSelector
        self.pauseTime = pauseTime
        
    def play(self):
        """The gameplay loop:
        join the game
        while the game is in progress
          wait for my turn
          select a shot
          update the enemy's board with the results of the shot
        """
        gameId = self.commandDriver.join(self.playerBoard)
        while True:
            gameStatus, myTurn = self.commandDriver.status(gameId)
            if gameStatus != "playing":
                logging.info("I %s!" % gameStatus)
                break
            if myTurn:
                shot = self.shotSelector.selectShot()
                hit, sunk = self.commandDriver.fire(gameId, shot)
                self.shotSelector.shotResult(hit, sunk)
            else:
                time.sleep(self.pauseTime)
