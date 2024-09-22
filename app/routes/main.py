from flask import Blueprint, render_template, jsonify, request
from app.models import Show, Episode, Season, CustomRow
from app.utils import process_media_playlist
import json

bp = Blueprint('main', __name__)

@bp.route('/')
def show_selection():
    shows = Show.query.all()
    custom_rows = CustomRow.query.order_by(CustomRow.order).all()  # Order by the new order field
    
    # Order shows within each custom row
    for row in custom_rows:
        row.ordered_shows = sorted(row.shows, key=lambda x: row.show_order.index(x.id) if x.id in row.show_order else len(row.show_order))
    
    return render_template('shows.html', shows=shows, custom_rows=custom_rows)


@bp.route('/get_episodes/<string:show_id>')
def get_episodes_by_show(show_id):
    show = Show.query.get_or_404(show_id)
    episodes = Episode.query.filter_by(show_id=show_id).all()
    return jsonify([episode.to_dict() for episode in episodes])

@bp.route('/get_episodes/<string:season_id>')
def get_episodes_by_season(season_id):
    season = Season.query.get_or_404(season_id)
    episodes = [{'id': e.id, 'name': e.name, 'description': e.description} for e in season.episodes]
    return jsonify(episodes)

@bp.route('/play/<string:episode_id>/<string:show_id>')
def init_episode(episode_id, show_id):
    episode = Episode.query.get_or_404(episode_id)
    show = Show.query.get_or_404(show_id)
    selected_episode_url = episode.url
    scte_message = "Monitoring for ad breaks..."
    
    scte_markers = process_media_playlist(selected_episode_url)

    response = render_template('player.html', 
                           scte_message=scte_message, 
                           episode_url=selected_episode_url,
                           episode=episode,
                           show=show,
                           scte_markers=json.dumps(scte_markers))
    return response, {'Permissions-Policy': 'browsing-topics=()'}

@bp.route('/status')
def status():
    scte_message = "No ad break detected yet."
    ad_played = False
    return jsonify(scte_message=scte_message, ad_played=ad_played)

@bp.route('/get_episodes/<string:season_id>')
def get_episodes(season_id):
    season = Season.query.get_or_404(season_id)
    episodes = [{'id': e.id, 'name': e.name, 'description': e.description} for e in season.episodes]
    return jsonify(episodes)

@bp.route('/show/<string:show_id>')
def show_detail(show_id):
    show = Show.query.get_or_404(show_id)
    return render_template('show_detail.html', show=show)
