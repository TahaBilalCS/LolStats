from riotwatcher import RiotWatcher, ApiError
from playsound import playsound
import json, requests, pyautogui, time

# Prevents chat from interrupting if you hit the corner of screen with your mouse
pyautogui.FAILSAFE = False

# Takes a string parameter and outputs it in all chat
def allChat(str):
    pyautogui.press("enter")
    pyautogui.write("/all ")
    pyautogui.write(str, interval=0.01)
    pyautogui.press("enter")


# Warning user to not type in next few seconds while outputting data in /all chat
def displaying():
    pyautogui.press("enter")
    pyautogui.write("WARNING", interval=0.01)
    pyautogui.press("enter")
    time.sleep(3)


# The values below before the region table are for you to modify
# Max number of searches for each individual player (API request limit is 100 per 2 minutes)
maxSearch = 15

# Takes string parameter specifying ARAM, DRAFT, and any other gamemodes you would like the players to know
def greeting(str1):
    time.sleep(4)
    allChat("Hello")
    time.sleep(2)
    allChat(
        "I will be displaying the win/loss of the past "
        + str(maxSearch)
        + " "
        + str1
        + " games for each champion that everyone is currently playing"
    )
    time.sleep(1)
    allChat("Processing Time: ~3 minutes")


greeting("DRAFT")
gameType = 400  # 450 is Aram, 440 is Flex, 430 is Norms, 420 is Solo/Duo Ranked, 400 is Draft,  0 is Customs

username = "PUT YOUR USERNAME HERE"
apiKey = "PUT YOUR API KEY HERE"
my_region = "na1"


# Table of region id's for each region
# br1	br1.api.riotgames.com
# eun1	eun1.api.riotgames.com
# euw1	euw1.api.riotgames.com
# jp1	jp1.api.riotgames.com
# kr	kr.api.riotgames.com
# la1	la1.api.riotgames.com
# la2	la2.api.riotgames.com
# na1	na1.api.riotgames.com
# oc1	oc1.api.riotgames.com
# tr1	tr1.api.riotgames.com
# ru	ru.api.riotgames.com

# Current patch can be found here: https://ddragon.leagueoflegends.com/realms/na.json
response = json.loads(
    requests.get("https://ddragon.leagueoflegends.com/realms/na.json").text
)
patch = response["v"]


try:
    # Get summoner account information, you can uncomment the prints to view that information
    watcher = RiotWatcher(apiKey)
    myAccount = watcher.summoner.by_name(my_region, username)
    game = watcher.spectator.by_summoner(my_region, myAccount["id"])
    champion = {}
    statsList = []

    for player1 in game["participants"]:
        champions1 = watcher.data_dragon.champions(patch)
        champID1 = champions1["data"]
        for i, j in champID1.items():
            if int(player1["championId"]) == int(j["key"]):
                champion.update({player1["summonerName"]: j["id"]})

    # print("Summoner-v4        Row 8-2")
    for user, champ in champion.items():
        myAccount = watcher.summoner.by_name(my_region, user)
        # print(json.dumps(myAccount, indent=4, sort_keys=True))
        # print("\n")

        accountID = myAccount["accountId"]
        globalID = myAccount["puuid"]
        wins = 0
        losses = 0
        timeSpent = 0
        lastPatch = ""

        # Extract champion ID
        champions = watcher.data_dragon.champions(patch)
        champID = champions["data"][champ]["key"]

        # champID = None
        matches = None
        try:
            # Get matches for certain game type and champion
            # API only allows 100 matches at a time but my loop accounts for that
            matches = watcher.match.matchlist_by_account(
                my_region,
                accountID,
                gameType,
                begin_time=None,
                end_time=None,
                begin_index=None,
                end_index=None,
                season=None,
                champion=champID,
            )
        except ApiError as err:
            # playsound("error.mp3")
            print("Data not found")

        # Riot API acknowledged that total games field in their json is inaccurate but is a good estimate for smaller values
        if matches:
            supposedGames = matches["totalGames"]
            print("Supposed Total Games: ", supposedGames)

        matchCount = 0
        loopCount = 0  # Everytime loopCount increments, that means we viewed 100 matches and will now look for the next 100
        maxCount = maxSearch
        # If no matches were found for a champion on a user, then go to next index
        while (
            matches and matchCount < len(matches["matches"]) and matchCount < maxCount
        ):

            gameID = matches["matches"][matchCount]["gameId"]
            match = watcher.match.by_id(my_region, gameID)
            timeSpent += match["gameDuration"]

            # Find player in match, currentAccountId should track player even if they name changed or region transferred
            found = False
            for player in match["participantIdentities"]:
                if accountID in player["player"]["currentAccountId"]:
                    playerID = player["participantId"]
                    found = True

            if not found:
                print(
                    "Summoner wasn't found for match "
                    + str(matchCount)
                    + " with champ: "
                    + str(champ)
                    + "\nCould be an API issue or account problem"
                )
                break

            # print("Patch: " + match["gameVersion"])

            # Search if player won or not
            for participant in match["participants"]:
                if participant["participantId"] == playerID:
                    if participant["stats"]["win"]:
                        wins += 1
                    else:
                        losses += 1

            if matchCount == maxCount - 1:
                lastPatch = match["gameVersion"]
            timeSpent += match["gameDuration"]
            matchCount += 1

        # Make a sound for each time a player is read
        playsound("heep.mp3")

        # Storing printed values and other stats to dump all stats for each player and their champions at the end
        # This avoids losing stats with limited terminal history
        if wins + losses != 0:
            statsList.append(
                str(champ) + " Wins: " + str(wins) + " Losses: " + str(losses)
            )
        else:
            statsList.append(str(champ) + " First time on this account? ... NICE!")

    # Display warning before outputting statistics
    displaying()
    for stat in statsList:
        print(stat + "\n")
        allChat(stat)
    allChat("Individual requests accepted")
except ApiError as err:
    playsound("error.mp3")
    if err.response.status_code == 429:
        print(
            "We should retry in {} seconds.".format(err.response.headers["Retry-After"])
        )
        print("this retry-after is handled by default by the RiotWatcher library")
        print("future requests wait until the retry-after time passes")
    elif err.response.status_code == 404:
        print("Data not found at all")
    else:
        raise

