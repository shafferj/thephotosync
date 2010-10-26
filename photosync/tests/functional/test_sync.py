from photosync.tests import *

class TestSyncController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='sync', action='index'))
        # Test response...
