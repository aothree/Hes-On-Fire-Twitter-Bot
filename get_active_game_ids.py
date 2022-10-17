# get list of today's game ids


def get_active_ids():
    from nba_api.live.nba.endpoints import scoreboard

    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()
    active_game_ids = []
    for game in games:
        active_game_ids.append(game["gameId"])
    return active_game_ids
