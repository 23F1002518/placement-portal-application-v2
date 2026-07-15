from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_mail import Mail
from flask_cors import CORS
from celery import Celery

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
mail = Mail()
cors = CORS()
celery = Celery(__name__)
