import statsapi
import json

redsox_id = 111
next_game = statsapi.next_game(111)

game_info = statsapi.get('game', {'gamePk': next_game})

def process_section(homeaway, section):
    pids = game_info['liveData']['boxscore']['teams'][homeaway][section]
    if len(pids) == 0:
        return []
    players = statsapi.get(
        'people',
        {'personIds': ','.join(str(pid) for pid in pids)}
    )['people']
    positions = get_positions(homeaway, pids)
    return [
        (player['primaryNumber'], player['boxscoreName'], player['batSide']['code'], player['pitchHand']['code'], pos)
        for player, pos in zip(players, positions)
    ]

def get_positions(homeaway, playerids):
  teamplayers = game_info['liveData']['boxscore']['teams'][homeaway]['players']
  return [teamplayers[f'ID{pid}']['position']['code'] or None for pid in playerids]

def get_starter(homeaway):
  pitchers = game_info['liveData']['boxscore']['teams'][homeaway]['pitchers']
  if len(pitchers) == 0:
    return None
  pid = pitchers[0]

  starter = statsapi.get(
    'person',
    {'personId': pid}
  )['people'][0]
  starterinfo = (starter['primaryNumber'], starter['boxscoreName'], starter['pitchHand']['code'])

  return starterinfo
  

def process_team(homeaway: str):
  teamname = game_info['gameData']['teams'][homeaway]['name']
  print(f"{homeaway.upper()}: {teamname}")
  if len(lineup := process_section(homeaway, 'batters')) == 0:
    print("Lineup Not Posted. Bench will include all players")
  else:
    for player in lineup:
      print(f"{player[0]:2} {int(player[4]) % 10} {player[1]} ({player[2]})")
  print("-"*80)
  print("BENCH")
  bench = process_section(homeaway, 'bench')
  for player in bench:
    print(f"{player[0]:2} {player[1]} ({player[2]})")
  print("-"*80)

  starter = get_starter(homeaway)
  if starter:
    print(f"STARTER: {starter[0]:2} {starter[1]} ({starter[2]})")
  else:
    print("Starters not yet posted")
  print("-"*80)
  print("BULLPEN")
  pen = process_section(homeaway, 'bullpen')
  for player in pen:
    print(f"{player[0]:2} {player[1]} ({player[3]})")

if __name__ == "__main__":
  process_team("away")
  print("-"*80)
  print("-"*80)
    
  process_team("home")
