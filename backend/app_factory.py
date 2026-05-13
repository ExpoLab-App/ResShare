import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from backend.controller import register_controllers


def create_app():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app = Flask(__name__)

    load_dotenv()
    allowed_origins = [
        'http://localhost:5997',
        'http://127.0.0.1:5997',
        'https://res-share-deployable.vercel.app',
    ]
    additional_origins = os.environ.get('CORS_ORIGINS', '')
    if additional_origins:
        allowed_origins.extend([origin.strip() for origin in additional_origins.split(',') if origin.strip()])

    CORS(app, origins=allowed_origins, supports_credentials=True)

    flask_env = os.environ.get('FLASK_ENV', 'development')
    is_development = flask_env == 'development'

    secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        if is_development:
            secret_key = 'dev-secret-key-change-in-production'
            logger.warning("Using default secret key for development. DO NOT use in production!")
        else:
            raise RuntimeError("FLASK_SECRET_KEY is required in production for session management")
    app.secret_key = secret_key

    if is_development:
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_COOKIE_SECURE'] = False
        logger.info("Running in DEVELOPMENT mode - cookies configured for HTTP")
    else:
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_SECURE'] = True
        logger.info("Running in PRODUCTION mode - cookies configured for HTTPS")

    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    app.config['SESSION_COOKIE_NAME'] = 'session'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'

    register_controllers(app, logger=logger)

    return app
