import sys
import argparse
import json
import logging
from collections import Counter
from command_driver import HttpCommandDriver
from shot_selector import RandomShotSelector
from shot_selector import MappingShotSelector
from player import Player

def setupLogging(logLevel):
        numericLevel = getattr(logging, logLevel.upper(), None)
        if not isinstance(numericLevel, int):
            raise ValueError("Invalid log level: %s" % logLevel)
        logging.basicConfig(level=numericLevel)
    
def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description = "plays a game of battleship")
    parser.add_argument("host", help = "host name of the gameplay server")
    parser.add_argument("port", type = int, help = "port to connect to the gameplay server")
    parser.add_argument("player", help = "name of the player playing the game")
    parser.add_argument("playerboard", help = "json file containing the player board")
    parser.add_argument("fleet", help = "json file containing the number and size of the initial fleet of ships")
    parser.add_argument("--pause", help = "number of seconds to pause between turns (0.5 is 1/2 second)",
                        type = float, default = 1)
    parser.add_argument("--strategy", choices = ["mapping", "random"], default = "random",
                        help = "shot selection strategy (default is random)")
    parser.add_argument("--logging", choices = ["debug", "info"], default = "info",
                        help = "logging level (default is info)")
    parser.add_argument("--join", type = int, help = "game id of game to join (default is to start new game)")
    parser.add_argument("--manualshot", action="store_true", help = "wait for player input to take a shot (default is not to)")
    try:
        args = parser.parse_args(argv)
        setupLogging(args.logging)
        playerBoard = json.load(open(args.playerboard))["board"]
        initialFleet = Counter(json.load(open(args.fleet))["fleet"])
        if args.strategy == "mapping":
            shotSelector = MappingShotSelector(len(playerBoard), initialFleet)
        else:
            shotSelector = RandomShotSelector(len(playerBoard), initialFleet)
        player = Player(playerBoard, HttpCommandDriver(args.host, args.port, args.player), shotSelector, args.pause, args.manualshot)
        if args.join is None:
            gameId = player.start()
            print("Starting new game, id: ", gameId)
        else:
            player.join(args.join)
        player.play()  
    except SystemExit:
        return 2

if __name__ == "__main__":
    sys.exit(main())