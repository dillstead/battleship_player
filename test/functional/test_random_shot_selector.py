import unittest
from shot_selector import RandomShotSelector
from shot_selector import BoardState
from collections import Counter

class RandomShotSelectorTestCase(unittest.TestCase):
    def test_shot_selection(self):
        fleet = Counter({ "2" : 1})
        rss = RandomShotSelector(3, fleet)
        # Select a shot, update the board with a result, and make sure the
        # board reflects the update.  Also, ensure ship removal is working.
        # HIT
        shot = rss.selectShot()
        rss.shotResult(shot, True, 0)
        coords = rss.mapToCoordinates(shot)
        assert(rss.enemyBoard[coords.x][coords.y] == BoardState.HIT)
        assert(len(rss.shipsAfloat) == 1)
        # MISS
        shot = rss.selectShot()
        rss.shotResult(shot, False, 0)
        coords = rss.mapToCoordinates(shot)
        assert(rss.enemyBoard[coords.x][coords.y] == BoardState.MISS)
        assert(len(rss.shipsAfloat) == 1)
        # Clear out the remaining board.
        for i in range(7):
            shot = rss.selectShot()
            rss.shotResult(shot, False, 0)
        for i in range(3):
            for j in range(3):
                assert(rss.enemyBoard[coords.x][coords.y] != BoardState.OPEN)
                
    
        
        


        

