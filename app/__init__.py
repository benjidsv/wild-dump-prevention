import click
from flask import Flask
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash

from config import DevConfig
from app.extensions import database, csrf, babel
import os

def create_app(config_class=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    babel.init_app(app)
    database.init_app(app)
    csrf.init_app(app)

    app.jinja_env.globals["csrf_token"] = generate_csrf
    app.config["LANGUAGES"] = {
        "en": "English",
        "fr": "Français"
    }
    app.config["BABEL_DEFAULT_LOCALE"] = "en"

    @babel.localeselector
    def get_locale():
        from flask import request, session
        return request.args.get('lang') or session.get('lang') or request.accept_languages.best_match(
            app.config['LANGUAGES'].keys())

    from app.routes import main
    app.register_blueprint(main)

    @app.cli.command("create-db")
    def create_db():
        """Create every table defined in SQLAlchemy models."""
        click.echo("Creating tables …")
        database.create_all()
        click.echo("✓ Database ready")

    @app.cli.command("drop-db")
    @click.confirmation_option("--yes", prompt="Drop **ALL** tables?")
    def drop_db():
        """Drops the database"""
        database.drop_all()
        click.echo("✓ All tables dropped")

    @app.cli.command("create-superuser")
    def create_superuser():
        """Create the superuser. This role can promote/demote any account to admin."""
        from app.db.models import User
        if User.query.filter_by(is_superadmin=True).first():
            click.echo("A super-admin already exists, abort.")
            return
        name = click.prompt("Username")
        email = click.prompt("E-mail")
        pwd = click.prompt("Password", hide_input=True,
                           confirmation_prompt=True)

        user = User(name=name,
                    mail=email,
                    password=generate_password_hash(pwd),
                    is_admin=True,
                    is_superadmin=True)
        database.session.add(user)
        database.session.commit()
        click.echo("✓ Super-admin created")

    @app.route('/set-language/<lang>')
    def set_language(lang):
        from flask import session, redirect, request
        session['lang'] = lang
        return redirect(request.referrer or '/')

    return app
