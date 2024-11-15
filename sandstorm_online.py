import mysql.connector
import socket
import struct
import re
import time

# RCON packet types
SERVERDATA_AUTH = 3
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_RESPONSE_VALUE = 0
SERVERDATA_AUTH_RESPONSE = 2

class Rcon:
    def __init__(self, host, port, password, timeout=10):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.socket = None
        self.request_id = 0
        self.connected = False

    def connect(self):
        print(f"Connecting to RCON server at {self.host}:{self.port}...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.host, self.port))
        self.connected = True
        print("RCON connection established.")

        if not self.authenticate():
            raise Exception("RCON authentication failed.")
        print("RCON authentication successful.")

    def authenticate(self):
        self.send_packet(SERVERDATA_AUTH, self.password)
        response = self.receive_packet()
        print(f"Auth Response: {response}")
        return response['request_id'] != -1

    def send_packet(self, packet_type, body):
        self.request_id += 1
        packet = struct.pack('<ii', self.request_id, packet_type)
        packet += body.encode('utf-8') + b'\x00\x00'
        packet = struct.pack('<i', len(packet)) + packet
        self.socket.sendall(packet)

    def receive_packet(self):
        try:
            packet_size = struct.unpack('<i', self.socket.recv(4))[0]
            response = self.socket.recv(packet_size)
            request_id, packet_type = struct.unpack('<ii', response[:8])
            body = response[8:-2].decode('utf-8')
            return {'request_id': request_id, 'packet_type': packet_type, 'body': body}
        except Exception as e:
            print(f"Error receiving packet: {e}")
            return {'request_id': -1, 'packet_type': -1, 'body': ''}

    def execute(self, command):
        self.send_packet(SERVERDATA_EXECCOMMAND, command)
        response = self.receive_packet()
        return response['body']

    def disconnect(self):
        if self.socket:
            self.socket.close()
        self.connected = False
        print("RCON connection closed.")

def clear_online_players_table(conn):
    """Clear the online_players table before each run."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM online_players")
    conn.commit()
    cursor.close()
    print("Cleared online_players table.")

def insert_online_player(steam_id, name, player_id, conn):
    """Insert player data into the online_players table."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO online_players (steam_id, name, player_id)
        VALUES (%s, %s, %s)
        """,
        (steam_id, name, player_id)
    )
    conn.commit()
    cursor.close()
    print(f"Inserted player - Steam ID: {steam_id}, Name: {name}, Player ID: {player_id}")

def parse_players(response, conn):
    """Parse player information and insert into the online_players table."""
    players = response.split('\n')
    print(f"Raw response data:\n{response}")  # Print the raw RCON response

    valid_player_count = 0
    for player in players:
        print(f"Raw player data: {player}")  # Print each line before processing
        match = re.search(r"(\d+)\s+\|\s+([^\|]+)\s+\|\s+SteamNWI:(\d+)", player)
        if match:
            player_id = match.group(1).strip()
            name = match.group(2).strip()
            steam_id = match.group(3).strip()

            print(f"Processing Player - ID: {player_id}, Name: {name}, Steam ID: {steam_id}")
            insert_online_player(steam_id, name, player_id, conn)
            valid_player_count += 1
        else:
            print(f"Could not parse player: {player}")

    print(f"Successfully processed {valid_player_count} players.")

if __name__ == '__main__':
    # RCON server details
    host = ''
    port = 
    password = ''

    # Connect to MySQL
    conn = mysql.connector.connect(
        host='',
        database='',
        user='',
        password=''
    )

    # Clear the online_players table before inserting new data
    clear_online_players_table(conn)

    # Create RCON object
    rcon = Rcon(host, port, password)

    try:
        # Connect to RCON
        rcon.connect()

        # Execute RCON command to get player data
        list_players_response = rcon.execute("ListPlayers")
        if list_players_response.strip():
            parse_players(list_players_response, conn)
        else:
            print("No player data found.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()
            print("MySQL connection closed.")
        rcon.disconnect()

