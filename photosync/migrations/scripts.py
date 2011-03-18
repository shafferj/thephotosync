import functools
import httplib
from functional import compose
from itertools import imap, izip, starmap

from photosync import flickr
from photosync import fb
from photosync.model import User, SyncRecord
from photosync.model.meta import Session
from photosync import http


__all__ = [
    'load_transfer_data',
    'delete_empty_albums'
    ]


def delete_empty_albums():
    """Delete empty albums that were accidentally created."""

    records = Session.query(SyncRecord).filter(
        SyncRecord.type==SyncRecord.TYPE_ALBUM).all()

    for record in records:
        user = record.user
        if user.fb_access_token:
            fbalbum = fb.GraphAlbum(
                id=record.fbid,
                access_token=user.fb_access_token)
            if len(fbalbum.photos) == 0:
                #this is an empty album... let's delete it.
                print "Deleting album %r for user %r" % (record.fbid, user)
                fbalbum.delete()
                #Session.delete(record)
    print "All done"


def load_transfer_data():
    """Loads bytes transferred data into the db.

    You will want to run this sql first:

      ALTER TABLE sync_records ADD COLUMN transfer_in int(11) DEFAULT 0;
      ALTER TABLE sync_records ADD COLUMN transfer_out int(11) DEFAULT 0;

    """

    records = Session.query(SyncRecord).filter(
        SyncRecord.type==SyncRecord.TYPE_PHOTO).filter(
        SyncRecord.transfer_in==0).all()

    def progress(message):
        def func(processed, total):
            print "%i/%i\t%i\t%s" % (processed, total, float(processed)/total*100, message)
        return func

    def get_size_request(record):
        return http.JsonRequest(flickr.get_url(
                record.user.flickr_token,
                method='flickr.photos.getSizes',
                photo_id=record.flickrid))


    def get_byte_size_request(request):
        try:
            url = request.read_response()['sizes']['size'][-1]['source']
            return http.Request(url, method="HEAD")
        except:
            pass

    def get_content_size(request):
        return int(request.read_headers()['Content-Length']) if request else None


    def migrate_sync_record(sync_record, content_size):
        if content_size:
            sync_record.transfer_in = content_size
            sync_record.transfer_out = content_size
            Session.commit()
        else:
            print "Couldn't get content size for", sync_record.id


    fetcher = http.Fetcher(
        progress_callback=progress("getting image urls"))

    map(compose(fetcher.queue, get_size_request), records)

    size_fetcher = http.Fetcher(
        progress_callback=progress("getting byte sizes"))

    map(compose(size_fetcher.queue, get_byte_size_request), fetcher.run())

    list(starmap(migrate_sync_record,
                 izip(records, imap(get_content_size, size_fetcher.run()))))
