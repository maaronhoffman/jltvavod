from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required
from app.models import db, Show, Season, Episode, CustomRow
from werkzeug.utils import secure_filename
from app.utils import fetch_episode_data, save_file
import os
import logging
import requests
from app.models import db, Show, Season, Episode
import re
from app.getutil import series, seasons, episodes
import argparse
import datetime
import uuid

logging.basicConfig(level=logging.DEBUG)

bp = Blueprint('admin', __name__)

@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    shows = Show.query.all()
    return render_template('admin_dashboard.html', shows=shows)

@bp.route('/admin/database')
@login_required
def admin_database():
    tables = db.metadata.tables.keys()
    return render_template('admin_database.html', tables=tables)

@bp.route('/admin/add_show', methods=['GET', 'POST'])
@login_required
def add_show():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        poster = request.files['poster']
        logo = request.files['logo']
        banner = request.files['banner']
        theme_color = request.form.get('theme_color_hex')
        air_day = request.form.get('air_day')
        air_time_et = request.form.get('air_time_et')
        air_time_pt = request.form.get('air_time_pt')

        poster_url = ''
        if poster:
            filename = secure_filename(poster.filename)
            poster.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            poster_url = url_for('static', filename=f'uploads/{filename}')

        logo_url = ''
        if logo:
            filename = secure_filename(logo.filename)
            logo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            logo_url = url_for('static', filename=f'uploads/{filename}')

        banner_url = ''
        if banner:
            filename = secure_filename(banner.filename)
            banner.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            banner_url = url_for('static', filename=f'uploads/{filename}')

        air_time = f"{air_day} {air_time_et} ET / {air_time_pt} PT" if air_day and air_time_et and air_time_pt else None

        new_show = Show(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            poster_url=poster_url,
            logo_url=logo_url,
            banner_poster_url=banner_url,
            theme_color=theme_color,
            air_time=air_time
        )

        db.session.add(new_show)
        db.session.commit()
        flash('Show added successfully', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('add_show.html')

@bp.route('/admin/show/<string:show_id>', methods=['GET'])
@login_required
def manage_show(show_id):
    show = Show.query.get_or_404(show_id)
    return render_template('manage_show.html', show=show)

@bp.route('/custom_rows', methods=['GET', 'POST'])
@login_required
def manage_custom_rows():
    if request.method == 'POST':
        name = request.form.get('name')
        row_type = request.form.get('row_type')
        new_row = CustomRow(id=str(uuid.uuid4()), name=name, row_type=row_type, order=CustomRow.query.count())
        db.session.add(new_row)
        db.session.commit()
        return redirect(url_for('admin.manage_custom_rows'))
    
    custom_rows = CustomRow.query.order_by(CustomRow.order).all()
    for row in custom_rows:
        row.ordered_shows = sorted(row.shows, key=lambda x: row.show_order.index(x.id) if x.id in row.show_order else len(row.show_order))
    
    return render_template('custom_rows.html', custom_rows=custom_rows)


@bp.route('/update_custom_row_order/<string:row_id>', methods=['POST'])
@login_required
def update_custom_row_order(row_id):
    data = request.get_json()
    
    if 'row_ids' in data:
        # Updating order of custom rows
        row_ids = data.get('row_ids', [])
        for index, row_id in enumerate(row_ids):
            custom_row = CustomRow.query.get(row_id)
            if custom_row:
                custom_row.order = index
    elif 'show_ids' in data:
        # Updating order of shows within a custom row
        show_ids = data.get('show_ids', [])
        custom_row = CustomRow.query.get(row_id)
        if custom_row:
            custom_row.show_order = show_ids
    
    db.session.commit()
    return jsonify({"success": True})


@bp.route('/admin/custom_row/<string:row_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_custom_row(row_id):
    custom_row = CustomRow.query.get_or_404(row_id)
    if request.method == 'POST':
        custom_row.row_type = request.form.get('row_type')
        
        existing_show_ids = request.form.getlist('shows')
        new_show_ids = request.form.getlist('new_shows')
        all_show_ids = existing_show_ids + new_show_ids
        
        custom_row.shows = Show.query.filter(Show.id.in_(all_show_ids)).all()
        
        custom_row.show_custom_text = {}
        for show in custom_row.shows:
            custom_text = request.form.get(f'custom_text_{show.id}')
            if custom_text:
                custom_row.show_custom_text[str(show.id)] = custom_text
            
            card_image = request.files.get(f'card_image_{show.id}')
            if card_image and allowed_file(card_image.filename):
                filename = secure_filename(card_image.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                card_image.save(file_path)
                show.card_image_url = url_for('static', filename=f'uploads/{filename}')
        
        db.session.commit()
        flash('Custom row updated successfully', 'success')
        return redirect(url_for('admin.manage_custom_rows'))
    
    shows = Show.query.all()
    ordered_shows = sorted(custom_row.shows, key=lambda x: custom_row.show_order.index(str(x.id)) if str(x.id) in custom_row.show_order else len(custom_row.show_order))
    return render_template('edit_custom_row.html', custom_row=custom_row, shows=shows, ordered_shows=ordered_shows)


@bp.route('/custom_row/<string:row_id>/delete', methods=['GET'])
@login_required
def delete_custom_row(row_id):
    row = CustomRow.query.get_or_404(row_id)
    db.session.delete(row)
    db.session.commit()
    flash('Custom row deleted successfully', 'success')
    return redirect(url_for('admin.manage_custom_rows'))


@bp.route('/admin/show/<string:show_id>/add_season', methods=['GET', 'POST'])
@login_required
def add_season(show_id):
    show = Show.query.get_or_404(show_id)
    if request.method == 'POST':
        number = request.form.get('number')
        new_season = Season(id=str(uuid.uuid4()), number=number, show_id=show.id)
        db.session.add(new_season)
        db.session.commit()
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('add_season.html', show=show)

@bp.route('/admin/show/<string:show_id>/season/<string:season_id>/add_episode', methods=['GET', 'POST'])
@login_required
def add_episode(show_id, season_id):
    show = Show.query.get_or_404(show_id)
    season = Season.query.get_or_404(season_id)
    if request.method == 'POST':
        name = request.form.get('name')
        number = request.form.get('number')
        url = request.form.get('url')
        description = request.form.get('description')
        thumbnail = request.files['thumbnail']
        
        if thumbnail:
            filename = secure_filename(thumbnail.filename)
            thumbnail.save(os.path.join(current_app.config['UPLOAD_folder'], filename))
            thumbnail_url = url_for('static', filename=f'uploads/{filename}')
        else:
            thumbnail_url = ''
        new_episode = Episode(id=str(uuid.uuid4()), name=name, number=number, url=url, description=description, thumbnail_url=thumbnail_url, season_id=season.id)
        db.session.add(new_episode)
        db.session.commit()
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('add_episode.html', show=show, season=season)

@bp.route('/admin/show/<string:show_id>/edit_description', methods=['GET', 'POST'])
@login_required
def edit_show_description(show_id):
    show = Show.query.get_or_404(show_id)
    if request.method == 'POST':
        show.description = request.form.get('description')
        db.session.commit()
        flash('Show description updated successfully', 'success')
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('edit_show_description.html', show=show)


@bp.route('/admin/episode/<string:episode_id>/edit_number', methods=['GET', 'POST'])
@login_required
def edit_episode_number(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    if request.method == 'POST':
        episode.number = request.form.get('number')
        db.session.commit()
        flash('Episode number updated successfully', 'success')
        return redirect(url_for('admin.manage_show', show_id=episode.season.show_id))
    return render_template('edit_episode_number.html', episode=episode)


@bp.route('/show/<string:show_id>/edit_poster', methods=['GET', 'POST'])
@login_required
def edit_show_poster(show_id):
    show = Show.query.get_or_404(show_id)
    if request.method == 'POST':
        if 'poster' in request.files:
            file = request.files['poster']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                show.poster_url = url_for('static', filename=f'uploads/{filename}')
                db.session.commit()
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('edit_show_poster.html', show=show)

@bp.route('/show/<string:show_id>/delete', methods=['POST'])
@login_required
def delete_show(show_id):
    show = Show.query.get_or_404(show_id)
    
    # Delete associated seasons first
    Season.query.filter_by(show_id=show_id).delete()
    
    # Now delete the show
    db.session.delete(show)
    db.session.commit()
    flash('Show and all associated seasons deleted successfully', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@bp.route('/season/<string:season_id>/delete', methods=['POST'])
@login_required
def delete_season(season_id):
    season = Season.query.get_or_404(season_id)
    show_id = season.show_id
    db.session.delete(season)
    db.session.commit()
    flash('Season and all associated episodes deleted successfully', 'success')
    return redirect(url_for('admin.manage_show', show_id=show_id))

@bp.route('/episode/<string:episode_id>/edit_thumbnail', methods=['GET', 'POST'])
@login_required
def edit_episode_thumbnail(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    if request.method == 'POST':
        if 'update_url' in request.form:
            json_url = f"https://tlmastercontrol.teleosmedia.com/backend/media/usingid/{episode_id}"
            response = requests.get(json_url)
            if response.status_code == 200:
                data = response.json()
                episode.thumbnail_url = data['poster']
                db.session.commit()
                flash('Thumbnail URL updated successfully', 'success')
            else:
                flash('Failed to update thumbnail URL', 'error')
        elif 'upload_file' in request.form and 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                save_file(file, current_app.config['UPLOAD_FOLDER'])
                episode.thumbnail_url = url_for('static', filename=f'uploads/{filename}')
                db.session.commit()
                flash('Thumbnail file uploaded successfully', 'success')
        return redirect(url_for('admin.manage_show', show_id=episode.season.show_id))
    return render_template('edit_episode_thumbnail.html', episode=episode)

@bp.route('/episode/<string:episode_id>/delete', methods=['POST'])
@login_required
def delete_episode(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    show_id = episode.season.show_id
    db.session.delete(episode)
    db.session.commit()
    flash('Episode deleted successfully', 'success')
    return redirect(url_for('admin.manage_show', show_id=show_id))

@bp.route('/admin/database/<table_name>')
@login_required
def view_table(table_name):
    table = db.metadata.tables[table_name]
    columns = [column.name for column in table.columns]
    records = db.session.query(table).all()
    return render_template('view_table.html', table_name=table_name, columns=columns, records=records)

@bp.route('/admin/database/<table_name>/<string:record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(table_name, record_id):
    table = db.metadata.tables.get(table_name)
    if table is None:
        flash(f'Table {table_name} does not exist.', 'danger')
        return redirect(url_for('admin.admin_database'))

    model_class = None
    if table_name == 'show':
        model_class = Show
    elif table_name == 'season':
        model_class = Season
    elif table_name == 'episode':
        model_class = Episode
    else:
        flash(f'Unsupported table: {table_name}', 'danger')
        return redirect(url_for('admin.admin_database'))

    record = model_class.query.get(record_id)
    if record is None:
        flash(f'Record with ID {record_id} does not exist in table {table_name}.', 'danger')
        return redirect(url_for('admin.view_table', table_name=table_name))

    if request.method == 'POST':
        for column in table.columns:
            if column.name in request.form:
                setattr(record, column.name, request.form[column.name])
        db.session.commit()
        flash(f'Record updated successfully.', 'success')
        return redirect(url_for('admin.view_table', table_name=table_name))

    return render_template('edit_record.html', table_name=table_name, record=record, columns=table.columns)

@bp.route('/admin/show/<string:show_id>/add_episodes_bulk', methods=['GET', 'POST'])
@login_required
def add_episodes_bulk(show_id):
    show = Show.query.get_or_404(show_id)
    if request.method == 'POST':
        episode_links = request.form.get('episode_links')
        season_id = request.form.get('season_id')
        season = Season.query.get_or_404(season_id)

        logging.debug(f"Received episode links: {episode_links}")
        logging.debug(f"Season ID: {season_id}")

        guid_pattern = r'jltv/([0-9a-f-]+)/playlist\.m3u8'
        episode_ids = re.findall(guid_pattern, episode_links)
        
        logging.debug(f"Extracted episode IDs: {episode_ids}")

        try:
            episodes_data = fetch_episode_data(episode_ids)
            logging.debug(f"Fetched episodes data: {episodes_data}")

            episodes_to_add = []
            for episode_data in episodes_data:
                episode_number = extract_episode_number(episode_data['keywords'])
                logging.debug(f"Extracted episode number: {episode_number} for episode {episode_data['id']}")
                if episode_number is not None:
                    episode_data['number'] = episode_number
                    episodes_to_add.append(episode_data)

            episodes_to_add.sort(key=lambda x: x['number'])
            logging.debug(f"Sorted episodes to add: {episodes_to_add}")

            for episode_data in episodes_to_add:
                existing_episode = Episode.query.get(episode_data['id'])
                if existing_episode:
                    logging.debug(f"Updating existing episode: {existing_episode.id}")
                    for key, value in episode_data.items():
                        setattr(existing_episode, key, value)
                    existing_episode.season_id = season.id
                else:
                    logging.debug(f"Adding new episode: {episode_data['id']}")
                    new_episode = Episode(
                        id=episode_data['id'],
                        name=episode_data['name'],
                        number=episode_data['number'],
                        url=episode_data['url'],
                        description=episode_data['description'],
                        short_description=episode_data['short_description'],
                        keywords=episode_data['keywords'],
                        category=episode_data['category'],
                        thumbnail_url=episode_data['thumbnail_url'],
                        season_id=season.id
                    )
                    db.session.add(new_episode)
            
            db.session.commit()
            logging.debug("All episodes added or updated successfully")
            flash('Episodes added or updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding episodes: {str(e)}")
            flash(f'Error adding episodes: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('add_episodes_bulk.html', show=show)

@bp.route('/show/<string:show_id>/update_all', methods=['POST'])
@login_required
def update_all_episodes(show_id):
    show = Show.query.get_or_404(show_id)
    for season in show.seasons:
        logging.info(f"Updating episodes for season {season.id}")
        existing_episodes = {episode.id: episode for episode in season.episodes}
        updated_episodes = []
        
        for episode_id, episode in existing_episodes.items():
            json_url = f"https://tlmastercontrol.teleosmedia.com/backend/media/usingid/{episode_id}"
            response = requests.get(json_url)
            if response.status_code == 200:
                data = response.json()
                episode_number = extract_episode_number(data['keywords'])
                episode.number = episode_number if episode_number is not None else episode.number
                episode.name = data['title']
                episode.description = data['metaData']['description']
                episode.short_description = data['metaData']['shortDescription']
                episode.keywords = ', '.join([keyword['keyword'] for keyword in data['keywords']])
                episode.category = data['metaData']['iabCategory']['description']
                episode.thumbnail_url = data['poster']
                updated_episodes.append(episode)
            else:
                logging.warning(f"Failed to fetch data for episode {episode_id}. Keeping existing data.")
                updated_episodes.append(episode)

        updated_episodes.sort(key=lambda x: x.number if x.number is not None else float('inf'))

        for index, episode in enumerate(updated_episodes):
            episode.order = index + 1

        season.episodes = updated_episodes

    db.session.commit()
    logging.info(f"Updated {len(updated_episodes)} episodes for show {show_id}")
    flash('All episodes updated and sorted successfully', 'success')
    return redirect(url_for('admin.manage_show', show_id=show_id))

def extract_episode_number(keywords):
    if isinstance(keywords, str):
        match = re.search(r'episode_number:\s*(\d+)', keywords)
    else:
        keywords_str = ', '.join([keyword['keyword'] for keyword in keywords])
        match = re.search(r'episode_number:\s*(\d+)', keywords_str)
    
    if match:
        return int(match.group(1))
    return None

@bp.route('/admin/update_all_content', methods=['POST'])
@login_required
def update_all_content():
    logging.info("Starting update_all_content() for shows and seasons")

    # Fetch all series
    series_data = series(None)
    logging.info(f"Series data received: {series_data}")
    
    if series_data:
        for series_item in series_data:
            logging.info(f"Processing series: {series_item['id']}")
            show = Show.query.get(series_item['id'])
            if not show:
                show = Show(id=series_item['id'])
            
            show.name = series_item['title']
            show.description = series_item['metaData']['description']
            show.short_description = series_item['metaData']['shortDescription']
            show.poster_url = series_item['origins'][0]['url'] if series_item['origins'] else None
            show.created_at = datetime.fromisoformat(series_item['createdAt'].rstrip('Z'))
            show.iab_category = series_item['metaData']['iabCategory']['description']
            db.session.add(show)
        db.session.commit()
        logging.info("Shows updated successfully")
    else:
        logging.warning("No series data available")
        flash('No series data available', 'warning')
    
    # Fetch all seasons
    seasons_data = seasons(None)
    logging.info(f"Seasons data received: {seasons_data}")
    
    if seasons_data:
        for season_item in seasons_data:
            logging.info(f"Processing season: {season_item['id']}")
            season = Season.query.get(season_item['id'])
            if not season:
                season = Season(id=season_item['id'])
            
            season.title = season_item['title']
            season.created_at = datetime.fromisoformat(season_item['createdAt'].rstrip('Z'))
            season.show_id = season_item['parentId']
            
            # Extract season number
            season_match = re.search(r'Season (\d+)', season_item['title'])
            if season_match:
                season.number = int(season_match.group(1))
            else:
                season.number = None
            
            db.session.add(season)
        db.session.commit()
        logging.info("Seasons updated successfully")
    else:
        logging.warning("No seasons data available")
        flash('No seasons data available', 'warning')

    logging.info("Shows and seasons update completed")
    flash('Shows and seasons updated successfully', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@bp.route('/show/<string:show_id>/edit_logo', methods=['GET', 'POST'])
@login_required
def edit_show_logo(show_id):
    show = Show.query.get_or_404(show_id)
    if request.method == 'POST':
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                show.logo_url = url_for('static', filename=f'uploads/{filename}')
                db.session.commit()
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('edit_show_logo.html', show=show)

@bp.route('/show/<string:show_id>/update_theme_color', methods=['POST'])
@login_required
def update_theme_color(show_id):
    show = Show.query.get_or_404(show_id)
    theme_color = request.form.get('theme_color_hex')
    if theme_color and re.match(r'^#[0-9A-Fa-f]{6}$', theme_color):
        show.theme_color = theme_color
        db.session.commit()
        flash('Theme color updated successfully', 'success')
    else:
        flash('Invalid color format. Please use a valid hex color code.', 'error')
    return redirect(url_for('admin.manage_show', show_id=show.id))

@bp.route('/show/<string:show_id>/edit_banner', methods=['GET', 'POST'])
@login_required
def edit_show_banner(show_id):
    show = Show.query.get_or_404(show_id)
    if request.method == 'POST':
        if 'banner' in request.files:
            file = request.files['banner']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                show.banner_poster_url = url_for('static', filename=f'uploads/{filename}')
                db.session.commit()
        return redirect(url_for('admin.manage_show', show_id=show.id))
    return render_template('edit_show_banner.html', show=show)

@bp.route('/show/<string:show_id>/update_airtime', methods=['POST'])
@login_required
def update_airtime(show_id):
    show = Show.query.get_or_404(show_id)
    air_day = request.form.get('air_day')
    air_time_et = request.form.get('air_time_et')
    air_time_pt = request.form.get('air_time_pt')
    
    if air_day and air_time_et and air_time_pt:
        air_time = f"{air_day} {air_time_et} ET / {air_time_pt} PT"
        show.air_time = air_time
        db.session.commit()
        flash('Air time updated successfully', 'success')
    else:
        flash('Invalid air time format. Please fill all fields.', 'error')
    return redirect(url_for('admin.manage_show', show_id=show.id))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
