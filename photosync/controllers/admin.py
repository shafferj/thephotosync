import os
import logging
import urllib2
import tempfile
import json

from sqlalchemy import func

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import AdminController, render
from photosync import fb
from photosync import flickr
from photosync.worker import tasks
from photosync.model.meta import Session
from photosync.model import SyncRecord, AsyncTask, User
from photosync import cost

class AdminController(AdminController):

    def stats(self):
        c.user_count = Session.query(User).count()
        c.sync_count = Session.query(SyncRecord).count()
        c.async_tasks_count = Session.query(AsyncTask).count()


        data = Session.query(SyncRecord.user_id,
                             func.count(1),
                             func.sum(SyncRecord.transfer_in),
                             func.sum(SyncRecord.transfer_out))\
            .filter(SyncRecord.type == SyncRecord.TYPE_PHOTO)\
            .group_by(SyncRecord.user_id).all()

        c.user_stats = []
        c.total_cost = 0
        c.total_tin = 0
        c.total_tout = 0
        for user_id, count, tin, tout in data:
            tin = tin or 0
            tout = tout or 0
            bandwidth_cost = cost.get_bandwidth_cost(tin,tout)
            c.total_cost += bandwidth_cost
            c.total_tout += int(tout)
            c.total_tin += int(tin)
            c.user_stats.append([User.get_by_id(user_id),
                                 count,
                                 round(tin/1024/1024, 2),
                                 round(tout/1024/1024, 2),
                                 bandwidth_cost])
        c.total_tout = round(c.total_tout/1024./1024, 2)
        c.total_tin = round(c.total_tin/1024./1024, 2)

        data.sort(key=lambda d: d[-1])
        return render('/admin/stats.mako')

    def index(self):
        return render('/admin/index.mako')
