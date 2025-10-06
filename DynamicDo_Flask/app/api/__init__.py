from flask import Flask


def register_blueprints(app: Flask) -> None:
    from .health import health_bp
    from .tasks import tasks_bp
    from .users import users_bp
    from .reminder import reminder_bp

    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(reminder_bp, url_prefix="/api/reminders")

