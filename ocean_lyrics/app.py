import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import os
from dotenv import load_dotenv

load_dotenv()  # Loads keys from .env

spotify_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
genius_token = os.getenv("GENIUS_ACCESS_TOKEN")
# when app:
# SPOTIFY_CLIENT_ID = st.secrets["SPOTIFY_CLIENT_ID"]
# SPOTIFY_CLIENT_SECRET = st.secrets["SPOTIFY_CLIENT_SECRET"]
# SPOTIFY_REDIRECT_URI = st.secrets["SPOTIFY_REDIRECT_URI"]

