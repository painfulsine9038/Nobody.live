#!/usr/bin/env python3

from functools import partial
import json
import os
import datetime
import pprint

from asyncpg import create_pool
from sanic import Sanic
from sanic.response import json as sanic_json, text

app = Sanic(__name__)

# use builtin json with unicode instead of sanic's
json_dumps = partial(json.dumps, separators=(",", ":"), ensure_ascii=False)

@app.listener('before_server_start')
async def register_db(app, loop):
    app.config['pool'] = await create_pool(
        dsn=f"postgres://{os.environ.get('NOBODY_USER')}:{os.environ.get('NOBODY_PASSWORD')}@{os.environ.get('NOBODY_HOST')}/{os.environ.get('NOBODY_DATABASE')}",
        min_size=10,
        max_size=10,
        max_queries=1000,
        max_inactive_connection_lifetime=300,
        loop=loop)

@app.listener('after_server_stop')
async def close_connection(app, loop):
    pool = app.config['pool']
    async with pool.acquire() as conn:
        await conn.close()

app.static('/', './static/index.html')
app.static('/static', './static')

@app.get('/stream')
async def get_streams(request):
    pool = request.app.config['pool']

    count = int(request.args.get('count', 1))
    include = request.args.get('include', '')
    exclude = request.args.get('exclude', '')
    lang = request.args.get('lang', '')
    min_age = int(request.args.get('min_age', 0))

    # do a moderate approximation of not falling over
    if count > 64 or len(include) + len(exclude) > 64:
        return text('Filter too large! Please request fewer records.', 413)

    include_list = include.split()
    exclude_list = exclude.split()

    if not include_list and not exclude_list and not lang and min_age == 0:
        # if we have no criteria we can optimize
        games_query = "SELECT data FROM streams TABLESAMPLE system_rows($1)"

        async with pool.acquire() as conn:
            streams = await conn.fetch(games_query, count)
    else:
        # this is so hacky but it looks like how we have to do things for asyncpg.
        # if anyone knows of an easier way to do LIKE on ALL elements of a list (and inverse)
        # than this please tell me
        query_arg_string = ''
        query_arg_index = 1
        query_arg_list = []

        for exclusion in exclude_list:
            query_arg_string += f"AND lower(game) NOT LIKE ${query_arg_index} "
            query_arg_index += 1
            query_arg_list.append(f"%{exclusion.lower()}%")

        for inclusion in include_list:
            query_arg_string += f"AND lower(game) LIKE ${query_arg_index} "
            query_arg_index += 1
            query_arg_list.append(f"%{inclusion.lower()}%")

        if min_age:
            query_arg_string += f"AND streamstart < (NOW() - interval '1 minute' * ${query_arg_index})"
            query_arg_index += 1
            query_arg_list.append(min_age)

        if lang:
            query_arg_string += f"AND lang = ${query_arg_index}"
            query_arg_index += 1
            query_arg_list.append(lang)

        query_arg_list.append(count)

        games_query = f"""
            SELECT data FROM streams
            WHERE 1=1
            {query_arg_string}
            ORDER BY RANDOM()
            LIMIT ${query_arg_index}"""

        async with pool.acquire() as conn:
            streams = await conn.fetch(games_query, *query_arg_list)

    if not streams:
        return sanic_json([], dumps=json_dumps)

    extracted_streams = [json.loads(stream[0]) for stream in streams]
    return sanic_json(extracted_streams, dumps=json_dumps)


@app.get('/stream/<stream_id>')
async def get_stream_details(request, stream_id):
    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        stream_details_query = "SELECT * FROM streams WHERE id = $1"
        stream_details = await conn.fetch(stream_details_query, stream_id)

        if not stream_details:
            return text('No such stream.', 410)

        twitch_data = json.loads(stream_details[0]['data'])

        now = datetime.datetime.now()
        scraped_at = datetime.datetime.fromtimestamp(stream_details[0]['time'])
        age = now - scraped_at
        start_age = now - stream_details[0]['streamstart']

        twitch_data['scraped_at_seconds_ago'] = age.total_seconds()
        twitch_data['streamstart_seconds_ago'] = start_age.total_seconds()
        return text(pprint.pformat(twitch_data))


if __name__ == "__main__":
    if os.environ.get('NOBODY_DEBUG'):
        app.run(host='0.0.0.0', port=5000, access_log=False, debug=True, auto_reload=True)
    else:
        app.run(host='0.0.0.0', port=8000, access_log=False, debug=False)
