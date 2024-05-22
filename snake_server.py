# Juyoung Lee
# Dec,8,2023

import numpy as np
import socket
from _thread import *
import pickle
from snake import SnakeGame
import uuid
import time 
import threading
import rsa


server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

counter = 0 
rows = 20 

# Dictionary to store connected players with their unique IDs
connected_players = {}

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen()
print("Waiting for a connection, Server Started")


# Generate public and private keys
(public_key, private_key) = rsa.newkeys(512)  # Adjust key size as needed

# Save the public key
with open('public_key.pem', 'wb') as p:
    p.write(public_key.save_pkcs1('PEM'))

# Save the private key
with open('private_key.pem', 'wb') as p:
    p.write(private_key.save_pkcs1('PEM'))


game = SnakeGame(rows)
game_state = "" 
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()

# Define locks for synchronization
game_state_lock = threading.Lock()
moves_queue_lock = threading.Lock()
player_positions = {}  # Store player positions and directions


# Function to load the server's private key
def load_private_key():
    with open('private_key.pem', 'rb') as p:
        return rsa.PrivateKey.load_pkcs1(p.read())
server_private_key = load_private_key()


def game_thread():
    global game, game_state, moves_queue
    while True:
        last_move_timestamp = time.time()
        
        # Acquire locks before updating game_state and moves_queue
        with game_state_lock:
            game.move(list(moves_queue))
        with moves_queue_lock:
            moves_queue = set()

        # Update player positions and directions
        for user_id, move in moves_queue:
            if user_id not in player_positions:
                player_positions[user_id] = (10, 10)
            if move:
                if move == "up":
                    player_positions[user_id] = (player_positions[user_id][0], player_positions[user_id][1] - 1)
                elif move == "down":
                    player_positions[user_id] = (player_positions[user_id][0], player_positions[user_id][1] + 1)
                elif move == "left":
                    player_positions[user_id] = (player_positions[user_id][0] - 1, player_positions[user_id][1])
                elif move == "right":
                    player_positions[user_id] = (player_positions[user_id][0] + 1, player_positions[user_id][1])

        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval:
            time.sleep(0.1)


rgb_colors = {
    "red" : (255, 0, 0),
    "green" : (0, 255, 0),
    "blue" : (0, 0, 255),
    "yellow" : (255, 255, 0),
    "orange" : (255, 165, 0),
} 
rgb_colors_list = list(rgb_colors.values())


# Dictionary to store connected players with their unique IDs and connection objects
connected_players = {}


# Function to handle client disconnection
def handle_client_disconnection(user_id):
    print("Client", user_id, "disconnected.")
    game.remove_player(user_id)
    del connected_players[user_id]


# Define a global lock for chat broadcasting to ensure thread safety
chat_broadcast_lock = threading.Lock()

# Function to broadcast chat messages to all connected players
def broadcast_chat_message(sender_id, message):
    global connected_players

    # Create the formatted chat message to send to all players
    formatted_message = f"Player {sender_id}: {message}"
    with chat_broadcast_lock:
        for player_id, player_data in connected_players.items():
            player_conn = player_data["conn"]
            try:
                if sender_id == "global":
                    # Send global messages to all clients
                    player_conn.send(formatted_message.encode())
                else:
                    # Send regular messages only to the intended player
                    player_conn.send(formatted_message.encode())
            except Exception as e:
                print("Error broadcasting chat message to Player", player_id, ":", e)


def client_thread(conn, addr):
    try:
        # Generate a unique ID for the player
        unique_id = str(uuid.uuid4())

        # Assign a color to the player
        color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]

        # Add the player to the connected_players dictionary with their connection object
        connected_players[unique_id] = {"conn": conn, "color": color}

        # Add the player to the game
        game.add_player(unique_id, color=color)

        while True:
            data = conn.recv(1024)
            if not data:
                break

            try:
                # Attempt to decrypt the data assuming it's a chat message
                decrypted_data = rsa.decrypt(data, server_private_key).decode()
                if decrypted_data.startswith("chat|global|"):
                    data = decrypted_data
            except Exception as e:
                # If decryption fails, assume it's not an encrypted message
                data = data.decode()

            if data == "get":
                # Send game state to the specific client
                conn.send(game.get_state().encode())
            elif data == "quit":
                # Handle client disconnection
                handle_client_disconnection(unique_id)
                break
            elif data.startswith("chat|global|"):
                # Extract the chat message and broadcast it to all players
                chat_message = data.split("|")[2]
                broadcast_chat_message("global", chat_message)
            elif data in ["up", "down", "left", "right"]:
                moves_queue.add((unique_id, data))
            elif data == "reset":
                game.reset_player(unique_id)
            else:
                print("Invalid or unencrypted data received from client:", data)

    except Exception as e:
        print("Client", addr, "disconnected:", e)
        # Handle client disconnection
        handle_client_disconnection(unique_id)
        conn.close()

    conn.close()

def main():
    global counter, game

    conn, addr = s.accept()
    print("Connected to:", addr)
    # Create a new thread for each connected client
    threading.Thread(target=client_thread, args=(conn, addr)).start()

    unique_id = str(uuid.uuid4())
    color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]
    # game.add_player(unique_id, color=color)

    start_new_thread(game_thread, ())

    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)
        start_new_thread(client_thread, (conn, addr))

        # Periodically check for disconnected clients
        disconnected_clients = []
        with game_state_lock:
            for user_id, player in list(game.players.items()):
                try:
                    player_socket = player.client_socket
                    player_socket.settimeout(0.1)
                    player_socket.recv(1)
                except socket.timeout:
                    disconnected_clients.append(user_id)
                except Exception as e:
                    print("Error while checking client socket:", e)

        # Remove disconnected players
        with game_state_lock:
            for user_id in disconnected_clients:
                print("Client", user_id, "disconnected.")
                game.remove_player(user_id)

        # Check if there are no connected clients, and if so, break out of the loop
        if not game.players:
            print("All clients disconnected. Stopping the server.")
            break

    conn.close()


if __name__ == "__main__" : 
    main()
