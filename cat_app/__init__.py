from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from music_db_setup import Base, Playlist, Song, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('/var/www/cat_app/cat_app/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Custom Playlists"


# Connect to Database and create database session
#engine = create_engine('sqlite:///playlists.db')
engine = create_engine('postgresql://catalog:Tisbury@localhost/catalog')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Helper Functions

# Add user by authentication data
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

# Return user info - look up in User table by id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Return user ID, look up by email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None



# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Gconnect function - get user credentials & info from google auth
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('/var/www/cat_app/cat_app/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session

# disconnect if user logged in via google authentication
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# user credentials from facebook
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('/var/www/cat_app/cat_app/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('/var/www/cat_app/cat_app/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output

# disconnect a Facebook-authenticated user
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            credentials = login_session.get('credentials')
            del credentials
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showPlaylists'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showPlaylists'))

# JSON API to view all playlists
@app.route('/playlist/JSON')
def playlistsJSON():
    playlists = session.query(Playlist).all()
    return jsonify(playlists=[p.serialize for p in playlists])

# JSON API to view songs in a playlist
@app.route('/playlist/<int:playlist_id>/songs_in_playlist/JSON')
def playlistSongsJSON(playlist_id):
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    items = session.query(Song).filter_by(
        playlist_id=playlist_id).all()
    return jsonify(Songs=[i.serialize for i in items])

# JSON API to view all songs
@app.route('/playlist/all_songs/JSON')
def allSongsJSON():
    songs = session.query(Song).all()
    return jsonify(songs=[s.serialize for s in songs])


# Show all playlists
@app.route('/')
@app.route('/playlist/')
def showPlaylists():
    playlists = session.query(Playlist,User).filter(Playlist.user_id == User.id).order_by(Playlist.id.desc())
    songs = session.query(Song,Playlist,User).filter(Song.playlist_id == Playlist.id, Song.user_id == User.id).order_by(Song.id.desc()).limit(2)
    if 'username' not in login_session:
        return render_template('public_playlists.html', playlists=playlists, items = songs)
        #for song in songs:
    else:
        return render_template('playlist.html', playlists=playlists, items = songs)

# Add a playlist if logged in. If user filled out form, create a new playlist with form data
@app.route('/playlist/new/', methods=['GET', 'POST'])
def newPlaylist():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newPlaylist = Playlist(title=request.form['title'], description=request.form['description'], user_id=login_session['user_id'])
        session.add(newPlaylist)
        flash('New Playlist %s Successfully Created' % newPlaylist.title)
        session.commit()
        return redirect(url_for('newSong', playlist_id = newPlaylist.id))
    else:
        return render_template('new_playlist.html')

# See all the songs in a playlist
@app.route('/playlist/<int:playlist_id>/')
@app.route('/playlist/<int:playlist_id>/songs/')
def showSongs(playlist_id):
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    creator = getUserInfo(playlist.user_id)
    items = session.query(Song).filter_by(
        playlist_id=playlist_id).all()
    # if user is not logged in, give them a page without CRUD links
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('public_list_of_songs.html', items=items, playlist=playlist, creator=creator)
    else:
        return render_template('list_of_songs.html', items=items, playlist=playlist, creator=creator)

# Edit a playlist if logged in and owner of playlist
@app.route('/playlist/<int:playlist_id>/edit/', methods=['GET', 'POST'])
def editPlaylist(playlist_id):
    editedPlaylist = session.query(
        Playlist).filter_by(id=playlist_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedPlaylist.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this restaurant. Please create your own restaurant in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['title']:
            editedPlaylist.title = request.form['title']
            editedPlaylist.description = request.form['description']
            session.commit()
            flash('Playlist Successfully Edited %s' % editedPlaylist.title)
            return redirect(url_for('showPlaylists'))
    else:
        return render_template('edit_playlist.html', playlist=editedPlaylist)

# Create a new song if logged in
@app.route('/playlist/<int:playlist_id>/song/new/', methods=['GET', 'POST'])
def newSong(playlist_id):
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['user_id'] != playlist.user_id:
        return "<script>function myFunction() {alert('You are not authorized to add menu items to this restaurant. Please create your own restaurant in order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newSong = Song(title=request.form['title'], performed_by=request.form['performed_by'], album=request.form[
                               'album'], notes=request.form['notes'], playlist_id=playlist_id, user_id=playlist.user_id)
        session.add(newSong)
        session.commit()
        flash('New Song %s Item Successfully Created' % (newSong.title))
        return redirect(url_for('showSongs', playlist_id = playlist.id))
    else:
        return render_template('new_song.html', playlist = playlist)

# Delete a playlist
@app.route('/playlist/<int:playlist_id>/delete/', methods=['GET', 'POST'])
def deletePlaylist(playlist_id):
    playlistToDelete = session.query(
        Playlist).filter_by(id=playlist_id).one()
    songsToDelete = session.query(Song).filter_by(playlist_id = playlist_id).all()
    if 'username' not in login_session:
        return redirect('/login')
    if playlistToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this playlist. Please create your own playlist in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(playlistToDelete)
        flash('%s Successfully Deleted' % playlistToDelete.title)
        session.commit()
        return redirect(url_for('showPlaylists', playlist_id=playlist_id))
    else:
        return render_template('delete_playlist.html', playlist=playlistToDelete)

# Edit song if you are a owner
@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/edit', methods=['GET', 'POST'])
def editSong(playlist_id, song_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedSong = session.query(Song).filter_by(id=song_id).one()
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    if login_session['user_id'] != playlist.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit songs in this playlist. Please create your own playlists.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['title']:
            editedSong.title = request.form['title']
        if request.form['performed_by']:
            editedSong.performed_by = request.form['performed_by']
        if request.form['album']:
            editedSong.album = request.form['album']
        if request.form['notes']:
            editedSong.notes = request.form['notes']
        session.add(editedSong)
        session.commit()
        flash('Song Successfully Edited')
        return redirect(url_for('showSongs', playlist_id=playlist_id))
    else:
        return render_template('edit_song.html', playlist_id=playlist_id, song_id=song_id, item=editedSong)

# Delete a song
@app.route('/playlist/<int:playlist_id>/song/<int:song_id>/delete', methods=['GET', 'POST'])
def deleteSong(playlist_id, song_id):
    if 'username' not in login_session:
        return redirect('/login')
    playlist = session.query(Playlist).filter_by(id=playlist_id).one()
    songToDelete = session.query(Song).filter_by(id=song_id).one()
    if login_session['user_id'] != songToDelete.user_id:
        return "<script>function myFunction() {alert('You are not authorized to delete songs in this playlist.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(songToDelete)
        session.commit()
        flash('Song Successfully Deleted')
        return redirect(url_for('showSongs', playlist_id=playlist_id))
    else:
        return render_template('delete_song.html', item=songToDelete, playlist_id = playlist_id)
 

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
