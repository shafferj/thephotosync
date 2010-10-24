from photosync.tests import *

class TestLogoutController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='logout', action='index'))
        # Test response...
