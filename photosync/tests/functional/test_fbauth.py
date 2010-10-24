from photosync.tests import *

class TestFbauthController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='fbauth', action='index'))
        # Test response...
