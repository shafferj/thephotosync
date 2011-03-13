import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lazy import lazy
from photosync.lib.base import BaseController, render
from photosync.lib import helpers as h
from photosync import fb
from photosync.model.settings import UserSetting, UserSettingConst
from photosync.model import User
from photosync.model.meta import Session
from photosync import flickr

log = logging.getLogger(__name__)

class SettingsController(BaseController):

    @lazy
    def settings(self):
        return UserSetting.multiget(
            settings=[UserSettingConst.FB_PRIVACY,
                      UserSettingConst.FLICKR_SET_SYNCING])

    def save(self):
        privacy = request.POST.getone('fb_privacy')
        if privacy in dict(fb.get_privacy_options()):
            UserSetting.set(UserSettingConst.FB_PRIVACY, privacy)

        flickr_settings = self.settings.get(UserSettingConst.FLICKR_SET_SYNCING, {})
        flickr_settings['select_sets'] = bool(request.POST.get('select_sets'))
        flickr_settings['selected_sets'] = request.POST.getall('selected_sets')
        UserSetting.set(UserSettingConst.FLICKR_SET_SYNCING, flickr_settings)
        h.flash("Your settings have been updated.")
        redirect(url('index'))

    def index(self):
        c.has_fb_account = bool(self.logged_in_user.fb_uid)
        if c.has_fb_account:
            c.fb_privacy_setting = self.settings.get(
                UserSettingConst.FB_PRIVACY, 'FB_DEFAULT')
            c.fb_privacy_options = fb.get_privacy_options()
        else:
            c.fb_connect_url = fb.get_authorization_url()

        c.has_flickr_account = bool(self.logged_in_user.flickr_token)

        if c.has_flickr_account:
            flickr_settings = self.settings.get(UserSettingConst.FLICKR_SET_SYNCING, {})
            c.select_sets = flickr_settings.get('select_sets', False)
            selected_sets = flickr_settings.get('selected_sets', [])

            c.all_sets = []

            fk = flickr.FlickrAPI(self.logged_in_user.flickr_token)
            photosets = fk.photosets_getList()[0]
            for photoset in photosets:
                id = photoset.get('id')
                title = photoset.find('title').text
                c.all_sets.append({'id':id,
                                   'title':title,
                                   'checked':id in selected_sets})
        else:
            c.flickr_connect_url = flickr.get_authorization_url()


        return render('/settings.mako')
