from pylons import session

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref
from sqlalchemy.schema import PrimaryKeyConstraint

from photosync.model.meta import Session, Base
from photosync.model.json import Json

class UserSetting(Base):
    __tablename__ = 'user_settings'
    __table_args__ = (
        PrimaryKeyConstraint('user_id','setting_id'),
        {}
        )

    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    setting_id = Column('setting_id', Integer)
    value = Column('value', Json)

    user = relation('User', backref=backref('settings'))

    def __init__(self, user_id, setting_id, value):
        self.user_id = user_id
        self.setting_id = setting_id
        self.value = value

    @staticmethod
    def get(user_id=None, setting=None):
        result = UserSetting.multiget(user_id=user_id, settings=[setting])
        return result.get(setting)

    @staticmethod
    def multiget(user_id=None, settings=None):
        user_id = user_id or session.get('user_id')
        query = Session.query(UserSetting).filter(UserSetting.user_id==user_id)
        if settings is not None:
            query = query.filter(UserSetting.setting_id.in_(settings))

        results = {}
        for result in query:
            results[result.setting_id] = result.value

        return results

    @staticmethod
    def set(setting_id, value, user_id=None):
        user_id = user_id or session.get('user_id')
        result = Session.merge(UserSetting(user_id, setting_id, value))
        Session.commit()
        return result


class UserSettingConst:
    FB_PRIVACY = 1
