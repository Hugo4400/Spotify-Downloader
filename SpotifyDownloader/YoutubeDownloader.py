import os
from urllib.error import HTTPError

import eyed3
import requests
from moviepy import editor
from pathvalidate import sanitize_filename
from pytube import YouTube

from SpotifyDownloader.SpotifyWebAPI import get_access_token, get_playlists


def mp4_to_mp3(mp4, mp3):
    mp4_without_frames = editor.AudioFileClip(mp4)
    mp4_without_frames.write_audiofile(mp3)
    mp4_without_frames.close()
    os.remove(mp4)


def downloader(spotify_url: str, location: str):
    try:
        track = get_playlists(spotify_url)
    except TypeError:
        get_access_token()
        track = get_playlists(spotify_url)

    path = f'{location}\\{sanitize_filename(track[0].replace(" ", "-"))}'

    os.makedirs(path)

    dict_of_playlist = track[1]
    tracklist: list[dict[str, str | bytes]] = list()

    for url_name in dict_of_playlist:
        try:
            yt = YouTube(dict_of_playlist[url_name])
            thumbnail_res = requests.get(yt.thumbnail_url)
            thumbnail = bytes(thumbnail_res.content)

            title: str = ""
            artist: str = ""
            album: str = ""

            try:
                metadata: dict[str, str] = yt.metadata[0]
                title = metadata.get("Song", "")
                artist = metadata.get("Artist", "")
                album = metadata.get("Album", "")
            except IndexError:
                pass

            audio = yt.streams.get_audio_only()
            audio.download(output_path=path)

            tracklist.append(
                dict(
                    filename=audio.default_filename,
                    title=title,
                    artist=artist,
                    album=album,
                    thumbnail=thumbnail,
                )
            )

            print(f"Downloaded {url_name} at -> {path}")

        except HTTPError:
            print(f'Couldn\'t download "{url_name}", continuing')
            continue

    print("Downloads done! converting to mp3")

    for file in tracklist:

        filepath = f'{path}\\{file["filename"]}'

        if filepath.endswith(".mp4"):
            mp4_to_mp3(filepath, filepath.replace(".mp4", ".mp3"))
            file["filename"] = file["filename"].replace(".mp4", ".mp3")
            filepath = file["filename"]
            print(f'-- {file["title"]} -- Conversion done!')

        print("Adding metadata to mp3")

        file_mdata = eyed3.load(f'{path}\\{file["filename"]}')
        file_mdata.tag.title = file["title"]
        file_mdata.tag.artist = file["artist"]
        file_mdata.tag.album = file["album"]
        file_mdata.tag.images.set(3, file["thumbnail"], "image/jpeg")
        file_mdata.tag.save()

        print(f'-- {file["title"]} -- Metadata added!')
