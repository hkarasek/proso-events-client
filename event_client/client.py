# -*- coding: utf-8 -*-

import simplejson as json
import requests
import itsdangerous
import hashlib
import psycopg2
import datetime


class EventClient:
    def __init__(self, api_id, api_secret, endpoint='http://localhost:8000', source='default'):
        self.source = source
        self.endpoint = endpoint
        self.api_id = api_id
        self.api_secret = api_secret
        self.signer = itsdangerous.TimestampSigner(self.api_secret)

    def get_headers(self, data: str) -> dict:
        return {
            'x-api-id': self.api_id,
            'x-api-sign': self.signer.sign(hashlib.sha1(data.encode()).hexdigest())
        }

    def push_event(self, event_type: str, data: dict):
        data['source'] = self.source
        data = [data]

        return self.push_many_events(event_type, data)

    def push_many_events(self, event_type: str, data: list):
        return self.api_post_req('/type/%s/event' % event_type, data)

    def create_type(self, json_schema):
        self.api_post_req('/type', json_schema)

    def api_post_req(self, path, data):
        data = json.dumps(data)

        req = requests.post(self.endpoint + path, headers=self.get_headers(data), data=data)
        if req.status_code != 201:
            raise Exception("Event storage error. Status: %s" % req.status_code)

    def get_types(self):
        req = requests.get("%s/type" % self.endpoint, headers=self.get_headers(''))
        return req.json()

    def delete_type(self, type_name):
        req = requests.delete("%s/type/%s" % (self.endpoint, type_name), headers=self.get_headers(''))

        if req.status_code != 200:
            raise Exception("Event storage error. Status: %s" % req.status_code)

    def get_db_connection(self):
        req = requests.get("%s/db" % self.endpoint, headers=self.get_headers(''))

        if req.status_code != 200:
            raise Exception("Event storage error. Status: %s" % req.status_code)

        return psycopg2.connect(**req.json())