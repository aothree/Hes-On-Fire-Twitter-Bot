# take playbyplay data and check for streaks


def get_streaks_from_game(df):
    import pandas as pd

    player_shots = {}

    plays = pd.merge(
        left=df[["HOMEDESCRIPTION", "EVENTNUM"]],
        right=df[["VISITORDESCRIPTION", "EVENTNUM"]],
        on="EVENTNUM",
    )
    plays.fillna("", inplace=True)
    plays["both_descriptions"] = plays["HOMEDESCRIPTION"] + plays["VISITORDESCRIPTION"]
    plays = plays[["EVENTNUM", "both_descriptions"]]
    # filter out blocks
    plays = plays[plays["both_descriptions"].str.contains("BLK") == False]
    plays.reset_index(inplace=True)

    for idx, play in enumerate(plays["both_descriptions"]):
        if play.split()[0] == "MISS":
            name = play.split()[1]
            outcome = "miss"
            if name in player_shots:
                player_shots[name].append([outcome])
            else:
                player_shots[name] = [[outcome]]
        else:
            name = play.split()[0]
            event_num = plays["EVENTNUM"][idx]
            outcome = ["made", event_num, play]
            if name in player_shots:
                player_shots[name].append([outcome])
            else:
                player_shots[name] = [[outcome]]

    # once dicitonary of shot outcomes is populated, create a list of streaks

    streaks = []
    for player in player_shots:

        streak = 0
        shots = player_shots[player]
        for i in range(len(shots)):
            if shots[i][0][0] == "made":
                streak += 1
                event_num = shots[i][0][1]
                event_description = shots[i][0][2]
                player_streak = [player, streak, event_num, event_description]
                
                if player_streak not in streaks:
                    streaks.append(player_streak)
            else:  # it was a miss, streak goes back to 0
                streak = 0
    return streaks

