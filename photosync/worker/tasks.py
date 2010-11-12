from __future__ import absolute_import
import os
import json
import time
import traceback
import logging
import tempfile

from photosync.model.meta import Session
from photosync.model import User, SyncRecord, AsyncTask
from photosync.model.settings import UserSetting, UserSettingConst
from photosync import fb
from photosync import flickr
from photosync import http

from photosync.worker.job import Job, register

log = logging.getLogger(__name__)


class TaskHandler(object):

    def __init__(self, job, task_id, task_args, task_kwargs):
        self.job = job
        self.__task_id = task_id
        self.__args = task_args
        self.__kwargs = task_kwargs

    __task = None
    __task_fetched = False

    @property
    def task(self):
        if not self.__task_fetched:
            self.__task_fetched = True
            self.__task = Session.query(AsyncTask).filter_by(
                id=self.__task_id).first()
        return self.__task

    def set_status(self, completed, total, data):
        log.info("%s %s Completed %s/%s: %r",
                 self.__class__.__name__, self.job.queue_id,
                 completed, total, data)
        self.task.set_status(completed, total, data, job=self.job)
        Session.commit()

    def run(self):
        return

    @classmethod
    def submit(cls, *args, **kwargs):
        task = AsyncTask()
        Session.add(task)
        Session.commit()
        queue_id = Job.submit(cls, task.id, args, kwargs)
        task.queue_id = queue_id
        Session.commit()
        return task

    def __call__(self):
        try:
            result = self.run(*self.__args, **self.__kwargs)
        except Exception, e:
            traceback.print_exc()
            log.exception("Failed to run task %s", self.__class__.__name__)
            raise

@register
class LongPing(TaskHandler):

    def run(self, N):
        for i in xrange(N):
            log.info("did %s sleeps" % i)
            self.set_status(i+1, N, "did %s sleeps" % i)
            time.sleep(1)
        return "all done"


class FlickrRequest(http.Request):

    def read_response(self):
        raw = super(FlickrRequest, self).read_response()
        if raw.startswith('jsonFlickrApi('):
            return json.loads(raw[len('jsonFlickrApi('):-1])
        return raw

@register
class FullSync(TaskHandler):


    def run(self, user_id):
        import pdb; pdb.set_trace()
        self.user = User.get_by_id(user_id)
        self.fk = flickr.FlickrAPI(self.user.flickr_token)
        self.fb_user = fb.GraphUser(access_token=self.user.fb_access_token)
        photosets = self.fk.photosets_getList()[0]

        self.synced_photos = 0
        self.total_photos = 0
        for photoset in photosets:
            self.total_photos += int(photoset.get('photos'))

        self.set_status(self.synced_photos, self.total_photos, "syncing Flickr photos to Facebook")

        self.fb_privacy = UserSetting.get(setting=UserSettingConst.FB_PRIVACY)

        for photoset in photosets:
            self.sync_photoset(photoset)


    def sync_photoset(self, photoset):
        log.info("Syncing flickr photoset %s to facebook", photoset.get('id'))
        sync = Session.query(SyncRecord).filter_by(
            flickrid=photoset.get('id'), type=SyncRecord.TYPE_ALBUM).first()
        album = None
        if sync and (sync.running or sync.success):
            # don't resync unless we failed before
            log.info("skipping... already synced")
            album = fb.GraphAlbum(id=sync.fbid, access_token=self.user.fb_access_token)
            if not album.data:
                album = None
        if not album:
            sync = SyncRecord(SyncRecord.TYPE_ALBUM)
            sync.flickrid = photoset.get('id')

            album = self.fb_user.albums.add(
                photoset.find('title').text,
                photoset.find('description').text,
                privacy=self.fb_privacy)

            if album:
                sync.fbid = album.id
                sync.status = SyncRecord.STATUS_SUCCESS
            else:
                sync.status = SyncRecord.STATUS_FAILED
            Session.add(sync)
            Session.commit()

        photos = self.fk.photosets_getPhotos(photoset_id=photoset.get('id'))[0]

        photos_to_sync = []
        for photo in photos:
            log.info("Syncing flickr photo %s to facebook", photo.get('id'))
            sync = Session.query(SyncRecord).filter_by(
                flickrid=photo.get('id'), type=SyncRecord.TYPE_PHOTO).first()
            fb_photo = None
            if sync and (sync.running or sync.success):
                log.info("Skipping... already synced")
                fb_photo = fb.GraphPhoto(id=sync.fbid, access_token=self.user.fb_access_token)
                if not fb_photo.data:
                    fb_photo = None
                self.synced_photos += 1
            if not fb_photo:
                photos_to_sync.append(photo)

        already_synced = len(photos) - len(photos_to_sync)
        self.synced_photos += already_synced
        status = "%s photos from %s already synced" % (already_synced,
                                                       photoset.find('title').text)
        self.set_status(self.synced_photos, self.total_photos, status)

        fetcher = http.Fetcher()
        requests = []
        for photo in photos_to_sync:
            url = flickr.get_url(
                self.user.flickr_token,
                method='flickr.photos.getSizes',
                photo_id=photo.get('id'))
            request = FlickrRequest(url)
            requests.append((photo, request))
            fetcher.queue(request)
        fetcher.run()

        fetcher = http.Fetcher()
        img_requests = []
        for photo, request in requests:
            sync = SyncRecord(SyncRecord.TYPE_PHOTO)
            sync.flickrid = photo.get("id")
            res = request.read_response()
            img_url = res['sizes']['size'][-1]['source']
            f, temp_filename = tempfile.mkstemp()
            log.info("Downloading image %s", img_url)
            img_request = http.Request(img_url, filename=temp_filename)
            img_requests.append((photo, temp_filename, sync, img_request))
            fetcher.queue(img_request)
        fetcher.run()

        for photo, temp_filename, sync, img_request in img_requests:
            graph_photo = album.photos.add(temp_filename, photo.get('title'))
            os.remove(temp_filename)
            if graph_photo:
                sync.fbid = graph_photo.id
                sync.status = SyncRecord.STATUS_SUCCESS
            else:
                sync.status = SyncRecord.STATUS_FAILED
            Session.add(sync)
            Session.commit()
            self.synced_photos += 1
            status = "Synced %s from %s to Facebook" % (photo.get('title'),
                                                        photoset.find('title').text)
            self.set_status(self.synced_photos, self.total_photos, status)

