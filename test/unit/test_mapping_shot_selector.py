import unittest
from shot_selector import MappingShotSelector
from shot_selector import Coordinates
from shot_selector import SinkingShip
from shot_selector import BoardState
from collections import Counter
from collections import namedtuple
from priority_queue import PriorityQueue

class MappingTestCase(unittest.TestCase):
    def obstacles(self, state):
        fleet = Counter({"2" : 1})
        mss = MappingShotSelector(3, fleet)
        mss.enemyBoard[1][1] = state 
        mss.weightBoard()
        assert(mss.enemyBoard[0][0] == 2)
        assert(mss.enemyBoard[0][1] == 2)
        assert(mss.enemyBoard[0][2] == 2)
        assert(mss.enemyBoard[1][0] == 2)
        assert(mss.enemyBoard[1][2] == 2)
        assert(mss.enemyBoard[2][0] == 2)
        assert(mss.enemyBoard[2][1] == 2)
        assert(mss.enemyBoard[2][2] == 2)
        
    def test_weightBoard(self):
        fleet = Counter({"2" : 1})
        # No obstacles.
        mss = MappingShotSelector(3, fleet)
        mss.weightBoard()
        assert(mss.enemyBoard[0][0] == 2)
        assert(mss.enemyBoard[0][1] == 3)
        assert(mss.enemyBoard[0][2] == 2)
        assert(mss.enemyBoard[1][0] == 3)
        assert(mss.enemyBoard[1][1] == 4)
        assert(mss.enemyBoard[1][2] == 3)
        assert(mss.enemyBoard[2][0] == 2)
        assert(mss.enemyBoard[2][1] == 3)
        assert(mss.enemyBoard[2][2] == 2)
        # Obstacles.
        self.obstacles(BoardState.BULLSEYE)
        self.obstacles(BoardState.MISS)
        self.obstacles(BoardState.SUNK)
        # Add a hit and make sure that affects the weighting.
        mss = MappingShotSelector(3, fleet)
        mss.enemyBoard[1][1] = BoardState.HIT
        mss.weightBoard()
        assert(mss.enemyBoard[0][0] == 2)
        assert(mss.enemyBoard[0][1] == 13)
        assert(mss.enemyBoard[0][2] == 2)
        assert(mss.enemyBoard[1][0] == 13)
        assert(mss.enemyBoard[1][1] == BoardState.HIT)
        assert(mss.enemyBoard[1][2] == 13)
        assert(mss.enemyBoard[2][0] == 2)
        assert(mss.enemyBoard[2][1] == 13)
        assert(mss.enemyBoard[2][2] == 2)
        
    def test_selectBestCoordinates(self):
        fleet = Counter({"2" : 1})
        # No obstacles.
        mss = MappingShotSelector(3, fleet)
        mss.weightBoard()
        coordinates = mss.selectBestCoordinates()
        assert(coordinates.x == 1 and coordinates.y == 1)
        assert(mss.enemyBoard[0][0] == BoardState.OPEN)
        assert(mss.enemyBoard[0][1] == BoardState.OPEN)
        assert(mss.enemyBoard[0][2] == BoardState.OPEN)
        assert(mss.enemyBoard[1][0] == BoardState.OPEN)
        assert(mss.enemyBoard[1][1] == BoardState.OPEN)
        assert(mss.enemyBoard[1][2] == BoardState.OPEN)
        assert(mss.enemyBoard[2][0] == BoardState.OPEN)
        assert(mss.enemyBoard[2][1] == BoardState.OPEN)
        assert(mss.enemyBoard[2][2] == BoardState.OPEN)
        # Add a hit and make sure that affects coordinate being selected.
        mss = MappingShotSelector(3, fleet)
        mss.enemyBoard[1][1] = BoardState.HIT
        mss.weightBoard()
        coordinates = mss.selectBestCoordinates()
        assert((coordinates.x == 0 and coordinates.y == 1) or (coordinates.x == 1 and coordinates.y == 0) or (coordinates.x == 1 and coordinates.y == 2) or (coordinates.x == 2 and coordinates.y == 1))
        assert(mss.enemyBoard[0][0] == BoardState.OPEN)
        assert(mss.enemyBoard[0][1] == BoardState.OPEN)
        assert(mss.enemyBoard[0][2] == BoardState.OPEN)
        assert(mss.enemyBoard[1][0] == BoardState.OPEN)
        assert(mss.enemyBoard[1][1] == BoardState.HIT)
        assert(mss.enemyBoard[1][2] == BoardState.OPEN)
        assert(mss.enemyBoard[2][0] == BoardState.OPEN)
        assert(mss.enemyBoard[2][1] == BoardState.OPEN)
        assert(mss.enemyBoard[2][2] == BoardState.OPEN)
        
    def testPositionAndSinkShip(self):
        fleet = Counter({"2" : 1})
        # Only one way to sink.
        mss = MappingShotSelector(3, fleet)
        mss.enemyBoard[0][0] = BoardState.BULLSEYE
        mss.enemyBoard[0][1] = BoardState.HIT
        sunkShip, shipsCoordinates = mss.positionAndSinkShip(SinkingShip(Coordinates(0, 0), 2))
        assert(sunkShip)
        for shipCoordinates in shipsCoordinates:
            assert((shipCoordinates.x == 0 and shipCoordinates.x == 0) or (shipCoordinates.x == 0 and shipCoordinates.y == 1))
        assert(mss.enemyBoard[0][0] == BoardState.BULLSEYE)
        assert(mss.enemyBoard[0][1] == BoardState.HIT)
        # Add a second way to sink, shouldn't be able to sink it.
        mss.enemyBoard[1][0] = BoardState.HIT
        sunkShip, shipsCoordinates = mss.positionAndSinkShip(SinkingShip(Coordinates(0, 0), 2))
        assert(not sunkShip)
        # Add an extra coordinate, but still a way to sink a ship of size 3.
        fleet = Counter({"3" : 1})
        mss = MappingShotSelector(3, fleet)
        mss.enemyBoard[0][0] = BoardState.BULLSEYE
        mss.enemyBoard[0][1] = BoardState.HIT
        mss.enemyBoard[0][2] = BoardState.HIT
        mss.enemyBoard[1][0] = BoardState.HIT
        sunkShip, shipsCoordinates = mss.positionAndSinkShip(SinkingShip(Coordinates(0, 0), 3))
        assert(sunkShip)

    def testSinkShips(self):
        fleet = Counter({"2" : 1, "3" : 1})
        mss = MappingShotSelector(3, fleet)
        mss.shipsToSink.append(SinkingShip(Coordinates(0, 0), 3))
        mss.shipsToSink.append(SinkingShip(Coordinates(2, 1), 2))
        # Add two ships that can't be sunk yet.
        mss.enemyBoard[0][0] = BoardState.BULLSEYE
        mss.enemyBoard[0][1] = BoardState.HIT
        mss.enemyBoard[0][2] = BoardState.HIT
        mss.enemyBoard[1][0] = BoardState.HIT
        mss.enemyBoard[2][0] = BoardState.HIT
        mss.enemyBoard[2][1] = BoardState.BULLSEYE
        mss.enemyBoard[2][2] = BoardState.HIT
        mss.sinkShips()
        assert(mss.enemyBoard[0][0] == BoardState.BULLSEYE)
        assert(mss.enemyBoard[0][1] == BoardState.HIT)
        assert(mss.enemyBoard[0][2] == BoardState.HIT)
        assert(mss.enemyBoard[1][0] == BoardState.HIT)
        assert(mss.enemyBoard[2][0] == BoardState.HIT)
        assert(mss.enemyBoard[2][1] == BoardState.BULLSEYE)
        assert(mss.enemyBoard[2][2] == BoardState.HIT)
        # Add another ship that will cause all three ships to be sunk. 
        mss.shipsToSink.append(SinkingShip(Coordinates(0, 2), 2))
        mss.enemyBoard[0][2] = BoardState.BULLSEYE
        mss.sinkShips()
        assert(mss.enemyBoard[0][0] == BoardState.SUNK)
        assert(mss.enemyBoard[0][1] == BoardState.SUNK)
        assert(mss.enemyBoard[0][2] == BoardState.SUNK)
        assert(mss.enemyBoard[1][0] == BoardState.SUNK)
        assert(mss.enemyBoard[2][0] == BoardState.SUNK)
        assert(mss.enemyBoard[2][1] == BoardState.SUNK)
        assert(mss.enemyBoard[2][2] == BoardState.SUNK)
        assert(len(mss.shipsToSink) == 0)     
        