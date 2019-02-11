#!/usr/bin/env bash
gunicorn -w 4 -b 0.0.0.0:8090 flask_hello_world:app
