"""The application's model objects"""
import json
import datetime

from pylons import session

from sqlalchemy import orm, Column, Unicode, UnicodeText, Integer, ForeignKey, Date
from sqlalchemy.orm import relation, backref
from sqlalchemy import types
from photosync.model.meta import Session, Base


def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)


class Json(types.TypeDecorator, types.MutableType):

    impl=types.Text

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        else:
            return json.loads(value)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        else:
            return json.dumps(value)


class User(Base):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    fb_uid = Column('fb_uid', Integer)
    flickr_nsid = Column('flickr_nsid', UnicodeText)
#    fb_access_token = Column('fb_access_token', UnicodeText)

    def __init__(self, fb_uid=None, flickr_nsid=None):
        self.fb_uid = fb_uid
        self.flickr_nsid = flickr_nsid

    def __unicode__(self):
        return u'%s' % self.id

    def __repr__(self):
        return "<User id=%s fb_uid=%s flickr_nsid=%s>" % (
            self.id, self.fb_uid, self.flickr_nsid)

    __str__ = __unicode__


class SyncRecord(Base):
    __tablename__ = 'sync_records'

    TYPE_ALBUM = 1
    TYPE_PHOTO = 2

    STATUS_SUCCESS = 0
    STATUS_FAILED = 1
    STATUS_RUNNING = 2

    id = Column('id', Integer, primary_key=True)
    fbid = Column('fbid', Integer)
    flickrid = Column('flickrid', Integer)
    timestamp = Column('timestamp', Date)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    status = Column('status', Integer)
    type = Column('type', Integer)
    user = relation('User', backref=backref('sync_records', order_by=timestamp))

    def __init__(self, type):
        self.type = type
        self.user_id = session.get('user_id')
        self.timestamp = datetime.datetime.now()
        self.status = SyncRecord.STATUS_RUNNING

    @property
    def success(self):
        return self.status == SyncRecord.STATUS_SUCCESS

    @property
    def failed(self):
        return self.status == SyncRecord.STATUS_FAILED

    @property
    def running(self):
        return self.status == SyncRecord.STATUS_RUNNING


class Album(Base):
    __tablename__ = 'albums'
    id = Column('id', Integer, primary_key=True)
    owner = Column('owner', Integer)
    fbid = Column('fnid', Integer)
    fbdata = Column('fbdata', Json)

    def __repr__(self):
        return "<Album id=%s owner=%s fbid=%s>" % (
            self.id, self.owner, self.fbid)
