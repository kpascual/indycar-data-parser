import requests
import json
import time
import sqlite3
import datetime
import os
import yaml
import argparse
from pprint import pprint


# Configurations
with open(os.path.join(os.path.dirname(__file__), 'config.yml'), 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# DB connection
conn = sqlite3.connect(config['database'])
conn.row_factory = sqlite3.Row
curs = conn.cursor()

# Constants
ASSET_HOST_DOMAIN = 'http://www.imscdn.com/'
PDF_DIR = config['pdf_root']


def get_event_sessions(event_id):
    # Get all sessions
    curs.execute("""
        SELECT 
            event_id,
            id AS session_id,
            source_id
        FROM 
            event_session
        WHERE 
            event_id = ?""",
        (event_id)
    )

    return [dict(row) for row in curs.fetchall()]

def main(event_id):
    sessions = get_event_sessions(event_id)

    for session in sessions:
        get_race_session_pdfs(session)




def get_race_session_pdfs(session):
    #race_id = session['race_id']
    
    event_id = session['event_id']
    session_id = session['session_id']
    source_session_id = session['source_id']

    #url = 'https://www.indycar.com/Services/IndyStats.svc/EventsSessionDetails?id={0}'.format(session_id)
    url = 'https://www.indycar.com/api/results/EventsSessionDetails?id={0}'.format(source_session_id)
    print(url)
    r = requests.get(url)
    results = r.json()

    pprint(results['SessionReports'])
    # Save section results
    for report in results['SessionReports']:
        print(report)
        asset_url = ASSET_HOST_DOMAIN + report['Url']
        pdf_contents = requests.get(asset_url)

        filename = PDF_DIR + '{0}_{1}_{2}.pdf'.format(session_id, source_session_id, report['DocumentType'].replace(' ',''))
        with open(filename, 'wb') as f:
            f.write(pdf_contents.content)
        time.sleep(4)
        

if __name__ == '__main__':
    # Commandline arguments
    parser = argparse.ArgumentParser(description='Save PDF files for all race sessions')
    parser.add_argument('--event', help='ID of the associated event')

    args = parser.parse_args()

    if args.event:
        main(args.event)
