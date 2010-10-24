from photosync.tests import *

class TestFlickrauthController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='flickrauth', action='index'))
        # Test response...
