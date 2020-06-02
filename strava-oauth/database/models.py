import google.cloud.datastore as datastore
import hashlib
import datetime


class Athlete(object):
    """Athlete item model"""

    def __init__(self, params):
        self.athlete_hub_seq = hashlib.md5(str(params['id']).encode()).hexdigest()
        self.athlete_id = params['id']
        self.firstname = params['firstname']
        self.lastname = params['lastname']
        self.access_token = params['access_token']
        self.expires_at = params['expires_at']
        self.refresh_token = params['refresh_token']
        self.load_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.record_source = 'Strava'
        # self.in_bq = False

    def hub(self):
        hub_record = [{
            'athlete_hub_seq': self.athlete_hub_seq,
            'athlete_id': self.athlete_id,
            'hub_load_date': self.load_date,
            'record_source': self.record_source
        }]

        return hub_record

    def satellite(self):
        satellite_record = [{
            'athlete_hub_seq': self.athlete_hub_seq,
            'sat_load_date': self.load_date,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'hash_diff': hashlib.md5((self.firstname.strip()+self.lastname.strip()).encode()).hexdigest(),
            'record_source': self.record_source
        }]

        return satellite_record

    def to_entity(self, key):

        entity = datastore.Entity(key=key)
        properties = self.__dict__
        # properties.__delitem__('athlete_id')
        entity.update(properties)

        return entity

    def save(self, client, key):

        record = self.to_entity(key)
        client.put(record)

        return self
