# nodbody.live
## PainfulSines Notes
This fork is just me experementing with CSS grids, as they are new to me, if you are intrested in seeing that then checkout the css grid branch, this branch probily will have almost no furthure work done on it unless I feel the need to push the changes...

# SCSS?
Yes, I love scss, and some people disagree because it is compiled, but with the use of a live compiler it is easy to get started in, I reccomend this [Live Sass Compiler for vscode](https://github.com/glenn2223/vscode-live-sass-compiler/), it is the one I use all the time and it is easy to get working in VSCode

# Example
[Link To Preview of Current Design](https://painfulsine9038.github.io/Nobody.live/static/test/)
## Architecture

A worker script (`scanner.py`) loops through the Twitch API's list of streams and spins until it inserts all streamers it finds matching the search criteria (default zero viewers), then it starts again. These streamers are pruned after a set number of seconds (`SECONDS_BEFORE_RECORD_EXPIRATION`) on the assumption that someone will view them and then they won't have zero viewers any more so should not be served for too long.

Environment variables needed for both scanner and app:

* `NOBODY_HOST`: the database host
* `NOBODY_DATABASE`: the database name
* `NOBODY_USER`: the database user
* `NOBODY_PASSWORD`: the database password

Environment variables to be set for the scanner only:

* `CLIENT_ID`: Your Twitch application client ID (found at https://dev.twitch.tv/console)
* `CLIENT_SECRET`: Your Twitch application client secret (found at https://dev.twitch.tv/console)

Meanwhile, the Flask app in `app.py` serves the index and the endpoint to get a random streamer.

## Getting Up and Running

* Install and start Postgres with a created database
* Run the stream fetcher (e.g. `CLIENT_ID=xxxxxx CLIENT_SECRET=xxxxxx scanner.py`). This will need to run continuously. Be sure to include your database credentials.
* Run the flask app (`flask run`). Be sure to include your database credentials.

This is obviously not production ready; you'll need to make sure all services are running as daemons (some config files are included in `etc`) and that your flask app is running safely (e.g. behind gunicorn/nginx/pick your poison).

## Dependencies

Update direct dependencies in `requirements.in`; use `pip-compile` to compile them down to `requirements.txt` if you update them.

## Components

* [Loading throbber Copyright (c) 2014 Sam Herbert](https://github.com/SamHerbert/SVG-Loaders)
* [Micromodal Copyright (c) 2017 Indrashish Ghosh](https://github.com/Ghosh/micromodal)
