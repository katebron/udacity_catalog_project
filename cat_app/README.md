Configuring an Ubuntu and Hosting "Custom Playlists" 
======================

SERVER INFO
-------------------
Public IP address: 35.162.149.220
URL: [http://ec2-35-162-149-220.us-west-2.compute.amazonaws.com/](http://ec2-35-162-149-220.us-west-2.compute.amazonaws.com/")

INITIAL SERVER SET UP
-----------------------
Initially, log in as root by referring to my provided udacity key (saved to my local computer) - 
```ssh -i ~/.ssh/udacity_key.rsa root@35.162.149.220```


Set up a user called grader:
```sudo createuser grader```

On local machine, create a key pair to be able to SSH into remote server:
```ssh-keygen -t rsa```

Scp the file from local to remote
```scp -i udacity_key.rsa grader.pub root@35.162.149.220:~/grader.pub```

Move the file:
```mv ~/grader.pub ~/grader/.ssh/authorized_keys```
Chown the file to grader and make sure the permissions are 644

Give the grader sudo access:
Create a file for grader under /etc/sudoers.d, containing this:
```grader ALL=(ALL:ALL) ALL```

Update existing packages:
```sudo apt-get update
sudo apt-get upgrade
```

CHANGE DEFAULT 22 SSH PORT TO 2200
----------------
Edit /etc/ssh/sshd_config: change line at "What ports, IPs and protocols we listen for" from 22 to 2200

CONFIGURE THE FIREWALL (UFW)
------------------
Set general ground rules: 
```sudo ufw default deny incoming
sudo ufw default allow outgoing
```

Allow for essentials:
SSH:
```sudo ufw allow 2200```
Httpserver:
```sudo ufw allow www```

NTP (For date synchronization):
```sudo ufw allow ntp ```

Double check, then enable firewall:
```sudo ufw enable```

CONFIGURE TIMEZONE TO UTC
-------------------------
```sudo timedatectl set-timezone Etc/UTC```

INSTALL APACHE 
----------------
```sudo apt-get update
sudo apt-get install apache2```

CONFIGURE APACHE TO SERVE A PYTHON MOD_WSGI APP
---------------------------------------------
Install mod_wsgi, then enable it:
```sudo apt-get install libapache2-mod-wsgi python-dev
sudo a2enmod wsgi
```

INSTALL FLASK
----------------
```sudo apt-get install python-pip```
If error, may  have to:
```sudo pip install virtualenv 
sudo virtualenv venv
source venv/bin/activate 
sudo pip install Flask 
```

SET UP DIRECTORY FOR INCOMING FLASK APP
-------------------------------------
I'll be bringing in an existing app from a git repository, but first I set up a directory
at /var/www/cat_app, with a lower directory at cat_app/cat_app. I added a cat_app/cat_app/static
directory. The project.py file in the original project will become __init__.py

I created a cat_app.wsgi file in www/cat_app with:

```#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/cat_app")

from cat_app import app as application
application.secret_key = '...'
```
Set up a configuration file in /etc/apache2/sites-available (can copy
cp /etc/apache2/sites-available/000-default.conf for template):
```
<VirtualHost *:80>
	ServerName 35.162.149.220
	ServerAdmin katebron@gmail.com
        ServerAlias http://ec2-35-162-149-220.us-west-2.compute.amazonaws.com
	WSGIScriptAlias / /var/www/cat_app/cat_app.wsgi
	<Directory /var/www/cat_app/cat_app/>
		Order allow,deny
		Allow from all
	</Directory>
	#Alias /static /var/www/cat_app/cat_app/static
	#<Directory /var/www/cat_app/cat_app/static/>
	#	Order allow,deny
	#	Allow from all
	#</Directory>
	ErrorLog ${APACHE_LOG_DIR}/error.log
	LogLevel warn
	CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```
Enable the site:
```sudo a2ensite cat_app.conf```

Set up local host file:
Edit /etc/hosts, add:
```127.0.0.1 http://ec2-35-162-149-220.us-west-2.compute.amazonaws.com```

Make sure permissions on /var/www/cat_app are 755 
```sudo chmod -R 755 /var/www

Ownership to www-data (chown)



INSTALL AND CONFIGURE POSTGRESQL
--------------------------------
Install:
```sudo apt-get install postgresql postgresql-contrib```

Switch to PostgresSQL:
```sudo -i -u postgres```

Create user ("catalog"):
```createuser --interactive```

Disallow remote connections:
Edit /etc/postgresql/9.3/main/pg_hba.conf. Make sure only "local" rules are un-commented out.

MOVE CATALOG APP OVER
-----------------------
Install Git & create an ssh-key for GitHub. Clone the app to cat_app/cat_app. Edit 
project.py to be __init__.py and translate existing sqlite commands to postgesql.

In __init__.py, music_db_setup.py and load_playlist.py, change engine = create engine('sqlite... to 
```engine = create_engine('postgresql://catalog:password@localhost/catalog')```

MAKE SURE .git FILE IS NOT ACCESSIBLE FROM THE BROWSER
-----------------------------------------------------
Create an .htaccess file on the same level with:
```RedirectMatch 404 /\.git```

UPDATE AUTHENTICATION
--------------------
The existing app used oauth authentication with Google & Facebook, so I had to add the public URL to
the list of URLs on the security pages for those apps with the platform's respective dev dashboards.
I also had to install python-oauth2client.


COMMAND COMMANDS & TROUBLESHOOTING
---------------
Restart Apache: sudo service apache2 restart
See error logs:  sudo tail -20 /var/log/apache2/error.log


RESOURCES
------------
Set up Apache https://www.digitalocean.com/community/tutorials/how-to-set-up-apache-virtual-hosts-on-ubuntu-14-04-lts
Flask configuration http://flask.pocoo.org/docs/0.10/config/
Deploy Flask app on Ubuntu https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
Ubuntu help http://askubuntu.com/
PostgreSQL Installation & set up https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04
PostgreSQL Connection Rules https://www.postgresql.org/docs/9.1/static/auth-pg-hba-conf.html
Udacity Forums


ABOUT THE CATALOG APP
----------------------

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
