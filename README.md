# Multiplayer Snake Game with Server-Client Architecture

## Overview
This repository hosts the code for a snake game designed with a server-client architecture. It includes a single-client version and an extended multiplayer version that supports multiple clients, public messaging, and RSA encryption for secure communication.

## Features

### Single-client Snake Game
- Server-centric game logic and state management.
- Client handles input and renders game state updates.
- Utilizes TCP socket communication.

### Multiplayer Snake Game
- Supports multiple clients with individual control over snakes.
- Implements public messaging among clients.
- Integrates RSA encryption for secure data exchange.

## Technologies Used
- **Python 3**: Main programming language.
- **Pygame**: Used for rendering the graphical interface.
- **Socket**: Facilitates network communication.
- **RSA**: Ensures secure message transmission.

## Installation
Clone the repository and install dependencies:
```bash
git clone <repository-url>
cd <project-directory>
pip install pygame rsa
```

![user interface](images/single_client_screenshot.png)

<img width="1437" alt="img" src="https://github.com/Jellyfish135/tcp_server_multiplayer_snake_game/assets/135635944/2ba5f1a0-aa5e-424e-9bfb-c2313edcbdcc">
