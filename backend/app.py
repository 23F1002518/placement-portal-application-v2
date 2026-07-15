import os

from flask import Flask, jsonify, send_from_directory

from config import Config
from extensions import db, jwt, cache, mail, cors


def create_app(config_class=Config):
    frontend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "frontend")
    )
    # The Vite build lands in frontend/dist: the SPA shell is dist/index.html and the
    # bundled JS/CSS live under dist/assets (referenced as /assets/* by the built HTML).
    dist_dir = os.path.join(frontend_dir, "dist")
    app = Flask(
        __name__,
        static_folder=os.path.join(dist_dir, "assets"),
        static_url_path="/assets",
    )
    app.config.from_object(config_class)
    app.config["DIST_DIR"] = dist_dir

    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    for path in (
        app.config["RESUME_DIR"],
        app.config["EXPORT_DIR"],
        app.config["OFFER_LETTER_DIR"],
    ):
        os.makedirs(path, exist_ok=True)

    with app.app_context():
        import models  # noqa: F401 — register models on db.metadata before create_all
        db.create_all()
        ensure_admin()

    register_blueprints(app)
    register_error_handlers(app)
    register_frontend_routes(app, dist_dir)

    return app


def ensure_admin():
    """Create the single admin account if one does not already exist.

    Called from the app factory right after ``db.create_all()`` so the admin
    exists the moment the database is created — logging in never requires a
    separate seed step. Idempotent: safe to run on every startup. Credentials
    come from config (``ADMIN_EMAIL`` / ``ADMIN_PASSWORD``, env-overridable).
    Returns True if an admin was created, False if one was already present.
    """
    from flask import current_app
    from models import User, ROLE_ADMIN

    if User.query.filter_by(role=ROLE_ADMIN).first():
        return False
    admin = User(email=current_app.config["ADMIN_EMAIL"], role=ROLE_ADMIN)
    admin.set_password(current_app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    return True


def register_blueprints(app):
    from auth import auth_bp
    from api.admin import admin_bp
    from api.company import company_bp
    from api.student import student_bp
    from api.common import common_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(common_bp)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"message": "Not found"}), 404

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"message": "Forbidden"}), 403

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"message": "Internal server error"}), 500


def register_frontend_routes(app, dist_dir):
    @app.route("/")
    @app.route("/<path:path>")
    def spa_shell(path=None):
        # Any unmatched /api/* path is a genuine 404, not a SPA route.
        if path and path.startswith("api/"):
            return jsonify({"message": "Not found"}), 404
        # Everything else serves the built Vue SPA shell; Vue Router handles routing.
        if not os.path.exists(os.path.join(dist_dir, "index.html")):
            return (
                jsonify(
                    {
                        "message": "Frontend build not found. Run 'npm install && npm run build' "
                        "in the frontend/ directory (or 'npm run dev' for the Vite dev server)."
                    }
                ),
                503,
            )
        return send_from_directory(dist_dir, "index.html")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
