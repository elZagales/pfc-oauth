# from flask_mongoengine import MongoEngine
#
# db = MongoEngine()
#
# def initialize_db(app):
#     db.init_app(app)

from google.cloud import datastore


def initialize_ds(app):
    datastore_client = datastore.Client()
