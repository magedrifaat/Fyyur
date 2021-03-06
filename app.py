#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for,
    abort
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate;

from datetime import datetime
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# TODO DONE: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  data = []
  all_venues = Venue.query.order_by('city').all()
  # Assumes all venues have a city
  current_city = None
  for venue in all_venues:
    # for a new city, append a new dictionary to write in
    if venue.city != current_city:
      data.append({
        "city": venue.city,
        "state": venue.state,
        "venues": []
      })
      current_city = venue.city
    
    upcoming_shows = [show for show in venue.shows if show.show_time > datetime.now()]
    data[-1]["venues"].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(venue.shows)
    })
     
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  matches = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response={
    "count": len(matches),
    "data": [{
      "id": match.id,
      "name": match.name,
      "num_upcoming_shows": len([show for show in match.shows if show.show_time > datetime.now()]),
    } for match in matches]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO DONE: replace with real venue data from the venues table, using venue_id
  
  venue = Venue.query.get(venue_id)
  if venue:
    past_shows = [show for show in venue.shows if show.show_time < datetime.now()]
    upcoming_shows = [show for show in venue.shows if show.show_time > datetime.now()]
    data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres.split(","),
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "image_link": venue.image_link,
      "past_shows": [{
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.show_time)
      } for show in past_shows],
      "upcoming_shows": [{
        "artist_id": show.artist.id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.show_time)
      } for show in upcoming_shows],
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
    if venue.seeking_talent:
      data["seeking_description"] = venue.seeking_description
    
    return render_template('pages/show_venue.html', venue=data)
  else:
    abort(404)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO DONE: insert form data as a new Venue record in the db, instead
  # TODO DONE: modify data to be the data object returned from db insertion
  
  # Reinstantiate a form with the request data to validate, disable csrf to prevent csrf validation error.
  form = VenueForm(request.form, csrf_enabled=False)
  if not form.validate_on_submit():
    return render_template('forms/new_venue.html', form=form)
  
  error = False
  data = {}
  try:
    venue = Venue(name = request.form.get('name', ''), 
                    city = request.form.get('city', ''),
                    state = request.form['state'],
                    address = request.form['address'],
                    phone = request.form['phone'],
                    facebook_link = request.form['facebook_link'],
                    genres = ",".join(request.form.getlist('genres')))
    db.session.add(venue)
    db.session.commit()
    data['name'] = venue.name
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if error:
    # TODO DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.', 'error')
  else:
    # on successful db insert, flash success
    flash('Venue ' + data['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO DONE: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = [{
    "id": artist.id,
    "name": artist.name
  } for artist in artists]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  matches = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response={
    "count": len(matches),
    "data": [{
      "id": match.id,
      "name": match.name,
      "num_upcoming_shows": len([show for show in match.shows if show.show_time > datetime.now()]),
    } for match in matches]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO DONE: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  if artist:
    past_shows = [show for show in artist.shows if show.show_time < datetime.now()]
    upcoming_shows = [show for show in artist.shows if show.show_time > datetime.now()]
      
    data={
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres.split(','),
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "image_link": artist.image_link,
      "past_shows": [{
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.show_time)
      } for show in past_shows],
      "upcoming_shows": [{
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.show_time)
      } for show in upcoming_shows],
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }
    if artist.seeking_venue:
      data["seeking_description"] = artist.seeking_description
    return render_template('pages/show_artist.html', artist=data)
  else:
    abort(404)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO DONE: insert form data as a new Venue record in the db, instead
  # TODO DONE: modify data to be the data object returned from db insertion

  # Reinstantiate a form with the request data to validate, disable csrf to prevent csrf validation error.
  form = ArtistForm(request.form, csrf_enabled=False)
  if not form.validate_on_submit():
    return render_template('forms/new_artist.html', form=form)
  
  error = False
  data = {}
  try:
    artist = Artist(name = request.form.get('name', ''), 
                    city = request.form.get('city', ''),
                    state = request.form['state'],
                    phone = request.form['phone'],
                    facebook_link = request.form['facebook_link'],
                    genres = ",".join(request.form.getlist('genres')))
    db.session.add(artist)
    db.session.commit()
    data['name'] = artist.name
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if error:
    # TODO DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.', 'error')
  else:
    # on successful db insert, flash success
    flash('Artist ' + data['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "artist_id": show.artist_id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": str(show.show_time)
  } for show in Show.query.all()]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO DONE: insert form data as a new Show record in the db, instead

  # Reinstantiate a form with the request data to validate, disable csrf to prevent csrf validation error.
  form = ShowForm(request.form, csrf_enabled=False)
  if not form.validate_on_submit():
    return render_template('forms/new_show.html', form=form)
  
  error = False
  try:
    show = Show(artist_id = request.form['artist_id'],
                venue_id = request.form['venue_id'],
                show_time = request.form['start_time'])
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  if error:
    # TODO DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.', 'error')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
