import unittest

import tests.runtime.app as j

appurl = "/%s"
header = {"content-type": "application/json"}


class DBCase(unittest.TestCase):
    def create_app(self):
        j.app.config['TESTING'] = True
        self.dburi = j.app.config['SQLALCHEMY_DATABASE_URI']
        j.app.config['DATABASE'] = self.dburi
        self.app = j.app.test_client()

    def setUp(self):
        self.create_app()
        self.session = j.db

    # def tearDown(self):
    #     self.session.remove()


if __name__ == "__main__":
    unittest.main()
