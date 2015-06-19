import random
import heapq
import logging
from collections import namedtuple

"""Stores x and y values of the enemy board positions."""
Coordinates = namedtuple('Coordinates', 'x y')
"""Stores information about a sinking ship, the shot that caused it to start sinking and its size."""
SinkingShip = namedtuple('SinkingShip', 'bullsEye size')

"""OPEN - no information is known, open for shot selection
HIT - shot hit a ship
BULLSEYE - shot sunk a ship
SUNK - sunk ship
MISS - shot missed a ship
"""
class BoardState:
    # Used to represent the state of the enemy board. 
    OPEN = 0
    HIT = -1
    BULLSEYE = -2
    SUNK = -3
    MISS = -4
    
"""Directions for the various searches used by MappingShotSelector."""
class Direction:
    North = Coordinates(-1, 0)
    South = Coordinates(1, 0)
    East = Coordinates(0, 1)
    West = Coordinates(0, -1)
    
"""Selects the next shot to take at the enemy.  This class needs to be overridden, child classes will
implement specific strategies.

Public interface
selectShot()
shotResult(shot, hit, sunk)

"""
class ShotSelector:        
    def __init__(self, boardDimensions, shipsAfloat):
        """Builds the enemy board.
        
        Arguments
        boardDimensions - dimensions of the (square) enemy board.
        shipsAfloat - the size and counts of the initial enemy fleet.
        """
        self.enemyBoard = [[BoardState.OPEN for j in range(boardDimensions)] for i in range(boardDimensions)]
        self.boardDimensions = boardDimensions
        self.shipsAfloat = shipsAfloat
        
    def printShipsAfloat(self):
        """For debugging purposes, prints the remaining ships afloat.
        """
        logging.debug("ships afloat")
        sb = []
        for size in self.shipsAfloat:
            number = self.shipsAfloat[size]
            sb.append(str(size))
            sb.append(":")
            sb.append(str(number))
            sb.append(" ")
        logging.debug("".join(sb))
        
    def printBoard(self):
        """For debugging purposes, prints the board.
        """
        logging.debug("enemy board")
        for i in range(self.boardDimensions):
            sb = []
            for j in range(self.boardDimensions):
                sb.append(str(self.enemyBoard[i][j]))
                sb.append(" ")
            logging.debug("".join(sb))
            
    def selectShot(self):
        """Selects the next shot to take.

        Returns 
        A shot of the form LetterNumber.
        """
        raise NotImplementedError("Subclass needs to implement this")
    
    def shotResult(self, shot, hit, sunk):
        """Updates internal state given the results of a shot.
        
        Arguments
        shot - Shot of the form LetterNumber.
        hit - True, if the shot was a hit.
        sunk - Size of the sunk ship, if the shot sunk it.
        """
        logging.debug("shot result: %s, hit: %d, sunk: %d" % (shot, hit, sunk))
        coordinates = self.mapToCoordinates(shot)
        # If a ship was sunk, remove it from the fleet.
        if sunk:
            sunk = str(sunk)
            assert(self.shipsAfloat[sunk] > 0)
            self.shipsAfloat[sunk] -= 1
            # Remove any counts that went to 0.
            if self.shipsAfloat[sunk] == 0:
                del(self.shipsAfloat[sunk])
            self.enemyBoard[coordinates.x][coordinates.y] = BoardState.BULLSEYE
        else:
            if hit:
                self.enemyBoard[coordinates.x][coordinates.y] = BoardState.HIT
            else:
                self.enemyBoard[coordinates.x][coordinates.y] = BoardState.MISS
    
    def mapToCoordinates(self, shot):
        """Maps a shot to x and y coordinates."""
        toks = shot.split("-")
        return Coordinates(ord(toks[0]) - ord("A"), int(toks[1]) - 1) 
        
    def mapToShot(self, coordinates):
        """Maps x and y coordinates to a shot."""
        return chr(coordinates.x + ord("A")) + "-" + str(coordinates.y + 1)
    
"""Implements a random shot selection strategy."""     
class RandomShotSelector(ShotSelector):
    def __init__(self, boardDimensions, shipsAfloat):
        """Builds the enemy board and keeps tracks of the remaining coordinates. 
        
        Arguments
        boardDimensions - dimensions of the (square) enemy board.
        shipsAfloat - the size and counts of the initial enemy fleet.
        """ 
        ShotSelector.__init__(self, boardDimensions, shipsAfloat)
        self.remainingCoordinates = [Coordinates(i, j) for i in range(self.boardDimensions) for j in range(self.boardDimensions)]
        random.shuffle(self.remainingCoordinates)

    def selectShot(self):
        """Picks a random coordinate from the coordinates remaining and returns it."""
        shot = self.mapToShot(self.remainingCoordinates.pop())
        logging.debug("select shot: %s" % (shot))
        return shot
    
    def shotResult(self, shot, hit, sunk):
        ShotSelector.shotResult(self, shot, hit, sunk)

"""Implements a mapping strategy.
Shots are selected by weighting the board with all remaining enemy ships in all possible positions and picking the highest 
weighted coordinates.  The more "ways" an enemy ship can be positioned over particular coordinates, the higher the weight 
of the coordinates.  Ship positions that overlay previously hit coordinates are given extra weight.  When a ship is sinking, 
all possible ways that a ship of that size can be sunk are tried.  If only one way is found, the ships coordinates are marked
as SUNK to preclude them in subsequent shot selections.  If there is more than one way a sinking ship can be sunk, the coordinates are 
left as-is with the hope being that the next sinking ship will provide enough information to sink this ship.  Think of it like
dominoes toppling. 
"""
class MappingShotSelector(ShotSelector):
    def __init__(self, boardDimensions, shipsAfloat):
        """Builds the enemy board and keeps tracks of the remaining shots. 
        
        Arguments
        boardDimensions - dimensions of the (square) enemy board.
        initialFleet - the sizes and number of ships in the initial enemy fleet. 
        """
        ShotSelector.__init__(self, boardDimensions, shipsAfloat)
        self.shipsToSink = []
        
    def printShipsToSink(self):
        """For debugging purposes, prints the ships that are sinking.
        """
        sb = []
        for sinkingShip in self.shipsToSink:
            shot = self.mapToShot(sinkingShip.bullseye)
            sb.append(str(shot))
            sb.append(":")
            sb.append(str(sinkingShip.size))
            sb.append(" ")
        logging.debug("".join(sb))
                             
    def selectShot(self):
        """ Weights the board and returns the highest weighted shot.

        Returns 
        A shot of the form LetterNumber.
        """
        self.weightBoard()
        self.printBoard()
        bestCoordinates = self.selectBestCoordinates()
        shot = self.mapToShot(bestCoordinates)
        logging.debug("select shot: %s" % (shot))
        return shot

    def weightBoard(self):
        """ Weights the board by placing all remaining ships in all possible positions.  The
        more ways a ship can be placed over a particular set of coordinates, the higher the weight.
        Positions that overlay previous hits are given extra weight.
        """
        directions = (Direction.East, Direction.South)
        for size, count in self.shipsAfloat.items():
            size = int(size)
            for i in range(self.boardDimensions):
                for j in range(self.boardDimensions):
                    for direction in directions:
                        coordinates = Coordinates(i, j)
                        self.positionAndWeightShip(coordinates, size, count, direction)
                    
    def positionAndWeightShip(self, coordinates, size, weight, direction):
        self.weightShip(coordinates, size, weight, direction)
        
    def weightShip(self, coordinates, size, weight, direction):
        self.weightShipSearch(coordinates, size, weight, direction, 0)
        
    def weightShipSearch(self, coordinates, size, weight, direction, hitWeight):
        """ Recursive function that positions a ship in a particular direction and applies
        the weights.
        
        Arguments
        coordinates - The coordinate to check.
        size - The size of the ship.
        weight - The weight to apply if this coordinate can hold a ship.
        direction - The direction to move as the ship is being placed.
        hitWeight - The extra amount of weight to add if the ship overlays previously hit
        coordinates.
        
        Returns
        result - True if the ship can be placed, False if it can't.
        hitWeight - The extra hit weight to apply as the recursive stack unwinds.
        """
        if size == 0:
            # Successfully searched the required size.
            return True, hitWeight        
        if coordinates.x < 0 or coordinates.y < 0 or coordinates.x == self.boardDimensions or coordinates.y == self.boardDimensions:
            # Can't go off the board.
            return False, 0
        if self.enemyBoard[coordinates.x][coordinates.y] < BoardState.HIT:
            # This search is all for naught since we can't possibly have a ship at this position.
            return False, 0
        if self.enemyBoard[coordinates.x][coordinates.y] == BoardState.HIT:
            # Weigh searches with hits already in them over searches without them.  This is to 
            # direct the shot selection toward coordinates with hits already near them.
            hitWeight += 10
        # Move to the next set of coordinates on the board.
        result, hitWeight = self.weightShipSearch(Coordinates(coordinates.x + direction.x, coordinates.y + direction.y),
                                                  size - 1, weight, direction, hitWeight)
        if result:
            # A entire ship can fit, weight the coordinate appropriately.
            if self.enemyBoard[coordinates.x][coordinates.y] >= BoardState.OPEN:
                self.enemyBoard[coordinates.x][coordinates.y] += (weight + hitWeight)
        return result, hitWeight
    
    def selectBestCoordinates(self):
        """ Puts all of the weighted coordinates in a priority queue and selects the coordinate with the most weight.
        
        Return
        bestCoordinates - The highest weighted coordinates.
        """
        coordinatesQueue = []
        # It's highly likely that there are going to be a lot of coordinates with the same "most" weight.  Rather
        # than always choosing the leftmost coordinates, make a random choice by adding a random tie breaker to the 
        # priority.  
        randomTieBreaker = [i for i in range(self.boardDimensions ** 2 )]
        random.shuffle(randomTieBreaker)
        for i in range(self.boardDimensions):
            for j in range(self.boardDimensions):
                if self.enemyBoard[i][j] > BoardState.OPEN:
                    heapq.heappush(coordinatesQueue, (-self.enemyBoard[i][j], randomTieBreaker.pop(), Coordinates(i, j)))
        bestCoordinates = heapq.heappop(coordinatesQueue)[-1]
        self.enemyBoard[bestCoordinates.x][bestCoordinates.y] = BoardState.OPEN
        while len(coordinatesQueue) > 0:
            coordinates = heapq.heappop(coordinatesQueue)[-1]
            # Reset the weights on all coordinates under consideration so they'll be ready for another round of 
            # weighting.
            self.enemyBoard[coordinates.x][coordinates.y] = BoardState.OPEN
        return bestCoordinates
    
    def shotResult(self, shot, hit, sunk):
        """Attempts to sink as many sinking ships as possible given the shot result.
        
        Arguments
        shot - Shot of the form LetterNumber.
        hit - True, if the shot was a hit.
        sunk - Size of the sunk ship, if the shot sunk it.
        """
        ShotSelector.shotResult(self, shot, hit, sunk)
        coordinates = self.mapToCoordinates(shot)
        if sunk:
            self.shipsToSink.append(SinkingShip(coordinates, sunk))
            self.sinkShips()
        self.printShipsAfloat()
        self.printShipsToSink()
            
    def sinkShips(self):
        """Attempts to sink all sinking ships by positioning them in all possible positions .  
        If there's not enough information to sink them, the board remains as-is.  For every ship that's sunk
        marks all of its coordinates as SUNK to prevent them from being used in subsequent shot selections.
        """
        while True:
            stillSinkingShips = False
            for i in range(len(self.shipsToSink) - 1, -1, -1):
                sunkShip, shipCoordinates = self.positionAndSinkShip(self.shipsToSink[i])
                if sunkShip:
                    stillSinkingShips = True
                    for coordinates in shipCoordinates:
                        self.enemyBoard[coordinates.x][coordinates.y] = BoardState.SUNK
                    del(self.shipsToSink[i])
            if not stillSinkingShips:
                break
                
    def positionAndSinkShip(self, sinkingShip):
        """Positions a sinking ship in all possible positions and tries to sink it.  
        
        Arguments 
        sinkingShip The ship to position.
        
        Returns 
        sunkShip - True if the ship was sunk, False if not.
        shipCoorindates - Only valid if the ship was sunk, the coordinates of the sunk ship.
        """
        directions = [Direction.North, Direction.South, Direction.East, Direction.West]
        sunkShip = False
        shipCoordinates = None
        for direction in directions:
            tSunkShip, tShipCoordinates = self.sinkShip(sinkingShip.bullsEye, sinkingShip.size, direction)
            if tSunkShip:
                if sunkShip:
                    return False, None
                else:
                    sunkShip = tSunkShip
                    shipCoordinates = tShipCoordinates
        return sunkShip, shipCoordinates
            
    def sinkShip(self, bullsEye, size, direction):
        """Skips over the BULLSEYE before placing the sinking ship as the BULLSEYE will cause early search termination.
        
        Arguments
        bullsEye - The coordinates of the shot that caused the ship to start sinking.
        size - The size of the ship.
        direction - The direction to move as the ship is being placed.
    
        Returns
        sunkShip - True if the ship was sunk, False if not.
        shipCoorindates - Only valid if the ship was sunk, the coordinates of the sunk ship.
        """
        sunkShip, shipCoordinates = self.sinkShipSearch(Coordinates(bullsEye.x + direction.x, bullsEye.y + direction.y), size - 1, direction)
        if sunkShip:
            shipCoordinates.append(bullsEye)
        return sunkShip, shipCoordinates
    
    def sinkShipSearch(self, coordinates, size, direction):
        """ Recursive function that positions a sinking ship in a particular direction to see if can be sunk.

        Arguments
        bullsEye - The coordinates of the shot that caused the ship to start sinking.
        size - The size of the ship.
        direction - The direction to move as the ship is being placed.
        
        Returns
        sunkShip - True if the ship was sunk, False if not.
        shipCoorindates - Only valid if the ship was sunk, the coordinates of the sunk ship.
        """
        if size == 0:
            # Successfully searched the required size.
            return True, []
        if coordinates.x < 0 or coordinates.y < 0 or coordinates.x == self.boardDimensions or coordinates.y == self.boardDimensions:
            # Can't go off the board.
            return False, None
        if self.enemyBoard[coordinates.x][coordinates.y] != BoardState.HIT:
            # This search is all for naught since the ship can't possibly have sunk at this position.
            return False, None
        sunkShip, shipCoordinates = self.sinkShipSearch(Coordinates(coordinates.x + direction.x, coordinates.y + direction.y), size - 1, direction)
        if sunkShip:
            shipCoordinates.append(coordinates)
        return sunkShip, shipCoordinates

