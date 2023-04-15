from typing import List
import time
import json
from os import environ, urandom
from datetime import datetime, timedelta
from eth_account.messages import encode_defunct
from eth_utils.crypto import keccak
from fastapi import Depends, Header
from jwt import PyJWTError
from pydantic import ValidationError, dataclasses
from enum import Enum

from fastapi.responses import HTMLResponse, JSONResponse 
from fastapi import FastAPI, HTTPException, WebSocket
from web3 import Web3, HTTPProvider
from web3.auto import w3
from pydantic import BaseModel
from eth_account import Account
import jwt
from fastapi.middleware.cors import CORSMiddleware
from siwe import SiweMessage
import random

app = FastAPI()
# setup cors
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game States
sign_in_queue: dict = {}

SECRET_KEY = environ.get("SECRET_KEY", "atlas")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

class Token(BaseModel):
    access_token: str
    token_type: str

class SignInRequest(BaseModel):
    signature: str
    message: str

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# HANDLE SIGN IN
@app.get("/sign-in")
async def sign_in_request(address: str) -> JSONResponse:
    nonce = urandom(32).hex()
    sign_in_queue[address] = nonce
    return JSONResponse({"nonce": nonce})

@app.post("/sign-in", response_model=Token)
async def sign_in(request: SignInRequest) -> JSONResponse:
    siwe_message = None
    try:
        siwe_message = SiweMessage(message=request.message)
    except:
        raise HTTPException(status_code=400, detail="Invalid auth payload")

    if siwe_message.address not in sign_in_queue:
        raise HTTPException(status_code=400, detail="No sign in request found")

    if siwe_message.nonce != sign_in_queue[siwe_message.address]:
        raise HTTPException(status_code=400, detail="Invalid nonce")
    
    try:
        siwe_message.verify(request.signature)
    except:
        raise HTTPException(status_code=400, detail="Invalid signature")

    del sign_in_queue[siwe_message.address]

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": siwe_message.address}, expires_delta=access_token_expires)

    return JSONResponse({"access_token": access_token, "token_type": "bearer"})

# Add this function to verify and decode the access token
def verify_access_token(token: str):
    token_parts = token.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=400, detail="Invalid access token format")
    try:
        payload = jwt.decode(token_parts[1], SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except (PyJWTError, ValidationError):
        raise HTTPException(status_code=400, detail="Invalid access token")

# Implement the /get endpoint
@app.get("/get-token-address")
async def get_user(access_token: str = Header(..., alias="Authorization")) -> JSONResponse:
    user_address = verify_access_token(access_token)
    return JSONResponse({"address": user_address})

active_players: dict = {}
# Game
# 5 preset NPC pokemon
# Return on every round for both players:
# HP = 200
# MANA = 10
# Attack = 100
# Defence = 100

# Mana increases by 2 every turn, max 10


# flow 
# 1. When a player connects, they send an access token
# 2. The server verifies the access token
# 3. If the access token is valid, the server adds the player to the active_players list

class GameStates(Enum):
    WAITING_FOR_PLAYER = 0
    WAITING_FOR_OPPONENT = 1
    FINISHED = 2


NPCS = [
    {
        "name": "Fireasaur",
        "monster_type": "fire", 
        "image": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/6.png",
        "moves": [
           "fireball",
           "overheat",
           "headbutt",
           "fire dance"
        ]
    },
    {
        "name": "Watermander",
        "monster_type": "water", 
        "image": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/23.png",
        "moves": [
            "fountain of youth",
            "hyper beam",
            "tsunami",
            "waterfall"
        ]
    },
    {
        "name": "Guirtle",
        "monster_type": "grass", 
        "image": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/63.png",
        "moves": [
            "solar dance",
            "leaf storm",
            "giga drain",
            "headbutt"
        ]
    },
]


async def verify_token_id(token_id: str, user_address: str):
    return {"monster_type": "fire", "name": "Goblinachu", "image": "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/912.png","moves": ["fireball", "overheat", "headbutt", "fire dance"]}


def calculate_modifier(attacker_type: str, defender_type: str) -> float:
    if attacker_type == "fire":
        if defender_type == "water":
            return 0.75
        elif defender_type == "grass":
            return 1.25
    elif attacker_type == "water":
        if defender_type == "fire":
            return 1.25
        elif defender_type == "grass":
            return 0.75
    elif attacker_type == "grass":
        if defender_type == "fire":
            return 0.75
        elif defender_type == "water":
            return 1.25
    return 1

def perform_state_transition(game_state, current_player_key, opponent_player_key, move_data):
    temp_game_state = game_state.copy()

    # handle mana calculation
    temp_game_state[current_player_key]['mana'] -= move_data['mana_cost']
    if temp_game_state[current_player_key]['mana'] < 0:
        raise Exception("Not enough mana")

    if temp_game_state[current_player_key]['mana'] < 9:
        temp_game_state[current_player_key]['mana'] += 2
    else:
        temp_game_state[current_player_key]['mana'] = 10

    # handle health updates 
    temp_game_state[current_player_key]['hp'] += move_data['heal']

    # Handle debuffs
    if move_data['debuffType'] != "none" or move_data['debuffType'] !=  None:
        if move_data['debuffType'] == "defense":
            temp_game_state[opponent_player_key]['defense'] -= move_data["debuffAmount"]
        else:
            temp_game_state[opponent_player_key]['attack'] -= move_data["debuffAmount"]

    # Handle buffs
    if move_data['buffType'] != "none" or move_data['buffType'] !=  None:
        if move_data['buffType'] == "defense":
            temp_game_state[current_player_key]['defense'] += move_data["buffAmount"]
        else:
            temp_game_state[current_player_key]['attack'] += move_data["buffAmount"]


    # handle damage calculation
    modifier = calculate_modifier(temp_game_state[current_player_key]['monster_type'], temp_game_state[opponent_player_key]['monster_type'])
    damage_dealt = move_data['damage'] * (
        temp_game_state[current_player_key]['attack'] / temp_game_state[opponent_player_key]['defense']
    ) * modifier
    temp_game_state[opponent_player_key]['hp'] -= damage_dealt
    
    # log this move 
    temp_game_state['state_transitions'].append({"player": current_player_key, "move": move_data['name']})

    # determine if game over 
    if temp_game_state[opponent_player_key]['hp'] <= 0:
        temp_game_state['state'] = GameStates.FINISHED.value
        temp_game_state['winner'] = current_player_key
    
    if temp_game_state['state'] == GameStates.WAITING_FOR_PLAYER.value:
        temp_game_state['state'] = GameStates.WAITING_FOR_OPPONENT.value
    else:
        temp_game_state['state'] = GameStates.WAITING_FOR_PLAYER.value
    return temp_game_state
    
def get_move_logic(move_name, move_map):
    for move in move_map:
        if move['name'] == move_name:
            return move
    return None

@app.websocket("/play")
async def play(websocket: WebSocket):
    await websocket.accept()
    """
    {"access_token": "token", "token_id": "token_id"}
    """
    auth = await websocket.receive_json()
    user_address = None
    try:
        user_address = verify_access_token(auth["access_token"])
    except:
        await websocket.send_json({"error": "Invalid access token"})
        await websocket.close()
         
    # TODO:
    # Verify requested token is owned by address
    # Load its valid moves
    move_map = json.loads(open("./server/moves.json", "r").read())
    player = await verify_token_id(auth["token_id"], user_address) #type:ignore
    npc = random.choice(NPCS)
    game_state = {
        "state": GameStates.WAITING_FOR_PLAYER.value,
        "winner": None,
        "turn": 0,
        "state_transitions": [],
        "npc": {
            "hp": 200,
            "mana": 10,
            "attack": 100,
            "defense": 100,
            "name": npc["name"],
            "valid_moves": npc["moves"],
            "image": npc["image"],
            "monster_type": npc["monster_type"]
        },
        "player": {
            "hp": 200,
            "mana": 10,
            "attack": 100,
            "defense": 100,
            "name": player["name"],
            "valid_moves": player["moves"],
            "image": player["image"],
            "monster_type": player["monster_type"]
        },
    }
    await websocket.send_json(game_state)
    while (game_state['state'] != GameStates.FINISHED):
        move_name = (await websocket.receive_json())['move']
        if move_name not in game_state['player']['valid_moves']:
            await websocket.send_json({"error": "Invalid move"})
            continue

        move_logic = get_move_logic(move_name, move_map)
        if move_logic is None:
            await websocket.send_json({"error": "Invalid move"})
            continue

        game_state = perform_state_transition(game_state, "player", "npc", move_logic)
        await websocket.send_json(game_state)
        time.sleep(random.randint(1, 5))
        npc_move_logic = get_move_logic(random.choice(game_state['npc_stats']['valid_moves']), move_map)
        # Random move logic
        game_state = perform_state_transition(game_state, "npc", "player", npc_move_logic)
        await websocket.send_json(game_state)

    # GAME over
    # TODO:
    # Add game outcome onchain 
    await websocket.close()

