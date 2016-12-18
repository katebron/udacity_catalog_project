Custom Playlists 
======================

This program allows users to create custom playlists: create a topic for a playlist, and then add song information to it. The playlists are publically available (including via an API), but a user can only edit and delete their own. Users need to log in (see authentication below) if they wish to create a playlist.

INSTALL
-------------------------
To use, run python to install 

```sh
python project.py
``` 

If you would like to pre-populate the catalog with playlists and songs, run 
```sh
python load_playlists.py
``` 



AUTHENTICATION
------------------------
Users can log in via Google or Facebook. A log in form for each is provided within the application itself. This information will not be posted to your Google or Facebook accounts.
