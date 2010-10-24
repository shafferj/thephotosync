"""The application's model objects"""
from sqlalchemy import orm, Column, Unicode, UnicodeText, Integer
from photosync.model.meta import Session, Base


def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    Session.configure(bind=engine)


class User(Base):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    fb_uid = Column('fb_uid', Integer)
#    fb_access_token = Column('fb_access_token', UnicodeText)

    def __init__(self, fb_uid):
        self.fb_uid = fb_uid

    def __unicode__(self):
        return u'%s' % self.id

    def __repr__(self):
        return "<User id=%s fb_uid=%s>" % (self.id, self.fb_uid)

    __str__ = __unicode__
