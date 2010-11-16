"""The application's model objects"""
from __future__ import absolute_import

import datetime

from pylons import session

from sqlalchemy import (desc, Column, String, UnicodeText, Integer,
                        ForeignKey, DateTime)
from sqlalchemy.dialects.mysql.base import BIGINT
from sqlalchemy.orm import relation, backref
from photosync.model.meta import Session, Base
from photosync.model.json import Json
from photosync.worker import job


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
    queue_id = Column('queue_id', Integer, index=True)
    type = Column('type', String(100), index=True)
    total_units = Column('total_units', Integer)
    completed_units = Column('completed_units', Integer)
    created_time = Column('created_time', DateTime)
    start_time = Column('start_time', DateTime)
    end_time = Column('end_time', DateTime)
    last_update_time = Column('last_update_time', DateTime)
    status_code = Column('status_code', Integer, index=True)
    status_data = Column('status_data', Json)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    user = relation('User', backref=backref('async_tasks', order_by=last_update_time))

    def __init__(self, user_id=None, type=None):
        user_id = user_id or session.get('user_id')
        if not user_id:
            raise ValueError("Cannot create async task without a user id")
        self.user_id = user_id
        self.type = type
        self.created_time = datetime.datetime.now()

    def set_status(self, completed, total, data):
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

    @property
    def is_completed(self):
        return not self._job

    @property
    def is_buried(self):
        return self._job and self._job.stats['state'] == job.STATE_BURIED

    __job = "SENTINAL"

    @property
    def _job(self):
        if self.__job == "SENTINAL":
            self.__job = job.from_id(self.queue_id)
        return self.__job

    @property
    def time_left(self):
        # 120 is magical TTR time in beanstalk. time left is
        # set to TTR when the task is being processed.
        if self._job and self._job.stats['time-left'] > 120:
            return self._job.stats['time-left']

    def run_now(self):
        self.queue_id = None
        Session.commit()
        self.queue_id = self._job.resubmit()
        self.__job = "SENTINAL"
        Session.commit()

    def __unicode__(self):
        return u"%s/%s %s: %r (%r)" % (
            self.completed_units, self.total_units,
            self.status_code, self.status_data)

    __str__ = __unicode__


    @staticmethod
    def get_for_user(user_id=None, limit=3, type=None):
        if not user_id:
            user_id = session.get('user_id')

        query = Session.query(AsyncTask)\
            .filter(AsyncTask.user_id==user_id)

        if type:
            query = query.filter(AsyncTask.type==type)

        query = query.order_by(desc('created_time'))\
            .limit(limit)

        return query


class SyncRecord(Base):
    __tablename__ = 'sync_records'

    TYPE_ALBUM = 1
    TYPE_PHOTO = 2

    STATUS_SUCCESS = 0
    STATUS_FAILED = 1

    id = Column('id', Integer, primary_key=True)
    fbid = Column('fbid', BIGINT, index=True)
    flickrid = Column('flickrid', String(100), index=True)
    timestamp = Column('timestamp', DateTime)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    status = Column('status', Integer)
    type = Column('type', Integer, index=True)
    user = relation('User', backref=backref('sync_records', order_by=timestamp))

    def __init__(self, type, user_id=None):
        user_id = user_id or session.get('user_id')
        if not user_id:
            raise ValueError("Must provide a user_id")
        self.type = type
        self.user_id = user_id
        self.timestamp = datetime.datetime.now()

    @property
    def success(self):
        return self.status == SyncRecord.STATUS_SUCCESS

    @property
    def failed(self):
        return self.status == SyncRecord.STATUS_FAILED

    @staticmethod
    def get_for_flickrid(flickrid=None, limit=3, type=None):
        query = Session.query(SyncRecord)\
            .filter(SyncRecord.flickrid==flickrid)

        if type:
            query = query.filter(SyncRecord.type==type)

        query = query.order_by(desc('timestamp'))\
            .limit(limit)

        return query
