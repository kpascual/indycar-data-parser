import requests
import yaml
import argparse
import json
import sqlite3
from pprint import pprint


with open('config.yml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

conn = sqlite3.connect(config['database'])
curs = conn.cursor()

def _get_race_keys_from_indycar():
    url = config['race_keys_url']
    r = requests.get(url)

    return r.json()


def main(year):
    seasons = _get_race_keys_from_indycar()
    for season in seasons:
        if season['Year'] == year:
            print(season['Year'])


            for event in season['Events']:
                print("Race key:")
                # Formatted to how it looks in database
                print(json.dumps({"EventId": event['EventID']}))
            
                print("Session keys:")
                for s in event['Sessions']:
                    print('Session: ' + s['SessionName'] + ': ' + json.dumps({"session_id": s['EventsSessionID']}))

                print("Raw payload:")
                pprint(event)



def save(year):
    seasons = _get_race_keys_from_indycar()
    for season in seasons:

        if season['Year'] == year:
            print(season['Events'])
            for event in season['Events']:
                event_id = _save_event(year, event['EventID'], event['EventName'])

                for session in event['Sessions']:
                    _save_event_session(event_id, session['EventsSessionID'], session['SessionName'])

            conn.commit()


def _save_event(year, event_id, event_name):
    curs.execute("""
        INSERT INTO event (source_id, source_name, year)
        VALUES (?, ?, ?)
        ON CONFLICT (source_id) DO NOTHING
    """,
        (event_id, event_name, year)
    )

    return curs.lastrowid

def _save_event_session(event_id, session_id, session_name):
    curs.execute("""
        INSERT INTO event_session (event_id, source_id, source_name)
        VALUES (?, ?, ?)
        ON CONFLICT (source_id) DO NOTHING
    """,
        (event_id, session_id, session_name)
    )


def save_all():
    seasons = _get_race_keys_from_indycar()
    for season in seasons:
        year = season['Year']

        print(season['Events'])
        for event in season['Events']:
            _save_event(year, event['EventID'], event['EventName'])

            for session in event['Sessions']:
                _save_event_session(session['EventsSessionID'], session['SessionName'])

        conn.commit()

def session_keys_by_race_id(race_id):
    curs.execute("SELECT source_info FROM race WHERE id = ?", (race_id,))
    result = curs.fetchone()

    info = json.loads(result[0])
    seasons = _get_race_keys_from_indycar()

    race = None
    for season in seasons:
        for event in season['Events']:
            if event['EventID'] == info['EventId']:
                print(event)
                # Create session
                race = event

    return race


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get race keys by year')
    parser.add_argument('-year', help='Indycar season')
    parser.add_argument('-save', help='Choose to save the results to database')
    parser.add_argument('-save_all', help='Save entire history to database')
    parser.add_argument('-raceid', help='Internal race id')

    args = parser.parse_args()
    
    if args.save:
        save(args.save)
    if args.save_all:
        save_all()
    elif args.year:
        main(args.year)
    elif args.raceid:
        session_keys_by_race_id(args.raceid)
