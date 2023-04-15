from typing import List
from os import environ, urandom
from datetime import datetime, timedelta
from eth_account.messages import encode_defunct
from eth_utils.crypto import keccak
from fastapi import Depends, Header
from jwt import PyJWTError
from pydantic import ValidationError


from fastapi.responses import HTMLResponse, JSONResponse 
from fastapi import FastAPI, HTTPException
from web3 import Web3, HTTPProvider
from web3.auto import w3
from pydantic import BaseModel
from eth_account import Account
import jwt
from fastapi.middleware.cors import CORSMiddleware
from siwe import SiweMessage

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
game_state: dict[str, dict] = {}
active_players: dict = {}
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
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except (PyJWTError, ValidationError):
        raise HTTPException(status_code=400, detail="Invalid access token")

# Implement the /get endpoint
@app.get("/get-token-address")
async def get_user(access_token: str = Header(..., alias="Authorization")) -> JSONResponse:
    # The access token is expected to be in the 'Authorization' header
    # with the format: "Bearer <access_token>"
    print("shit", access_token)
    token_parts = access_token.split()
    if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
        raise HTTPException(status_code=400, detail="Invalid access token format")

    user_address = verify_access_token(token_parts[1])
    return JSONResponse({"address": user_address})


# GAME LOGIC

