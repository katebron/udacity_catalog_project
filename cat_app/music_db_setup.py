from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import backref
 
Base = declarative_base()

class User(Base):
  __tablename__ = 'user'

  id = Column(Integer, primary_key=True)
  name = Column(String(250), nullable=False)
  email = Column(String(250), nullable=False)
  picture = Column(String(250))


class Playlist(Base):
    __tablename__ = 'playlist'
   
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    description = Column(String(250))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'title'         : self.title,
           'id'           : self.id,
           'description'  : self.description,
       }
 
class Song(Base):
    __tablename__ = 'song'


    title =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    notes = Column(String(250))
    performed_by = Column(String(16))
    album = Column(String(16))
    playlist_id = Column(Integer,ForeignKey('playlist.id'))
    playlist = relationship(Playlist, backref=backref("songs", cascade="all, delete-orphan"))
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'title'         : self.title,
           'notes'         : self.notes,
           'id'         : self.id,
           'performed_by'         : self.performed_by,
           'album'         : self.album,
       }



#engine = create_engine('sqlite:///playlists.db')
engine = create_engine('postgresql://catalog:Tisbury@localhost/catalog') 

Base.metadata.create_all(engine)
