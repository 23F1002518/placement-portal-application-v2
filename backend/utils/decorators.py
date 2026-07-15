from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from extensions import db
from models import User


def login_required(fn):
    """Require any valid JWT, regardless of role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles):
    """Require a valid JWT whose 'role' claim is one of `roles`."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"message": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def current_user():
    """Load the User row for the current JWT identity. Call inside a request with a valid JWT."""
    user_id = get_jwt_identity()
    return db.session.get(User, int(user_id))
