from photosync.tests import *

class TestHomepageController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='homepage', action='index'))
        # Test response...
