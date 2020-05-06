"""
Youtube song videos to Spotify Script
Uses Youtube Data API, Spotify Web API, and Youtube DL package
"""
import json
import requests
import os
from secrets import spotify_user_id
import google_auth_oauthlib.flow
import youtube_dl
import googleapiclient.discovery
import googleapiclient.errors

class CreateSpotifyPlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.getYoutubeClient()
        self.all_song_info = {}

    # Log into your youtube account
    def getYoutubeClient(self):
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    # Create playlist from liked videos first
    def createPlaylist(self):
        # First create request body
        request_body = json.dumps({
            "name": "Youtube favorites"
            "description": "All my favorite Youtube music!"
            "public": True
        })
        # Then create response body and send
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        reponse = requests.post(
            query,
            date = request_body,
            headers = {
                "Content-Type":"application/json"
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        # Sent Response gets saved
        response_json = response.json()
        # Save the playlist ID. Will need this to add songs to Playlist.
        return response_json["id"]

    # Obtain liked music videos from response and place into a dict
    def getVideos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics"
            myRating="like"
        )
        response = request.execute()
        # Pull list of videos and get the title and url
        for video in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])
            # Youtube_dl package to get song name and artist
            vid = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = vid["track"]
            artist = vid["artist"]
            # Save this info into a dict
            self.all_song_info[video_title]={
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,

                # Add in uri to get songs and put into a playlist
                "spotify_uri":self.get_spotify_uri(song_name, artist)
            }
    
    # Look for the song using Spotify Web API
    def getSpotifyURI(self, song_name, artist):
        # Set up search query (from Spotify)
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        # Send response and get the response back
        response = requests.get(
            query,
            headers={
                "Content-Type":"application/json"
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        # Sent Response gets saved
        response_json = response.json()
        # Save the playlist ID. Will need this to add songs to Playlist.
        songList = response_json["tracks"]["items"]

        # For simplicity, we will pull the first song from the list (Could be a future improvement)
        uri = songList[0]["uri"]
        return uri

    # Add songs into a playlist on Spotify
    def addSongs(self):
        # Populate song dict
        self.getVideos()

        # Collect all the uri
        uriList = []
        for song, info in self.all_song_info.items():
            uriList.append(info["spotify_uri"])

        # Create the playlist
        playlistID = self.createPlaylist()

        # Add songs into the playlist
        request_data = json.dumps(uriList)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlistID)
        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type":"application/json"
                "Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        # Return response
        response_json = response.json()
        return response_json = response.json()