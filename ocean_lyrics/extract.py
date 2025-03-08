import spotipy
import lyricsgenius
import pandas as pd
import time
from typing import List
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Track:
    track_name: str
    first_artist: str
    album_name: str
    uri_spotify: str
    track_id_genius: str | None = None

def format_track(raw_track: dict) -> Track:
    """Convert raw Spotify track data to structured class"""
    return Track(
        track_name=raw_track.get("name", ""),
        first_artist=raw_track["artists"][0]["name"] if raw_track.get("artists") else "",
        album_name=raw_track["album"]["name"] if raw_track.get("album") else "",
        uri_spotify=raw_track.get("uri", "")
    )

def get_songs_from_entity(uri: str, sp: spotipy.Spotify) -> List[Track]:
    """
    Fetch all tracks from a Spotify album or playlist
    Returns list of Track dataclass instances
    """
    max_pages = 20 # ~2000 tracks

    # Validate URI format
    parts = uri.split(":")
    if len(parts) < 3 or parts[1] not in {"album", "playlist"}:
        raise ValueError(f"Invalid Spotify URI: {uri}. Must be album or playlist.")

    entity_type, entity_id = parts[1], parts[-1]
    all_tracks = []

    try:
        if entity_type == "album":
            results = sp.album_tracks(entity_id)
        else:
            results = sp.playlist_tracks(entity_id)

        # Paginate through results
        page_count = 0
        while results and page_count < max_pages:
            items = results["items"]
            
            valid_tracks = [item["track"] for item in items if item.get("track")]  # playlists might be empty
            all_tracks.extend(valid_tracks)

            results = sp.next(results) if results["next"] else None
            page_count += 1  # TODO add a warning if reaches max_pages

        return [format_track(t) for t in all_tracks if t]

    except spotipy.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return list(Track())
    except KeyError as e:
        print(f"Missing expected field in response: {e}")
        return list(Track())
    

def is_good_match(song: lyricsgenius.Song, track: Track) -> bool:
    """Verify basic match criteria"""
    # Check primary artist matches (case-insensitive)
    main_artist = song.artist.lower()
    target_artist = track.first_artist.lower()
    
    # Allow partial matches (e.g., "Beyoncé" vs "Beyoncé & JAY-Z")
    return (
        target_artist in main_artist or
        main_artist in target_artist
    )

def add_genius_ids(
    tracks: list[Track],
    genius_client: lyricsgenius.Genius,
    delay: float = 0.5,
    max_retries: int = 2
) -> list[Track]:
    """
    Enrich tracks with Genius IDs using smart searching
    - delay: seconds between requests (avoid rate limits)
    - max_retries: number of search attempts per track
    """
    enriched = []
    
    for track in tracks:
        genius_id = None
        attempt = 0
        
        while attempt < max_retries and not genius_id:
            try:
                # Search using both artist and track name
                song = genius_client.search_song(
                    title=track.track_name,
                    artist=track.first_artist,
                    get_full_info=False  # Faster search
                )
                
                # Verify match quality
                if song and is_good_match(song, track):
                    genius_id = song.id
                    
            except Exception as e:
                print(f"Error searching '{track.track_name}': {str(e)}")
                if "429" in str(e):  # Rate limited
                    time.sleep(5)  # Extra wait for rate limits
                
            attempt += 1
            time.sleep(delay)
        
        enriched.append(replace(track, track_id_genius=genius_id))
    
    return enriched