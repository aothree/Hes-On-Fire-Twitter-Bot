import tweepy
import pandas as pd
import numpy as np
import requests
import re
import config
import nba_api
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import playbyplayv2
from get_active_game_ids import get_active_ids
from get_streaks import get_streaks_from_game
from auth_to_twitter import authenticate_twitter
import boto3
import pickle
import urllib.request

headers = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://stats.nba.com/",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}
print("-----------were running--------------------------------")

game_ids = [
    "0012200068"
]  # hard coded now.  once there are active games, set game_ids equal to the get_active_ids() function.  will return a list of active game_ids

for game_id in game_ids:
    print(f"game id is {game_id}")
    game_df = playbyplayv2.PlayByPlayV2(game_id).get_data_frames()[0]
    # filter to only made and missed baskets
    fgs = game_df.loc[
        (game_df["EVENTMSGTYPE"] == 1) | (game_df["EVENTMSGTYPE"] == 2)
    ].copy()
    # grab just the play descriptions, and filter out blocks
    fgs = fgs[fgs["HOMEDESCRIPTION"].str.contains("BLK") == False]

    # get list of streaks
    streaks = get_streaks_from_game(fgs)

    for streak in streaks:
        # check s3 bucket to see if streak has already been tweeted about
        bucket = config.bucket
        key = config.key
        s3 = boto3.resource("s3")
        previous_content = pickle.loads(
            s3.Bucket(bucket).Object(key).get()["Body"].read()
        )
        try:
            tweets = previous_content.split(",")
            # print(f"tweets list is: {tweets}")
        except:
            tweets = []
            # print(f"tweets list is: {tweets}")

        # if name hasn't been tweeted about, proceed
        if streak not in tweets:

            player_name = streak[0]
            streak_length = streak[1]
            event_id = streak[2]
            event_desc = streak[3]

            # check for streaks over 4.
            if streak[1] > 4:
                url = "https://stats.nba.com/stats/videoeventsasset?GameEventID={}&GameID={}".format(
                    event_id, game_id
                )
                r = requests.get(url, headers=headers)
                json = r.json()
                video_urls = json["resultSets"]["Meta"]["videoUrls"]
                playlist = json["resultSets"]["playlist"]
                video_event = {
                    "video": video_urls[0]["lurl"],
                    "desc": playlist[0]["dsc"],
                }
                print(f"{player_name} has a streak of {streak_length}: {video_event}")

                # authenticate to twitter
                api = authenticate_twitter()
                print("authenticated to Twitter")

                # compile tweet
                emoji = "\U0001F525"
                text = f"{event_desc}\n\nThat's now {streak_length} made buckets in a row for {player_name}.  He's on fire!\n\n{streak_length * emoji}"
                file_name = f"{player_name}_{streak_length}_video.mp4"
                print("attempting urllib.request")
                urllib.request.urlretrieve(video_event["video"], file_name)
                print("attempting media upload with twitter api")
                upload_result = api.media_upload(file_name)

                # send tweet
                print(f"attempting to send Tweet for {player_name}")
                api.update_status(
                    status=text, media_ids=[upload_result.media_id_string]
                )

                # save info to s3 bucket to prevent duplicate tweet
                s3 = boto3.resource("s3")
                previous_content = pickle.loads(
                    s3.Bucket(bucket).Object(key).get()["Body"].read()
                )
                tweet_info_to_add = pickle.dumps(
                    f"[{previous_content}],[{player_name},{streak_length},{event_id}]"
                )
                s3.Object(bucket, key).put(Body=tweet_info_to_add)

print("done checking game ids")

