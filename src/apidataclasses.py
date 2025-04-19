from dataclasses import dataclass


@dataclass
class GameMetaData:
    wait: int
    timeStamp: str
    gameEvents: list
    logicalEvents: list


@dataclass
class GameDataGame:
    doubleHeader: str


@dataclass
class GameDataDatetime:
    dateTime: str
    originalDate: str
    officialDate: str
    dayNight: str
    time: str
    ampm: str


@dataclass
class GameDataTeamRecord:
    gamesPlayed: int
    wins: int
    losses: int


@dataclass
class GameDataTeam:
    id: int
    teamName: str
    franchiseName: str
    record: GameDataTeamRecord


@dataclass
class GameDataTeams:
    away: GameDataTeam
    home: GameDataTeam


@dataclass
class Handedness:
    code: str
    description: str


@dataclass
class GameDataPlayer:
    id: int
    primaryNumber: str
    fullName: str
    boxscoreName: str
    batSide: Handedness
    pitchHand: Handedness


@dataclass
class GameDataVenue:
    id: int
    name: str


@dataclass
class GameData:
    game: GameDataGame
    datetime: GameDataDatetime
    teams: GameDataTeams
    players: dict[str, GameDataPlayer]
    venue: GameDataVenue


@dataclass
class Position:
    code: str
    name: str
    abbreviation: str

@dataclass
class LiveDataPlayerPerson:
    id: int
    fullName: str


@dataclass
class LiveDataPlayer:
    person: LiveDataPlayerPerson
    jerseyNumber: str
    position: Position
    parentTeamId: int


@dataclass
class LiveDataTeam:
    battingOrder: list[int]
    bench: list[int]
    pitchers: list[int]
    bullpen: list[int]
    players: dict[str, LiveDataPlayer]


@dataclass
class LiveDataTeams:
    away: LiveDataTeam
    home: LiveDataTeam


@dataclass
class LiveDataBoxOfficialInfo:
    id: int
    fullName: str


@dataclass
class LiveDataBoxOfficial:
    official: LiveDataBoxOfficialInfo
    officialType: str

@dataclass
class LiveDataBoxscore:
    teams: LiveDataTeams
    officials: list[LiveDataBoxOfficial]


@dataclass
class LiveData:
    boxscore: LiveDataBoxscore


@dataclass
class GameInfo:
    gamePk: int
    metaData: GameMetaData
    gameData: GameData
    liveData: LiveData
