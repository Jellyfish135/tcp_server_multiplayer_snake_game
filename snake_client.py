# Juyoung Lee
# Dec,8,2023
import socket
import pygame
import sys
import re
import rsa
import random


# Define server address and port
server = "localhost"
port = 5555

# Create a socket to connect to the server and connect to server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server, port))

# Initialize Pygame
pygame.init()

# Set the width and rows for drawing cubes
w = 500
rows = 20

# Player colors
player_colors = [(255, 0, 0),
    (0, 255, 0),   
    (0, 0, 255),   
    (255, 255, 0), 
    (255, 0, 255), 
    (0, 255, 255)]

# Define predefined messages and hotkeys for this player
predefined_messages = {
    'z': "Congratulations!",
    'x': "It works!",
    'c': "Ready?"
}

# Function to load the server's public key
def load_server_public_key():
    with open('public_key.pem', 'rb') as p:
        return rsa.PublicKey.load_pkcs1(p.read())

server_public_key = load_server_public_key()

# Function to send control commands to the server
def send_control_command(command):
    client_socket.send(command.encode())

# Modify only the send_global_chat_message function to encrypt messages
def send_global_chat_message(message):
    encrypted_message = rsa.encrypt(("chat|global|" + message).encode(), server_public_key)
    client_socket.send(encrypted_message)


# Function to request the current game state
def get_game_state():
    send_control_command("get")
    game_state = client_socket.recv(1024).decode()
    return game_state

# Function to draw a cube
def drawCube(surface, pos, color, is_head=False):
    dis = w // rows
    x, y = pos
    pygame.draw.rect(surface, color, (x * dis, y * dis, dis, dis))
    if is_head:
        centre = dis // 2
        radius = 3
        eye_color = (0, 0, 0)
        eye1_pos = (x * dis + centre - radius, y * dis + 8)
        eye2_pos = (x * dis + dis - radius * 2, y * dis + 8)
        pygame.draw.circle(surface, eye_color, eye1_pos, radius)
        pygame.draw.circle(surface, eye_color, eye2_pos, radius)

def render_game(screen, game_state):
    def parse_position_str(positions_str):
        positions = []
        messages = []

        # Use regular expressions to find valid positions and chat messages
        pattern = r'\((\d+), (\d+)\)|([^\(\)]+)'
        matches = re.findall(pattern, positions_str)

        for match in matches:
            x, y, message = match
            if x and y:
                # If x and y are not None, it's a valid position
                positions.append((int(x), int(y)))
            elif message:
                # If message is not None, it's a chat message
                messages.append(message.strip())

        return positions, messages

    def drawPlayer(screen, player_data, color):
        for pos_or_message in player_data:
            if isinstance(pos_or_message, tuple):
                # It's a regular position, unpack and draw
                x, y = pos_or_message
                drawCube(screen, (x, y), color, is_head=(pos_or_message == player_data[0]))
            else:
                print(pos_or_message)

    def drawSnacks(screen, snack_positions):
        for pos in snack_positions:
            coords = pos.strip("()").split(',')
            if len(coords) == 2 and all(c.strip().isdigit() for c in coords):
                x, y = map(int, coords)
                drawCube(screen, (x, y), (0, 255, 0))
            else:
                print("Invalid snack position:", pos)

    # Clear the screen
    screen.fill((0, 0, 0))

    # Split the received data into game state and chat message parts
    game_data_parts = game_state.split("|")
    if len(game_data_parts) > 1 and "Player global: " in game_data_parts[1]:
        snack_data, chat_message = game_data_parts[1].split("Player global: ", 1)
        game_data_parts[1] = snack_data
        print("Public message: ",chat_message)
    else:
        snack_data = game_data_parts[1] if len(game_data_parts) > 1 else ""

    # Process player positions
    if len(game_data_parts) >= 1:
        player_data = game_data_parts[0]
        players_data = player_data.split("**")
        for idx, player_data in enumerate(players_data):
            positions, messages = parse_position_str(player_data)

            if idx < len(player_colors):
                color = player_colors[idx]
            else:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            drawPlayer(screen, positions, color)

            # Handle chat messages
            for message in messages:
                handle_chat_messages(message)

    # Handle snack positions
    snacks_pos = snack_data.split("**")
    for snack_pos in snacks_pos:
        coords = snack_pos.strip("()").split(',')
        if len(coords) == 2:
            x, y = map(int, coords)
            drawCube(screen, (x, y), (0, 255, 0))  # Snack color

    # Draw grid lines
    dis = w // rows
    for x in range(0, w, dis):
        pygame.draw.line(screen, (255, 255, 255), (x, 0), (x, w))
    for y in range(0, w, dis):
        pygame.draw.line(screen, (255, 255, 255), (0, y), (w, y))

    pygame.display.update()

# Add a global list to store sent messages
sent_messages = []

# Modify send_global_chat_message to log sent messages
def send_global_chat_message(message):
    client_socket.send(("chat|global|" + message).encode())
    sent_messages.append({"message": message, "displayed": False})
    

# Function to display undisplayed sent messages
def display_undisplayed_messages():
    for msg in sent_messages:
        if not msg["displayed"]:
            print(f"Sent message: {msg['message']}")
            msg["displayed"] = True

# Main game loop
def main():
    screen = pygame.display.set_mode((500, 500))
    pygame.display.set_caption("Snake Game")

    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    send_control_command("up")
                elif event.key == pygame.K_DOWN:
                    send_control_command("down")
                elif event.key == pygame.K_LEFT:
                    send_control_command("left")
                elif event.key == pygame.K_RIGHT:
                    send_control_command("right")
                elif event.key == pygame.K_r:
                    send_control_command("reset")
                elif event.key == pygame.K_q:
                    send_control_command("quit")
                elif event.unicode in predefined_messages:
                    send_global_chat_message(predefined_messages[event.unicode])

        try:
            game_state = get_game_state()
            render_game(screen, game_state)
            handle_chat_messages(game_state)
            display_undisplayed_messages()

        except ConnectionResetError:
            print("Disconnected from the server.")
            break

        clock.tick(10)
    client_socket.close()
    pygame.quit()

# Function to handle chat messages
def handle_chat_messages(game_state):
    chat_data = game_state.split("chat|")
    if len(chat_data) > 1:
        message = chat_data[1]
        print("Received chat message:", message)

if __name__ == "__main__":
						    main()
