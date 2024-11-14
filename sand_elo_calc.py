import mysql.connector
import statistics
import time
import logging

# Set up logging
logging.basicConfig(filename='elo_calculation.log', level=logging.DEBUG, 
                    format='%(asctime)s %(message)s')

# Connect to the MySQL database
db_config = {
    'user': '',
    'password': '',
    'host': '',
    'database': ''
}

# Function to establish connection and execute a query with retry on lock
def execute_with_lock_retries(query, params=None, retries=5):
    attempt = 0
    conn = None
    cursor = None
    while attempt < retries:
        try:
            # Establish connection
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            
            # Execute the query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            return conn, cursor  # Return both connection and cursor for further processing

        except mysql.connector.Error as err:
            # Check for lock timeout or deadlock, retry if so
            if 'Lock wait timeout exceeded' in str(err) or 'Deadlock' in str(err):
                attempt += 1
                logging.warning(f"Retrying query due to lock... attempt {attempt}/{retries}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"Error accessing MySQL database: {err}")
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                return None, None  # Return None if some other error occurs

    # If retries are exhausted, return None
    return None, None

# Step 1: Fetch all players and their statistics for ELO calculation
query = """
    SELECT 
        p.steam_id,
        p.player_name,
        COALESCE((SELECT COUNT(k.id) FROM kill_log k WHERE k.steam_id = p.steam_id), 0) as kills,
        COALESCE((SELECT COUNT(v.id) FROM kill_log v WHERE v.victim_steam_id = p.steam_id), 0) as deaths,
        COALESCE((SELECT COUNT(a.id) FROM assist_log a WHERE a.steam_id = p.steam_id), 0) as assists,
        COALESCE((SELECT COUNT(c.id) FROM capture_log c WHERE c.steam_id = p.steam_id), 0) as captures,
        COALESCE((SELECT COUNT(d.id) FROM destroyed_log d WHERE d.steam_id = p.steam_id), 0) as destroyed,
        COALESCE((SELECT COUNT(rl.id) FROM round_result_log rl WHERE rl.steam_id = p.steam_id AND rl.winner_team != 0), 0) as round_loser,
        COALESCE((SELECT COUNT(rw.id) FROM round_result_log rw WHERE rw.steam_id = p.steam_id AND rw.winner_team = 0), 0) as round_winner,
        COALESCE((SELECT COUNT(lc.id) FROM capture_log lc WHERE lc.steam_id = p.steam_id AND lc.captured_team != 0), 0) as lost_capture,
        COALESCE((SELECT COUNT(ld.id) FROM destroyed_log ld WHERE ld.steam_id = p.steam_id AND ld.destroyed_team != 0), 0) as lost_destroyed,
        p.elo2
    FROM players p
    WHERE p.steam_id != 0  -- Exclude bots
"""

conn, cursor = execute_with_lock_retries(query)

if cursor:
    players = cursor.fetchall()

    # Step 2: Recalculate ELO based purely on performance metrics
    elos = []
    performance_stats = []

    def calculate_performance_elo(player):
        # Start with a base ELO of 1000, then adjust based on performance
        performance_elo = 1000

        # Adjust ELO based on stats
        performance_elo += player['kills'] * 1
        performance_elo += player['assists'] * 5
        performance_elo += player['round_winner'] * 50
        performance_elo += player['destroyed'] * 10
        performance_elo += player['captures'] * 10
        performance_elo -= player['deaths'] * 10
        performance_elo -= player['round_loser'] * 15
        performance_elo -= player['lost_capture'] * 10
        performance_elo -= player['lost_destroyed'] * 10
        
        # Ensure no player who contributed drops below 500 ELO
        if player['kills'] > 0 or player['assists'] > 0 or player['captures'] > 0 or player['destroyed'] > 0:
            performance_elo = max(performance_elo, 500)
        
        return performance_elo

    # Collect performance-based ELO scores for all players
    for player in players:
        player_elo = calculate_performance_elo(player)
        elos.append(player_elo)
        performance_stats.append((player['steam_id'], player_elo))
        logging.info(f"Calculated performance ELO for player {player['steam_id']} (Name: {player['player_name']}): {player_elo}")
        
        # Additional logging for players with NULL or zero elo2
        if player['elo2'] is None or player['elo2'] == 0:
            logging.info(f"Player {player['steam_id']} (Name: {player['player_name']}) has NULL or zero elo2, recalculating and updating.")

    # Step 3: Calculate the mean and standard deviation of the newly calculated ELOs
    if elos:  # Ensure there are players with stats before calculating mean and std_dev
        mean_elo = statistics.mean(elos)
        std_dev_elo = statistics.stdev(elos)
        logging.info(f"Mean ELO: {mean_elo}, Std Dev ELO: {std_dev_elo}")

        # Step 4: Rescale ELO to center around 1000
        def rescale_elo(elo, mean_elo, std_dev_elo):
            # Normalize the ELO score and rescale to ensure the mean is 1000
            normalized_elo = (elo - mean_elo) / std_dev_elo
            rescaled_elo = 1000 + normalized_elo * std_dev_elo
            return max(rescaled_elo, 0)  # Ensure no negative ELO

        # Step 5: Update player ELOs in the database with retries on lock
        update_query = """
            UPDATE players
            SET elo2 = %s
            WHERE steam_id = %s
        """
        
        for steam_id, performance_elo in performance_stats:
            new_elo = rescale_elo(performance_elo, mean_elo, std_dev_elo)
            logging.info(f"Updating player {steam_id} with new ELO: {new_elo}")

            # Retry the update with lock checking
            update_conn, update_cursor = execute_with_lock_retries(update_query, (new_elo, steam_id))
            if update_cursor:
                update_conn.commit()
                update_cursor.close()
                logging.info(f"Successfully updated player {steam_id} with ELO2: {new_elo}")
            else:
                logging.error(f"Failed to update player {steam_id} with ELO2: {new_elo}")
            
            if update_conn:
                update_conn.close()

    # Close the cursor and connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()

else:
    logging.error("Failed to connect or execute the query.")

