from typing import List
from itertools import zip_longest
from datetime import datetime, timedelta
import statsapi
from dacite import from_dict
from apidataclasses import (
    GameInfo,
    GameMetaData,
    GameData,
    LiveData,
    LiveDataPlayer,
    ScheduleDate,
    Schedule
)

BREAK = "#"*80
SECTIONBREAK = "#" + "-"*38 + "##" + "-"*38 + "#"


class GameCard:
    def __init__(self, gameinfo: dict):
        self.gameinfo: GameInfo = from_dict(GameInfo, gameinfo)
        self.gamePk: int = self.gameinfo.gamePk
        self.metaData: GameMetaData = self.gameinfo.metaData
        self.gameData: GameData = self.gameinfo.gameData
        self.liveData: LiveData = self.gameinfo.liveData

        self.awayteam = self.gameData.teams.away
        self.hometeam = self.gameData.teams.home

        self.cardwidth = 80

        self.card: List[str] = [""]*100

    def center(self, text: str, half: bool = False):
        width = (self.cardwidth // 2) if half else self.cardwidth
        nspace = width - 2 - len(text)
        leftspace = " " * (nspace // 2)
        rightspace = " " * (nspace // 2 + nspace % 2)
        return f"#{leftspace}{text}{rightspace}#"

    def make_header(self):
        self.header: List[str] = [""] * 7
        awayteam = (
            f"{self.gameData.teams.away.franchiseName} "
            f"{self.gameData.teams.away.teamName}"
        )
        hometeam = (
            f"{self.gameData.teams.home.franchiseName} "
            f"{self.gameData.teams.home.teamName}"
        )
        matchup: str = f"{awayteam} @ {hometeam}"

        dt = datetime.fromisoformat(self.gameData.datetime.officialDate)
        datetimestr = (
            f"{dt.strftime('%a %b %d, %Y')} "
            f"{self.gameData.datetime.time} "
            f"{self.gameData.datetime.ampm} "
        )
        self.header[0] = BREAK
        self.header[1] = self.center(matchup)
        self.header[2] = self.center(datetimestr)
        self.header[3] = self.center(self.gameData.venue.name)
        self.header[4] = BREAK
        self.header[5] = self.center("Away", half=True) + self.center("Home", half=True)
        self.header[6] = SECTIONBREAK

    def player_entry(self, boxdata: LiveDataPlayer, starting = True):
        if boxdata:
            entry = f" {boxdata.jerseyNumber:2}"
            entry += f" {self.gameData.players[f'ID{boxdata.person.id}'].boxscoreName}"
            if str(boxdata.position.code) == '1':
                side = self.gameData.players[f'ID{boxdata.person.id}'].pitchHand.code
            else:
                side = self.gameData.players[f'ID{boxdata.person.id}'].batSide.code

                entry += f" ({side})"

            entry += ' ' * ((self.cardwidth // 2) - 8 - len(entry))

            if starting:
                pos = int(boxdata.position.code) % 10
                entry += (f"| {pos} | ")
            else:
                entry += ' '*6
        else:
            entry = ' '*((self.cardwidth // 2) - 2)

        return "#" + entry + "#"

    def make_lineup(self):
        self.awaylineup = self.liveData.boxscore.teams.away.battingOrder
        self.homelineup = self.liveData.boxscore.teams.home.battingOrder

        self.lineups = [self.center("Lineup"), SECTIONBREAK]
        for away, home in zip(self.awaylineup, self.homelineup):
            self.lineups.append(
                self.player_entry(self.liveData.boxscore.teams.away.players[f"ID{away}"])
                + self.player_entry(self.liveData.boxscore.teams.home.players[f"ID{home}"])
            )

    def is_bench(self, player: LiveDataPlayer):
        lineup = self.awaylineup if player.parentTeamId == self.awayteam.id else self.homelineup
        return (player.person.id not in lineup) and (int(player.position.code) != 1)

    def make_bench(self):
        awaybench = [
            player
            for player in self.liveData.boxscore.teams.away.players.values()
            if self.is_bench(player)
        ]
        homebench = [
            player
            for player in self.liveData.boxscore.teams.home.players.values()
            if self.is_bench(player)
        ]

        self.benches = [self.center("Bench"), SECTIONBREAK]
        for away, home in zip(awaybench, homebench):
            self.benches.append(
                self.player_entry(away, starting=False)
                + self.player_entry(home, starting=False)
            )

    def make_starters(self):
        self.starters = [self.center("Starters"), SECTIONBREAK]
        awaystarter = self.liveData.boxscore.teams.away.pitchers[0]
        homestarter = self.liveData.boxscore.teams.home.pitchers[0]
        self.starters.append(
            self.player_entry(
                self.liveData.boxscore.teams.away.players[f'ID{awaystarter}'], starting=False
            ) +
            self.player_entry(
                self.liveData.boxscore.teams.home.players[f'ID{homestarter}'], starting=False
            )
        )

    def get_prob_pitchers(self, scheduledate: ScheduleDate, team_id: int):
        pitchers = []
        for game in scheduledate.games:
            if game.teams.away.team.id == team_id:
                if pitcher := game.teams.away.probablePitcher:
                    pitchers.append(pitcher.id)
            else:
                if pitcher := game.teams.home.probablePitcher:
                    pitchers.append(pitcher.id)
        return pitchers

    def make_bullpens(self):
        self.bullpens = [self.center("Bullpens"), SECTIONBREAK]
        self.awaypen = self.liveData.boxscore.teams.away.bullpen
        self.homepen = self.liveData.boxscore.teams.home.bullpen

        today = datetime.now()
        awayten = from_dict(
            Schedule,
            statsapi.get(
                'schedule',
                params={
                    'sportId':1,
                    'teamId': self.awayteam.id,
                    'startDate': (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    'endDate': (today + timedelta(days=10)).strftime("%Y-%m-%d"),
                    'hydrate': 'probablePitcher'
                }
            )
        )
        hometen = from_dict(
            Schedule,
            statsapi.get(
                'schedule',
                params={
                    'sportId': 1,
                    'teamId': self.hometeam.id,
                    'startDate': (today - timedelta(days=10)).strftime("%Y-%m-%d"),
                    'endDate': (today + timedelta(days=10)).strftime("%Y-%m-%d"),
                    'hydrate': 'probablePitcher'
                }
            )
        )
        awaystarters = set(
            [
                p
                for date in awayten.dates
                for p in self.get_prob_pitchers(date, self.awayteam.id)
            ]
        )
        homestarters = set(
            [
                p
                for date in hometen.dates
                for p in self.get_prob_pitchers(date, self.hometeam.id)
            ]
        )

        awaynonstarters = set(self.awaypen) - awaystarters
        homenonstarters = set(self.homepen) - homestarters

        for away, home in zip_longest(awaynonstarters, homenonstarters):
            self.bullpens.append(
                self.player_entry(
                    self.liveData.boxscore.teams.away.players.get(f"ID{away}", None), starting=False
                ) +
                self.player_entry(
                    self.liveData.boxscore.teams.home.players.get(f"ID{home}", None), starting=False
                )
            )

        # print(awaystarters)
        # print(homestarters)
        activeawaystarters = set(self.awaypen).intersection(awaystarters)
        activehomestarters = set(self.homepen).intersection(homestarters)
        self.bullpens.extend([SECTIONBREAK, self.center("Other Pitchers"), SECTIONBREAK])
        for away, home in zip_longest(activeawaystarters, activehomestarters):
            print(away, home)
            self.bullpens.append(
                self.player_entry(
                    self.liveData.boxscore.teams.away.players.get(f"ID{away}", None), starting=False
                ) +
                self.player_entry(
                    self.liveData.boxscore.teams.home.players.get(f"ID{home}", None), starting=False
                )
            )


    def assemble_card(self):
        self.make_header()
        self.make_lineup()
        self.make_bench()
        self.make_starters()
        self.make_bullpens()

        self.card = [
            *self.header,
            *self.lineups,
            SECTIONBREAK,
            *self.benches,
            SECTIONBREAK,
            *self.starters,
            SECTIONBREAK,
            *self.bullpens,
            # SECTIONBREAK,
            BREAK
        ]

    def print_card(self):
        for line in self.card:
            if not line:
                break
            print(line + "\n", end='')

if __name__ == "__main__":
    # next_game = statsapi.next_game(111)
    todays_game = statsapi.schedule(team=111)[0]['game_id']
    #778470
    print(todays_game)
    gameinfo = statsapi.get('game', {'gamePk': todays_game})
    gamecard = GameCard(gameinfo)
    # print(gamecard.gameData.venue.name)
    gamecard.assemble_card()
    gamecard.print_card()
