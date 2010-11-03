"""The application's model objects"""
import json
import datetime
import uuid

from pylons import session

from gearman.client import GearmanClient

from sqlalchemy import orm, Column, String, Unicode, UnicodeText, Integer, ForeignKey, Date
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


class AsyncTask(Base):
    __tablename__ = 'async_task'

    id = Column('id', Integer, primary_key=True)
    gearman_unique = Column('gearman_unique', String(100))
    gearman_data = Column('gearman_data', Json)
    total_units = Column('total_units', Integer)
    completed_units = Column('completed_units', Integer)
    start_time = Column('start_time', Date)
    end_time = Column('end_time', Date)
    last_update_time = Column('last_update_time', Date)
    status_code = Column('status_code', Integer)
    status_data = Column('status_data', Json)


    def __init__(self):
        self.gearman_unique = str(uuid.uuid4())

    def set_status(self, completed, total, data, worker=None, job=None):
        self.completed_units = completed
        self.total_units = total
        self.status_data = data
        self.last_update_time = datetime.datetime.now()
        if not self.start_time:
            self.start_time = self.last_update_time

    def submit_job(self, gearman_task, data, **kwargs):
        Session.add(self)
        Session.commit()
        client = GearmanClient(['localhost:4730'])
        request = client.submit_job(
            gearman_task,
            json.dumps(data),
            unique=str(self.gearman_unique),
            **kwargs)
        self.gearman_data = request.job.to_dict()
        Session.commit()
        return request

    @property
    def percentComplete(self):
        return 100.0*self.completed_units/self.total_units

    def __unicode__(self):
        return u"%s/%s %s: %r (%r)" % (
            self.completed_units, self.total_units,
            self.status_code, self.status_data,
            self.gearman_data)

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
