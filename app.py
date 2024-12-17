from flask import Flask, request, redirect, jsonify
from flask_restful import Api
import redis
from rq import Queue

from controllers import initialize_routes
from config import Config

import psycopg2


app = Flask(__name__)
app.config.from_object(Config)

# Redis Connection and Queue Initialization
redis_conn = redis.from_url(app.config['REDIS_URL'])
queue = Queue('gemini', connection=redis_conn)

conn = psycopg2.connect(database=app.config['POSTGRES_DB'],
                        user=app.config['POSTGRES_USER'],
                        password=app.config['POSTGRES_PASSWORD'],
                        host=app.config['POSTGRES_HOST'],
                        port=app.config['POSTGRES_PORT'])

# Initialize routes
initialize_routes(app,redis_conn,conn)

if __name__ == '__main__':
    app.run(debug=True, port=3000)