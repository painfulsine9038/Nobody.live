#!/usr/bin/env python3

import json
import os
import datetime
import functools
import subprocess
import sys

from flask import Flask, jsonify, json, request

import db_utils
cursor = db_utils.get_cursor()

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['JSON_AS_ASCII'] = False

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
git_rev_fetch = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=script_path, stdout=subprocess.PIPE)
loaded_git_rev = git_rev_fetch.stdout.decode("ascii").rstrip()

# decorator to cache a result for a given time
# https://stackoverflow.com/a/50866968/1588786
def cache(ttl=datetime.timedelta(seconds=5)):
    def wrap(func):
        time, value = None, None
        @functools.wraps(func)
        def wrapped(*args, **kw):
            nonlocal time
            nonlocal value
            now = datetime.datetime.now()
            if not time or now - time > ttl:
                value = func(*args, **kw)
                time = now
            return value
        return wrapped
    return wrap

@cache(ttl=datetime.timedelta(seconds=1))
def get_sys_load():
    return os.getloadavg()

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/stream')
def get_streams():
    count = request.args.get('count', default=1, type=int)
    include = request.args.get('include', default='', type=str)
    exclude = request.args.get('exclude', default='', type=str)

    # do a moderate approximation of not falling over
    if count > 64 or len(include) + len(exclude) > 128:
        return ('Filter too large! Please request fewer records.', 413)

    streams = db_utils.get_games(cursor, count, include.split(), exclude.split())

    if not streams:
        return jsonify([])

    extracted_streams = [json.loads(stream[0]) for stream in streams]
    return jsonify(extracted_streams)

@app.route('/stats')
def get_stats_json():
    stats = (db_utils.get_stats())
    stats['load'] = get_sys_load()
    stats['rev'] = loaded_git_rev

    return jsonify(stats)

@app.route('/motd')
@cache(ttl=datetime.timedelta(minutes=1))
def get_motd():
    try:
        with open('motd.txt', "r") as fh:
            return fh.read().strip()
    except IOError:
        return ('', 204)

@app.route('/games')
@cache(ttl=datetime.timedelta(seconds=30))
def get_games_streamers():
    games = [{'game': game[0], 'streamers': game[1]} for game in db_utils.get_games_list_by_game(cursor)]
    return jsonify(sorted(games, key=lambda game: game['streamers'], reverse=True))

if __name__ == "__main__":
    app.run()
