from flask import Blueprint, render_template, jsonify, request, redirect, abort, url_for, current_app
from app.models import Show, Episode, Season, CustomRow, db
from app.utils import process_media_playlist
import json
import logging
import os


bp = Blueprint('main', __name__)

# Configure logging
logger = logging.getLogger(__name__)
if os.environ.get('FLASK_ENV') == 'production':
    logger.setLevel(logging.ERROR)  # Only log errors in production
else:
    logger.setLevel(logging.DEBUG)  # Keep debug logging for development
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@bp.route('/')
def show_selection():
    shows = Show.query.all()
    custom_rows = CustomRow.query.order_by(CustomRow.order).all()  # Order by the new order field
    
    # Order shows within each custom row
    for row in custom_rows:
        try:
            row.ordered_shows = sorted(
                row.shows, 
                key=lambda x: row.show_order.index(x.id) if x.id in row.show_order else len(row.show_order)
            )
        except ValueError as e:
            logger.error(f"Error ordering shows in custom row {row.id}: {e}")
            row.ordered_shows = row.shows  # Fallback to unordered
    
    logger.debug(f"Number of shows: {len(shows)}")
    logger.debug(f"Number of custom rows: {len(custom_rows)}")
    
    return render_template('shows.html', shows=shows, custom_rows=custom_rows)

@bp.route('/get_episodes/show/<string:show_id>')
def get_episodes_by_show(show_id):
    show = Show.query.get_or_404(show_id)
    episodes = Episode.query.filter_by(show_id=show_id).order_by(Episode.number).all()
    logger.debug(f"Fetched {len(episodes)} episodes for show {show_id}")
    return jsonify([episode.to_dict() for episode in episodes])

@bp.route('/get_episodes/season/<string:season_id>')
def get_episodes_by_season(season_id):
    season = Season.query.get_or_404(season_id)
    episodes = [{'id': e.id, 'name': e.name, 'description': e.description} for e in season.episodes]
    logger.debug(f"Fetched {len(episodes)} episodes for season {season_id}")
    return jsonify(episodes)

@bp.route('/play/<string:episode_id>/<string:show_id>')
def init_episode(episode_id, show_id):
    logger.debug(f"init_episode called with episode_id: {episode_id}, show_id: {show_id}")
    
    if not episode_id or not show_id:
        logger.error("Missing episode_id or show_id in the request")
        abort(400, description="Episode ID and Show ID are required.")
    
    episode = Episode.query.get(episode_id)
    if not episode:
        logger.error(f"Episode with ID {episode_id} not found")
        abort(404, description="Episode not found.")
    
    show = Show.query.get(show_id)
    if not show:
        logger.error(f"Show with ID {show_id} not found")
        abort(404, description="Show not found.")
    
    selected_episode_url = episode.url
    scte_message = "Monitoring for ad breaks..."
    
    try:
        scte_markers = process_media_playlist(selected_episode_url)
        logger.debug(f"SCTE markers: {scte_markers}")
    except Exception as e:
        logger.error(f"Error processing media playlist: {e}")
        scte_markers = []
    
    # Determine the next episode
    next_episode = get_next_episode(episode)
    if next_episode:
        logger.debug(f"Next episode found: {next_episode.id}")
        next_episode_data = {
            'id': next_episode.id,
            'name': next_episode.name,
            'thumbnail_url': next_episode.thumbnail_url or url_for('static', filename='images/default_thumbnail.png')
        }
    else:
        logger.debug("No next episode found")
        next_episode_data = None

    response = render_template('player.html', 
                               scte_message=scte_message, 
                               episode_url=selected_episode_url,
                               episode=episode,
                               show=show,
                               scte_markers=scte_markers,
                               next_episode=next_episode_data)
    logger.debug("Rendered player.html successfully")
    return response, {'Permissions-Policy': 'browsing-topics=()'}

def get_next_episode(current_episode):
    """
    Determines the next episode based on the current episode's season and number.
    """
    logger.debug(f"Determining next episode for current_episode_id: {current_episode.id}")
    
    if not current_episode.season_id or not current_episode.number:
        logger.warning(f"Current episode {current_episode.id} lacks season_id or number")
        return None

    current_season = Season.query.get(current_episode.season_id)
    if not current_season:
        logger.warning(f"Season with ID {current_episode.season_id} not found for episode {current_episode.id}")
        return None

    current_number = current_episode.number
    logger.debug(f"Current episode number: {current_number} in season {current_season.id}")

    # Attempt to find the next episode in the same season
    next_episode = Episode.query.filter_by(season_id=current_season.id, number=current_number + 1).first()
    if next_episode:
        logger.debug(f"Next episode in the same season found: {next_episode.id}")
        return next_episode

    # If not found, attempt to find the first episode of the next season
    next_season = Season.query.filter(
        Season.show_id == current_season.show_id, 
        Season.number > current_season.number
    ).order_by(Season.number).first()
    
    if next_season:
        next_episode = Episode.query.filter_by(season_id=next_season.id, number=1).first()
        if next_episode:
            logger.debug(f"First episode of next season {next_season.id} found: {next_episode.id}")
            return next_episode
        else:
            logger.debug(f"No episodes found in next season {next_season.id}")
    
    # If no next episode exists
    logger.debug(f"No next episode available after season {current_season.id}")
    return None


@bp.route('/status')
def status():
    scte_message = "No ad break detected yet."
    ad_played = False
    logger.debug("Status endpoint called")
    return jsonify(scte_message=scte_message, ad_played=ad_played)

@bp.route('/show/<string:show_id>')
def show_detail(show_id):
    show = Show.query.get_or_404(show_id)
    logger.debug(f"Showing details for show_id: {show_id}")
    return render_template('show_detail.html', show=show)

@bp.route('/ads.txt')
def ads_txt():
    logger.debug("Redirecting to ads.txt")
    return redirect('https://adstxt.guru/hosting/EqzTPODF6Imv8za6tjmmGYWlWrfqzEHW/')

@bp.route('/app-ads.txt')
def app_ads_txt():
    logger.debug("Redirecting to app-ads.txt")
    return redirect('https://adstxt.guru/hosting/EqzTPODF6Imv8za6tjmmGYWlWrfqzEHW/')
