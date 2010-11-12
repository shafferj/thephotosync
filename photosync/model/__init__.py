"""The application's model objects"""
from __future__ import absolute_import

import datetime
import uuid

from pylons import session

from sqlalchemy import desc, orm, Column, String, Unicode,\
    UnicodeText, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relation, backref
from photosync.lazy import lazy
from photosync.model.meta import Session, Base
from photosync.model.json import Json
from photosync.model.settings import UserSetting

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)


class User(Base):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    fb_uid = Column('fb_uid', Integer, index=True)
    flickr_nsid = Column('flickr_nsid', String(100), index=True)
    flickr_token = Column('flickr_token', UnicodeText)
    fb_access_token = Column('fb_access_token', UnicodeText)

    def __init__(self, fb_uid=None, fb_access_token=None, flickr_nsid=None, flickr_token=None):
        self.fb_uid = fb_uid
        self.flickr_nsid = flickr_nsid
        self.fb_access_token = fb_access_token
        self.flickr_token = flickr_token

    def __unicode__(self):
        return u'%s' % self.id

    def __repr__(self):
        return "<User id=%s fb_uid=%s flickr_nsid=%s>" % (
            self.id, self.fb_uid, self.flickr_nsid)

    __str__ = __unicode__

    @staticmethod
    def get_by_id(id):
        return Session.query(User).filter_by(id=id).first()

    @staticmethod
    def get_current_user():
        if 'user_id' in session:
            return User.get_by_id(session.get('user_id'))


class AsyncTask(Base):
    __tablename__ = 'async_task'

    id = Column('id', Integer, primary_key=True)
    queue_id = Column('gearman_unique', String(100), index=True)
    total_units = Column('total_units', Integer)
    completed_units = Column('completed_units', Integer)
    start_time = Column('start_time', DateTime)
    end_time = Column('end_time', DateTime)
    last_update_time = Column('last_update_time', DateTime)
    status_code = Column('status_code', Integer)
    status_data = Column('status_data', Json)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    user = relation('User', backref=backref('async_tasks', order_by=last_update_time))

    def __init__(self):
        self.user_id = session.get('user_id')

    def set_status(self, completed, total, data, worker=None, job=None):
        self.completed_units = completed
        self.total_units = total
        self.status_data = data
        self.last_update_time = datetime.datetime.now()
        if not self.start_time:
            self.start_time = self.last_update_time
        if self.completed_units >= self.total_units:
            self.end_time = self.last_update_time

    @property
    def percentComplete(self):
        if self.completed_units is not None and self.total_units:
            return 100.0*self.completed_units/self.total_units

    @lazy
    def _beanstalk_connection(self):
        return 

    def __unicode__(self):
        return u"%s/%s %s: %r (%r)" % (
            self.completed_units, self.total_units,
            self.status_code, self.status_data)

    __str__ = __unicode__


    @staticmethod
    def get_for_user(user_id=None, limit=3):
        if not user_id:
            user_id = session.get('user_id')
        return Session.query(AsyncTask)\
            .filter(AsyncTask.user_id==user_id)\
            .order_by(desc('last_update_time'))\
            .limit(limit)


class SyncRecord(Base):
    __tablename__ = 'sync_records'

    TYPE_ALBUM = 1
    TYPE_PHOTO = 2

    STATUS_SUCCESS = 0
    STATUS_FAILED = 1
    STATUS_RUNNING = 2

    id = Column('id', Integer, primary_key=True)
    fbid = Column('fbid', Integer, index=True)
    flickrid = Column('flickrid', Integer, index=True)
    timestamp = Column('timestamp', DateTime)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    status = Column('status', Integer)
    type = Column('type', Integer, index=True)
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
