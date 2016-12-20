from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from music_db_setup import Playlist, Base, Song, User

#engine = create_engine('sqlite:///playlists.db')
engine = create_engine('postgresql://catalog:Tisbury@localhost/catalog')

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Ronald Thump", email="dt_real_me@shoo.com",
             picture='http://img.ifcdn.com/images/c6b7f17490ba207fdfa8c92ac184b1fd347ecee0b72e3a12d9644f832e19d8c3_1.jpg')
session.add(User1)
session.commit()

playlist1 = Playlist(user_id=1, title="Monday Tunes", description="Songs for getting back to it")

session.add(playlist1)
session.commit()

song1 = Song(user_id=1, album="Cardinal Cross", performed_by="Mount Mariah", title="Skeptic Goodbye", notes="Matt S. likes", playlist=playlist1)


session.commit()

song2 = Song(user_id=1, album="Cardinal Cross", performed_by="Mount Mariah", title="How to Dance", notes="", playlist=playlist1)

song3 = Song(user_id=1, album="Early Recordings", performed_by="Waxahatchee", title="Clumsy", notes="", playlist=playlist1)



session.add(song1)
session.add(song2)
session.add(song3)
session.commit()

User2 = User(name="Coco", email="nola@me.com", picture="http://vignette3.wikia.nocookie.net/bobsburgerpedia/images/6/6e/Tina_render.png/revision/latest?cb=20130113192209")
session.add(User2)
session.commit()

playlist2 = Playlist(user_id=2, title="Friend karaoke", description="Y'all know this song")

session.add(playlist2)
session.commit()

song3 = Song(user_id=2, title="We belong", performed_by="Pat Benatar", album="Tropico", notes="Whatever you deny or convey...", playlist=playlist2)

song4 = Song(user_id=2, title="Bohemian Rhapsody", performed_by="Queen", album="A night at the opera", notes="How do i know these words", playlist=playlist2)

session.add(song3)
session.add(song4)
session.commit()

User3 = User(name="Elliot", email="somewhere@att.com", picture="https://s-media-cache-ak0.pinimg.com/736x/fd/c8/0b/fdc80bea8393a4421f61c6b5c1830949.jpg")
session.add(User3)
playlist3 = Playlist(user_id=3, title="To gnaw on", description="Grows on you")


song3 = Song(user_id=3, title="Joe Goes to School", performed_by="Car Sear Headrest", album="Teens of denial", notes="", playlist=playlist3)

song4 = Song(user_id=3, title="Strange Torpedo", performed_by="Lucy Dacus", album="No Burden", notes="Keep thinking it's Torres", playlist=playlist3)


session.add(playlist2)
session.commit()
session.add(song3)
session.add(song4)
session.commit()

song3 = Song(user_id=2, title="We belong", performed_by="Pat Benatar", album="Tropico", notes="Whatever you deny or convey...", playlist=playlist2)

song4 = Song(user_id=2, title="Bohemian Rhapsody", performed_by="Queen", album="A night at the opera", notes="Some how i know the words", playlist=playlist2)

session.add(song3)
session.add(song4)
session.commit()

print "added songs"
