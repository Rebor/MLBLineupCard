from typing import List
from datetime import datetime
import statsapi
from dacite import from_dict
from apidataclasses import GameInfo, GameMetaData, GameData, LiveData, LiveDataPlayer

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
        # LiveData
        # if boxdata.parentTeamId == self.awayteam:
        # boxname = self.gameData.players[f"ID{boxdata.person.id}"].boxscoreName
        entry = f" {boxdata.jerseyNumber:2}"
        # entry += f" {boxdata.position.code}"
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

        # return self.center(entry, half=True)
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
        lineup = self.awaylineup if player.parentTeamId == self.awayteam else self.homelineup
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

    def make_bullpens(self):
        self.bullpens = [self.center("Bullpens"), SECTIONBREAK]
        awaypen = self.liveData.boxscore.teams.away.bullpen
        homepen = self.liveData.boxscore.teams.home.bullpen
        for away, home in zip(awaypen, homepen):
            self.bullpens.append(
                self.player_entry(
                    self.liveData.boxscore.teams.away.players[f"ID{away}"], starting=False
                ) +
                self.player_entry(
                    self.liveData.boxscore.teams.home.players[f"ID{home}"], starting=False
                )
            )


    def assemble_card(self):
        self.make_header()
        self.make_lineup()
        self.make_bench()
        self.make_starters()
        self.make_bullpens()
        # self.card[0:5] = self.header
        # self.card[5:5+len(self.lineups)] = self.lineups
        self.card = [
            *self.header,
            *self.lineups,
            SECTIONBREAK,
            *self.benches,
            SECTIONBREAK,
            *self.starters,
            SECTIONBREAK,
            *self.bullpens,
            SECTIONBREAK,
            BREAK
        ]

    def print_card(self):
        for line in self.card:
            if not line:
                break
            print(line + "\n", end='')

if __name__ == "__main__":
    gameinfo = statsapi.get('game', {'gamePk': 778470})
    gamecard = GameCard(gameinfo)
    # print(gamecard.gameData.venue.name)
    gamecard.assemble_card()
    gamecard.print_card()
    
