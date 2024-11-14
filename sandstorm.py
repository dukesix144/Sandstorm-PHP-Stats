import re
import json
import ftplib
from datetime import datetime
import mysql.connector

# MySQL database configuration
db_config = {
    'user': '',
    'password': '',
    'host': '',
    'database': ''
}

# FTP configuration
ftp_host = ''
ftp_user = ''
ftp_pass = ''
remote_file = '/sand83/Insurgency/Saved/Logs/Insurgency.log'
local_file = '/home/rrgaming/public_html/python/Insurgency83.log'
remote_file2 = '/sand84/Insurgency/Saved/Logs/Insurgency.log'
local_file2 = '/home/rrgaming/public_html/python/Insurgency84.log'

# Define regex patterns for login, logout, kill, assist, team join, round result, destroyed, and capture events
login_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogNet: Login request: \?Name=(?P<player_name>\w+)?\suserId:\sSteamNWI:(?P<steam_id>\d+)\splatform:\sSteamNWI'
logout_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogOnlineSession: Warning: STEAM \(NWI\): Player\s(?P<steam_id>\d+)\sis\snot\spart\sof\ssession\s\(GameSession\)'
kill_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogGameplayEvents: Display:\s(?P<killer_name>\w+)\[(?P<killer_steam_id>[\w]+),.*?\]\skilled\s(?P<victim_name>\w+)\[(?P<victim_steam_id>\w+),.*?\]'
assist_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogGameplayEvents: Display:\s(?P<first_assistor_name>\w+)\[(?P<first_assistor_steam_id>[\w]+),.*?\]\s\+\s(?P<second_assistor_name>\w+)\[(?P<second_assistor_steam_id>\d+),.*?\]\skilled\s(?P<victim_name>\w+)\[(?P<victim_steam_id>\w+),.*?\]'
team_join_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogGameMode: Display: Player \d+ \'(?P<player_name>\w+)\' joined team (?P<team>\d+)'
round_result_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogGameMode: Display: Recorded match results for new round: Winner:(?P<winner_team>\d+)'
destroyed_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogGameplayEvents: Display: Objective \d+ owned by team \d+ was destroyed for team (?P<destroyed_team>\d+) by (?P<player_name>\w+)\[(?P<steam_id>\d+)\]'
capture_pattern = r'\[(?P<timestamp>[\d\.\-\:]+)\]\[\d+\]LogGameplayEvents: Display: Objective \d+ was captured for team (?P<captured_team>\d+) from team (?P<previous_team>\d+) by (?P<player_name>\w+)\[(?P<steam_id>\d+)\]'

# Function to calculate ELO rating (allow ELO to go below 1000 but not negative)
def calculate_elo(player):
    elo = player['elo']  # Start with the player's current ELO

    # Calculate the ELO rating based on performance metrics
    elo += player['kills'] * 1  # +1 for kills since players are against bots
    elo += player['assists'] * 5
    elo += player['round_winner'] * 15
    elo += player['destroyed'] * 10
    elo += player['captures'] * 10
    elo -= player['deaths'] * 10
    elo -= player['round_loser'] * 15
    elo -= player['lost_capture'] * 10
    elo -= player['lost_destroyed'] * 10

    # Ensure ELO doesn't go negative
    return max(elo, 0)

# Function to update the player's ELO in the MySQL database
def update_player_elo(cursor, steam_id, elo):
    sql = "UPDATE players SET elo = %s WHERE steam_id = %s"
    cursor.execute(sql, (elo, steam_id))

# Function to download log files via FTP
def download_logs():
    with ftplib.FTP(ftp_host) as ftp:
        ftp.login(ftp_user, ftp_pass)
        
        # Download the first remote log file
        with open(local_file, 'wb') as local_file_obj:
            ftp.retrbinary(f"RETR {remote_file}", local_file_obj.write)

        # Download the second remote log file
        with open(local_file2, 'wb') as local_file_obj2:
            ftp.retrbinary(f"RETR {remote_file2}", local_file_obj2.write)

# Function to insert events into MySQL database
def insert_event_to_db(cursor, table, steam_id, timestamp, event_data):
    if event_data:
        placeholders = ', '.join(['%s'] * len(event_data))
        columns = ', '.join(event_data.keys())
        sql = f"INSERT INTO {table} (steam_id, timestamp, {columns}) VALUES (%s, %s, {placeholders}) ON DUPLICATE KEY UPDATE timestamp = timestamp"
        cursor.execute(sql, (steam_id, timestamp, *event_data.values()))
    else:
        sql = f"INSERT INTO {table} (steam_id, timestamp) VALUES (%s, %s) ON DUPLICATE KEY UPDATE timestamp = timestamp"
        cursor.execute(sql, (steam_id, timestamp))

# Function to insert players into the players table
def insert_player(cursor, steam_id, player_name):
    sql = f"INSERT INTO players (steam_id, player_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE player_name = VALUES(player_name)"
    cursor.execute(sql, (steam_id, player_name))

# Function to establish database connection
def connect_to_db():
    return mysql.connector.connect(**db_config)

# Helper function to avoid duplicate events
def event_exists(cursor, table, steam_id, timestamp):
    sql = f"SELECT COUNT(*) FROM {table} WHERE steam_id = %s AND timestamp = %s"
    cursor.execute(sql, (steam_id, timestamp))
    return cursor.fetchone()[0] > 0

# Helper function to calculate time played
def calculate_time_played(login_timestamp, logout_timestamp):
    if login_timestamp and logout_timestamp:
        login_time = datetime.strptime(login_timestamp, '%Y.%m.%d-%H.%M.%S:%f')
        logout_time = datetime.strptime(logout_timestamp, '%Y.%m.%d-%H.%M.%S:%f')
        time_diff = logout_time - login_time
        total_seconds = int(time_diff.total_seconds())  # Round to whole seconds
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"  # Format as HH:MM:SS
    return "00:00:00"  # Default if either timestamp is missing

# Helper function to add a player if they don't exist in the dictionary
def ensure_player_exists(players, steam_id, player_name=None, login_timestamp=None):
    if steam_id not in players:
        players[steam_id] = {
            'steam_id': steam_id,
            'login_timestamp': login_timestamp,
            'player_name': player_name or f"Unknown({steam_id})",
            'logout_timestamp': None,
            'time_played': None,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'team': '0',  # Default to team 0
            'round_winner': 0,
            'round_loser': 0,
            'destroyed': 0,
            'captures': 0,
            'lost_capture': 0,
            'lost_destroyed': 0,
            'elo': 1000
        }

# Helper function to check if the player was active during the round
def was_player_active(player, round_timestamp):
    login_time = player.get('login_timestamp')
    logout_time = player.get('logout_timestamp')

    if login_time:
        login_time = datetime.strptime(login_time, '%Y.%m.%d-%H.%M.%S:%f')
        round_time = datetime.strptime(round_timestamp, '%Y.%m.%d-%H.%M.%S:%f')

        if logout_time:
            logout_time = datetime.strptime(logout_time, '%Y.%m.%d-%H.%M.%S:%f')
            return login_time <= round_time <= logout_time
        else:
            # If logout_time is None, assume the player is still active
            return login_time <= round_time
    return False

def parse_log(file_path):
    players = {}

    # Connect to the MySQL database
    conn = connect_to_db()
    cursor = conn.cursor()

    with open(file_path, 'r') as log_file:
        for line in log_file:
            # Check for login events
            login_match = re.search(login_pattern, line)
            if login_match:
                login_timestamp = login_match.group('timestamp')
                player_name = login_match.group('player_name')
                steam_id = login_match.group('steam_id')
                
                # Ensure player is added to the players dictionary
                ensure_player_exists(players, steam_id, player_name, login_timestamp)

                # Insert the player into the players table
                insert_player(cursor, steam_id, player_name)

                # Insert into the database
                if not event_exists(cursor, 'login_log', steam_id, login_timestamp):
                    insert_event_to_db(cursor, 'login_log', steam_id, login_timestamp, {
                        'player_name': player_name
                    })
            
            # Check for logout events
            logout_match = re.search(logout_pattern, line)
            if logout_match:
                logout_timestamp = logout_match.group('timestamp')
                steam_id = logout_match.group('steam_id')

                # Ensure player exists before setting the logout timestamp
                ensure_player_exists(players, steam_id)
                players[steam_id]['logout_timestamp'] = logout_timestamp

                # Insert into the database
                if not event_exists(cursor, 'logout_log', steam_id, logout_timestamp):
                    insert_event_to_db(cursor, 'logout_log', steam_id, logout_timestamp, {})

            # Check for kill events
            kill_match = re.search(kill_pattern, line)
            if kill_match:
                kill_timestamp = kill_match.group('timestamp')
                killer_name = kill_match.group('killer_name')
                killer_steam_id = kill_match.group('killer_steam_id')
                victim_name = kill_match.group('victim_name')
                victim_steam_id = kill_match.group('victim_steam_id')

                # Ensure both killer and victim exist in the players dictionary
                ensure_player_exists(players, killer_steam_id, killer_name)
                ensure_player_exists(players, victim_steam_id, victim_name)

                # Insert the killer and victim into the players table
                insert_player(cursor, killer_steam_id, killer_name)
                insert_player(cursor, victim_steam_id, victim_name)

                # Add kill and death
                players[killer_steam_id]['kills'] += 1
                players[victim_steam_id]['deaths'] += 1

                # Insert into the database
                if not event_exists(cursor, 'kill_log', killer_steam_id, kill_timestamp):
                    insert_event_to_db(cursor, 'kill_log', killer_steam_id, kill_timestamp, {
                        'victim_steam_id': victim_steam_id,
                        'victim_name': victim_name
                    })

            # Check for assist events
            assist_match = re.search(assist_pattern, line)
            if assist_match:
                assist_timestamp = assist_match.group('timestamp')
                first_assistor_name = assist_match.group('first_assistor_name')
                first_assistor_steam_id = assist_match.group('first_assistor_steam_id')
                second_assistor_name = assist_match.group('second_assistor_name')
                second_assistor_steam_id = assist_match.group('second_assistor_steam_id')
                victim_name = assist_match.group('victim_name')
                victim_steam_id = assist_match.group('victim_steam_id')

                # Ensure all players exist in the players dictionary
                ensure_player_exists(players, first_assistor_steam_id, first_assistor_name)
                ensure_player_exists(players, second_assistor_steam_id, second_assistor_name)
                ensure_player_exists(players, victim_steam_id, victim_name)

                # Insert the assistors and victim into the players table
                insert_player(cursor, first_assistor_steam_id, first_assistor_name)
                insert_player(cursor, second_assistor_steam_id, second_assistor_name)
                insert_player(cursor, victim_steam_id, victim_name)

                # Add assists and death
                players[first_assistor_steam_id]['assists'] += 1
                players[second_assistor_steam_id]['assists'] += 1
                players[victim_steam_id]['deaths'] += 1

                # Insert into the database
                if not event_exists(cursor, 'assist_log', first_assistor_steam_id, assist_timestamp):
                    insert_event_to_db(cursor, 'assist_log', first_assistor_steam_id, assist_timestamp, {
                        'second_assistor_steam_id': second_assistor_steam_id,
                        'victim_steam_id': victim_steam_id,
                        'victim_name': victim_name
                    })

            # Check for team join events
            team_join_match = re.search(team_join_pattern, line)
            if team_join_match:
                join_timestamp = team_join_match.group('timestamp')
                player_name = team_join_match.group('player_name')
                team = team_join_match.group('team')

                # Ensure team variable exists
                if team:
                    # Check if a player with this name exists in the dictionary
                    player_found = None
                    for player in players.values():
                        if player['player_name'] == player_name:
                            player_found = player
                            player['team'] = team

                    # Proceed only if the player was found
                    if player_found:
                        if not event_exists(cursor, 'team_join_log', player_found['steam_id'], join_timestamp):
                            insert_event_to_db(cursor, 'team_join_log', player_found['steam_id'], join_timestamp, {
                                'team': team
                            })
           
            # Check for round result events
            round_result_match = re.search(round_result_pattern, line)
            if round_result_match:
                round_timestamp = round_result_match.group('timestamp')
                winner_team = round_result_match.group('winner_team')

                for player in players.values():
                    if was_player_active(player, round_timestamp):
                        if player['team'] == winner_team:
                            player['round_winner'] += 1
                        else:
                            player['round_loser'] += 1

                        # Insert into the database
                        if not event_exists(cursor, 'round_result_log', player['steam_id'], round_timestamp):
                            insert_event_to_db(cursor, 'round_result_log', player['steam_id'], round_timestamp, {
                                'winner_team': winner_team
                            })

            # Check for destroyed events
            destroyed_match = re.search(destroyed_pattern, line)
            if destroyed_match:
                destroyed_timestamp = destroyed_match.group('timestamp')
                player_name = destroyed_match.group('player_name')
                steam_id = destroyed_match.group('steam_id')
                destroyed_team = destroyed_match.group('destroyed_team')

                # Ensure player exists in the players dictionary
                ensure_player_exists(players, steam_id, player_name)

                # Insert the player into the players table
                insert_player(cursor, steam_id, player_name)

                # Add destroyed and lost_destroyed
                players[steam_id]['destroyed'] += 1
                if destroyed_team == players[steam_id]['team']:
                    players[steam_id]['lost_destroyed'] += 1

                # Insert into the database
                if not event_exists(cursor, 'destroyed_log', steam_id, destroyed_timestamp):
                    insert_event_to_db(cursor, 'destroyed_log', steam_id, destroyed_timestamp, {
                        'destroyed_team': destroyed_team
                    })

            # Check for capture events
            capture_match = re.search(capture_pattern, line)
            if capture_match:
                capture_timestamp = capture_match.group('timestamp')
                captured_team = capture_match.group('captured_team')
                previous_team = capture_match.group('previous_team')
                player_name = capture_match.group('player_name')
                steam_id = capture_match.group('steam_id')

                # Ensure player exists in the players dictionary
                ensure_player_exists(players, steam_id, player_name)

                # Insert the player into the players table
                insert_player(cursor, steam_id, player_name)

                # Add capture and lost_capture
                players[steam_id]['captures'] += 1
                if previous_team == players[steam_id]['team']:
                    players[steam_id]['lost_capture'] += 1

                # Insert into the database
                if not event_exists(cursor, 'capture_log', steam_id, capture_timestamp):
                    insert_event_to_db(cursor, 'capture_log', steam_id, capture_timestamp, {
                        'captured_team': captured_team,
                        'previous_team': previous_team
                    })

    # Now calculate and update ELO for each player
    for player in players.values():
        new_elo = calculate_elo(player)
        update_player_elo(cursor, player['steam_id'], new_elo)

    # Commit the transactions and close the connection
    conn.commit()
    cursor.close()
    conn.close()

# Function to parse both logs
def parse_both_logs():
    parse_log(local_file)
    parse_log(local_file2)

# First, download both logs
download_logs()

# Now, parse both logs
parse_both_logs()

