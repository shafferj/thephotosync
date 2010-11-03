import os
import logging
import urllib2
import tempfile

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from gearman.client import GearmanClient

from photosync.lib.base import BaseController, render
from photosync import fb
from photosync import flickr
from photosync.model.meta import Session
from photosync.model import SyncRecord, AsyncTask

log = logging.getLogger(__name__)


class SyncController(BaseController):

    def long_ping(self):
        client = GearmanClient(['localhost:4730'])
        AsyncTask().submit_job(
            'long_ping',
            int(request.GET.getone('seconds')),
            background=True)
        redirect(url('index'))

    def index(self):
        fb_user = fb.GraphUser()
        fk = flickr.FlickrUser()
        photosets = fk.photosets_getList()[0]
        for photoset in photosets:
            log.info("Syncing flickr photoset %s to facebook", photoset.get('id'))

            sync = Session.query(SyncRecord).filter_by(
                flickrid=photoset.get('id'), type=SyncRecord.TYPE_ALBUM).first()
            if sync and (sync.running or sync.success):
                # don't resync unless we failed before
                log.info("skipping... already synced")
                album = fb.GraphAlbum(id=sync.fbid)
            else:

                sync = SyncRecord(SyncRecord.TYPE_ALBUM)
                sync.flickrid = photoset.get('id')

                album = fb_user.albums.add(photoset.find('title').text,
                                          photoset.find('description').text)
                if album:
                    sync.fbid = album.id
                    sync.status = SyncRecord.STATUS_SUCCESS
                else:
                    sync.status = SyncRecord.STATUS_FAILED
                Session.add(sync)
                Session.commit()

            photos = fk.photosets_getPhotos(photoset_id=photoset.get('id'))[0]
            for photo in photos:
                log.info("Syncing flickr photo %s to facebook", photo.get('id'))
                sync = Session.query(SyncRecord).filter_by(
                    flickrid=photo.get('id'), type=SyncRecord.TYPE_PHOTO).first()
                if sync and (sync.running or sync.success):
                    log.info("Skipping... already synced")
                else:
                    sync = SyncRecord(SyncRecord.TYPE_PHOTO)
                    sync.flickrid = photo.get("id")

                    sizes_response = None
                    for i in xrange(3):
                        try:
                            sizes_response = fk.photos_getSizes(photo_id=photo.get('id'))[0]
                        except IOError, e:
                            log.warn("Unable to reach flickr api... trying again: %r", e)
                    if sizes_response is None:
                        log.error("Unable to reach flickr api... skipping photo: %r",
                                  photo.get('id'))
                        sync.status = SyncRecord.STATUS_FAILED
                        Session.add(sync)
                        Session.commit()
                        continue #try the next one

                    img_url = sizes_response[-1].get('source')
                    log.info("Downloading image %s", img_url)
                    data = urllib2.urlopen(img_url).read()
                    f, temp_filename = tempfile.mkstemp()
                    f = os.fdopen(f, 'w')
                    f.write(urllib2.urlopen(img_url).read())
                    f.close()
                    graph_photo = album.photos.add(temp_filename, photo.get('title'))
                    os.remove(temp_filename)
                    if graph_photo:
                        sync.bfid = graph_photo.id
                        sync.status = SyncRecord.STATUS_SUCCESS
                    else:
                        sync.status = SyncRecord.STATUS_FAILED
                    Session.add(sync)
                    Session.commit()

        return 'Hello World'
