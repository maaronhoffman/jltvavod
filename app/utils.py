import requests
from flask import current_app, url_for
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import logging
import json
import os

logging.basicConfig(level=logging.DEBUG)

def get_cue_points(guid):
    url = f"https://tlmastercontrol.teleosmedia.com/backend/media/usingid/{guid}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cues = data.get('cues', [])
        return [cue['offset'] / 1000 for cue in cues]  # Convert milliseconds to seconds
    return []

def process_media_playlist(master_playlist_url):
    parsed_url = urlparse(master_playlist_url)
    path_parts = parsed_url.path.split('/')
    guid = path_parts[-2]  # Assuming GUID is always the second-to-last part of the path
    
    cue_points = get_cue_points(guid)
    
    all_scte_markers = []
    for cue_point in cue_points:
        all_scte_markers.append({
            'time': cue_point,
            'tag': "Found" 
        })
    
    print(f"Found {len(all_scte_markers)} SCTE markers")
    return all_scte_markers

def fetch_episode_data(episode_ids):
    episodes_data = []
    for episode_id in episode_ids:
        json_url = f"https://tlmastercontrol.teleosmedia.com/backend/media/usingid/{episode_id}"
        logging.debug(f"Requesting URL: {json_url}")
        response = requests.get(json_url)
        logging.debug(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logging.debug(f"Response Data: {data}")
            episode_data = {
                'id': data['id'],
                'name': data['title'],
                'url': f"https://vcnjltv.teleosmedia.com/vod/jltv/{episode_id}/playlist.m3u8",
                'description': data['metaData']['description'],
                'short_description': data['metaData']['shortDescription'],
                'keywords': ', '.join([keyword['keyword'] for keyword in data['keywords']]),
                'category': data['metaData']['iabCategory']['description'],
                'thumbnail_url': data['poster']
            }
            episodes_data.append(episode_data)
        else:
            logging.error(f"Failed to fetch data for episode ID {episode_id}")
            raise Exception(f"Failed to fetch data for episode ID {episode_id}")
    return episodes_data

def save_file(file, upload_folder):
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return url_for('static', filename=f'uploads/{filename}')