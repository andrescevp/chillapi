import json
import os

from faker import Faker
from flask import Response
from unittest import mock

from tests.runtime_auth_strict import appurl, DBCase, header

locale_list = ['ja-JP', 'en_US']
fake = Faker(locale_list)
fake.seed_locale('en_US', 0)


class ApiTest(DBCase):

    def test_path_in_swagger_schema(self):
        rv: Response = self.app.get(appurl % "swagger.json", headers = header)
        response = json.loads(rv.data)
        self.assertTrue(rv.status_code == 200)
        self.assertTrue('/create/author' in response['paths'].keys())


    def test_validations(self):
        rv: Response = self.app.put("/create/dummy", headers = header, json = {
                "no": 32321,
                })

        response = json.loads(rv.data)
        self.assertTrue(rv.status_code == 400)
        self.assertTrue('{"name": ["This field is required."]}' == response['message'])

        rv: Response = self.app.put("/create/author", headers = header, json = {
                "asin": "a",
                "name": {},
                })

        response = json.loads(rv.data)

        self.assertTrue(rv.status_code == 400)
        self.assertTrue('{"name": ["This field is required."], "asin": ["Field must be between 5 and 100 characters long."]}'
                        == response['message'])

        rv: Response = self.app.put("/create/author", headers = header, json = {
                "asin": "aaaaaa",
                "name": 'a',
                })

        response = json.loads(rv.data)

        self.assertTrue(rv.status_code == 400)
        self.assertTrue('{"name": ["This field contains invalid JSON"]}'
                        == response['message'])

        rv: Response = self.app.put("/create/author", headers = header, json = {
                "asin": "aaaaaa",
                "name": {},
                })

        response = json.loads(rv.data)

        self.assertTrue(rv.status_code == 400)
        self.assertTrue('{"name": ["This field is required."]}'
                        == response['message'])


    def test_put_get_post_delete_single_dummy(self):
        name = fake.unique.name()
        rv: Response = self.app.put("/create/dummy", headers = header, json = {
                "name": name,
                })

        response = json.loads(rv.data)

        self.assertTrue(rv.status_code == 200)
        rv: Response = self.app.get(
                f"/read/dummy/{response['id']}",
                headers = header
                )

        response = json.loads(rv.data)
        self.assertTrue(response['name'] == name)

        self.assertTrue(rv.status_code == 200)
        rv: Response = self.app.post(f"/update/dummy/{response['id']}", headers = header, json = {
                "name": f'POST_{name}',
                })

        response = json.loads(rv.data)
        self.assertTrue(response['name'] == f'POST_{name}')

        self.assertTrue(rv.status_code == 200)

        rv: Response = self.app.delete(f"/delete/dummy/{response['id']}", headers = header)

        response = json.loads(rv.data)

        self.assertTrue(response['message'] == 'ok')

        self.assertTrue(rv.status_code == 200)


    def test_put_get_post_delete_list_dummy(self):
        name = fake.unique.name()
        name2 = fake.unique.name()
        rv: Response = self.app.put("/create/dummies", headers = header, json = [
                {
                        "name": name,
                        },
                {
                        "name": name2,
                        },
                {
                        "name": 'test',
                        }
                ])

        response = json.loads(rv.data)

        self.assertTrue(response['message'] == 'Affected rows: 3')
        self.assertTrue(rv.status_code == 200)

        rv: Response = self.app.get(
                '/read/dummies?size={"limit":100,"offset":0}&order={"field": ["id"],"direction": "asc"}',
                headers = header
                )

        response = json.loads(rv.data)

        self.assertTrue('_meta' in response)
        self.assertTrue('data' in response)
        self.assertTrue(len(response['data']) > 1)
        # self.assertTrue(response['_meta']['total_records'] == 6)
        print(response)
        self.assertTrue(rv.status_code == 200)
        _found = False
        for _i, item in enumerate(response['data']):
            if item['name'] == 'test':
                _found = True
            response['data'][_i] = {**item, **{'name': f"POST_MULTI_{item['name']}"}}
        self.assertTrue(_found)

        rv: Response = self.app.post(f"/update/dummies", headers = header, json = response['data'])

        response_bu = json.loads(rv.data)

        _found = False
        _ids = []
        for _i, item in enumerate(response_bu):
            _ids.append(item['id'])
            if 'POST_MULTI_' in item['name']:
                _found = True

        self.assertTrue(_found)
        self.assertTrue(response_bu == response['data'])
        self.assertTrue(rv.status_code == 200)

        rv: Response = self.app.delete(f"/delete/dummies", headers = header, json = _ids)

        response = json.loads(rv.data)

        self.assertTrue(response == 'ok')
        self.assertTrue(rv.status_code == 200)
