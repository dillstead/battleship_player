import json
import logging
from http.client import HTTPConnection

"""Sends HTTP commands to the gameplay server and returns the results.  Commands
are encoded to JSON format before sending to the server and results are decoded from JSON
format before returning.   

Public interface
join(playerBoard)
status(gameId)
fire(gameId, shot):
"""
class HttpCommandDriver:
    def __init__(self, host, port, user):
        """Constructor.

        Arguments
        host - Gameplay server host name.
        port - Gameplay server port.
        user - Username of the person playing the game.
        """
        self.host = host;
        self.port = port;
        self.user = user;
        
    def getResponse(self, connection):
        """Logs and returns the response body."""
        response = connection.getresponse()
        body = response.read() 
        logging.debug("HTTP response status: %d, body: %s" % (response.status, body))
        return body
        
    def join(self, playerBoard):
        """Joins the game.

        Arguments
        playerBoard - Player board with ship placements.
        
        Returns 
        gameId - The id of the game that was just joined.
        """
        logging.debug("cmd: join")
        connection = HTTPConnection(self.host, self.port)
        body = json.dumps({"user:" : self.user, "board" : playerBoard})
        connection.request("POST", "/games/join", body)
        response = json.loads(self.getReponse(connection))
        connection.close()
        return response["game_id"] 
    
    def status(self, gameId):
        """Returns the status of the game.

        Arguments
        gameId - The id of the current game.
        
        Returns 
        gameStatus - "playing", "won" or "lost".
        myTurn - True if it's my turn, False if it's the enemy's turn.
        """
        logging.debug("cmd: status, game id: %d" % gameId)
        connection = HTTPConnection(self.host, self.port)
        body = json.dumps({"user:" : self.user, "game_id" : gameId})
        connection.request("GET", "/games/status", body)
        response = json.loads(self.getReponse(connection))
        connection.close()
        return response["game_status"], response["my_turn"] 
            
    def fire(self, gameId, shot):
        """Fires a shot at the enemy.

        Arguments
        gameId - The id of the current game.
        shot - Shot to fire of the form LetterNumber.
        
        Returns 
        hit - True if an enemy's ship was hit.
        sunk - Size of the sunk ship, if the shot sunk it.
        """
        logging.debug("cmd: fire, game id: %d, shot: %s" % (gameId, shot))
        connection = HTTPConnection(self.host, self.port)
        body = json.dumps({"user:" : self.user, "game_id" : gameId, "shot" : shot})
        connection.request("POST", "/games/fire", body)
        response = json.loads(self.getReponse(connection))
        connection.close()
        return response["hit"], response["sunk"]
