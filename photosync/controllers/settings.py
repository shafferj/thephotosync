import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync import fb
from photosync.model.settings import UserSetting, UserSettingConst
from photosync.model.meta import Session
log = logging.getLogger(__name__)

class SettingsController(BaseController):

    def save(self):
        privacy = request.POST.getone('fb_privacy')
        if privacy in dict(self.get_privacy_options()):
            UserSetting.set(UserSettingConst.FB_PRIVACY, privacy)
        redirect(url('settings'))

    def index(self):
        settings = UserSetting.multiget(settings=[UserSettingConst.FB_PRIVACY])
        c.fb_privacy_setting = settings.get(UserSettingConst.FB_PRIVACY, 'FB_DEFAULT')
        c.fb_privacy_options = fb.get_privacy_options()
        return render('/settings.mako')
