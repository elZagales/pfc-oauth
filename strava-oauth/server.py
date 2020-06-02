#!flask/bin/python
import logging
import os
from flask import Flask, render_template, redirect, url_for, request, jsonify
from stravalib import Client
from database.models import Athlete
from google.cloud import datastore
from google.cloud import bigquery


app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')
datastore_client = datastore.Client()
bq_client = bigquery.Client()

@app.route("/")
def login():
    c = Client()
    url = c.authorization_url(client_id=app.config['STRAVA_CLIENT_ID'],
                              redirect_uri=url_for('.logged_in', _external=True),
                              approval_prompt='auto',
                              scope='activity:read')
    return render_template('login.html', authorize_url=url)


@app.route("/strava-oauth")
def logged_in():
    """
    Method called by Strava (redirect) that includes parameters.
    - state
    - code
    - error
    """
    error = request.args.get('error')
    state = request.args.get('state')
    if error:
        return render_template('login_error.html', error=error)
    else:
        code = request.args.get('code')
        strava_client = Client()
        access_token = strava_client.exchange_code_for_token(client_id=app.config['STRAVA_CLIENT_ID'],
                                                             client_secret=app.config['STRAVA_CLIENT_SECRET'],
                                                             code=code)
        # Get athlete info for authenticated user
        strava_athlete = strava_client.get_athlete()
        # Extract necessary items to dict
        strava_athlete_dict = {'id': strava_athlete.id, 'firstname': strava_athlete.firstname, 'lastname': strava_athlete.lastname}
        # Update Dict with access token info
        strava_athlete_dict.update(access_token)
        # Create Athlete object
        athlete = Athlete(strava_athlete_dict)
        # Generate Datastore Key
        athlete_key = datastore_client.key('Athlete', strava_athlete.id)

        try:
            # Try to get entity for generated key
            athlete_record = datastore_client.get(athlete_key)
            # If no record exists, athlete_record is an Object of type None
            if not athlete_record:
                # If record did not exist, insert into hub/sat tables in BQ
                print('in loop')
                hub_table_ref = bq_client.dataset('strava_datavault').table('athlete_hub')
                print('create hub table ref')
                sat_table_ref = bq_client.dataset('strava_datavault').table('athlete_sat')
                print('create sat table ref')
                athlete_dict = athlete.hub()
                bq_client.load_table_from_json(athlete.hub(), hub_table_ref)
                print('load hub')
                bq_client.load_table_from_json(athlete.satellite(), sat_table_ref)
                print('load sat')
                # Add property to Athlete object for verification
                athlete.in_bq = True
                print('set bq flag true')
                # Save out entity to Datastore
                athlete.save(datastore_client, athlete_key)
                print('save to datastore')

        except Exception as e:
            print('Unable to get in_bq field or insert to bq' + str(e))

        return render_template('login_results.html', athlete=strava_athlete, access_token=access_token)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
