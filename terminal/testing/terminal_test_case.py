import testify as T
from pyramid import testing


class TerminalTestCase(T.TestCase):
    @T.setup
    def setup(self):
        self.config = testing.setUp()

    @T.teardown
    def teardown(self):
        testing.tearDown()
