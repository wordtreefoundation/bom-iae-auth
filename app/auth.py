# -*- coding: utf-8 -*-
from flask import Flask, redirect, render_template_string, request, url_for, send_from_directory, jsonify
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.user import current_user, login_required, UserManager, UserMixin, SQLAlchemyAdapter
from flask.ext.login import login_url
from functools import wraps
import datetime
import jwt
import iso8601
from os import environ

# Use a Class-based config to avoid needing a 2nd file
class ConfigClass(object):
    CSRF_ENABLED = True
    CONSUMER_TTL = 86400

    # Configure Flask-User
    USER_ENABLE_USERNAME         = True
    USER_ENABLE_CONFIRM_EMAIL    = True
    USER_ENABLE_CHANGE_USERNAME  = True
    USER_ENABLE_CHANGE_PASSWORD  = True
    USER_ENABLE_FORGOT_PASSWORD  = True
    USER_ENABLE_RETYPE_PASSWORD  = True
    USER_LOGIN_TEMPLATE = 'flask_user/login_or_register.html'
    USER_REGISTER_TEMPLATE = 'flask_user/login_or_register.html'

def create_app(test_config=None):                   # For automated tests
    # Setup Flask and read config from ConfigClass defined above
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')
    
    c = app.config

    # Load local_settings.py if file exists         # For automated tests
    app.config.from_pyfile('local_config.py')

    mailgun_username = environ.get('MAILGUN_USERNAME')
    if mailgun_username:
        c['MAIL_SERVER'] = 'smtp.mailgun.org'
        c['MAIL_PORT'] = 465
        c['MAIL_USE_TLS'] = True
        c['MAIL_USERNAME'] = mailgun_username
        c['MAIL_PASSWORD'] = environ['MAILGUN_PASSWORD']
        c['MAIL_DEFAULT_SENDER'] = environ.get('MAILGUN_SENDER', mailgun_username)

    consumer_secret = environ['CONSUMER_SECRET']
    c['CONSUMER_KEY'] = environ.get('CONSUMER_KEY', 'annotateit')
    c['CONSUMER_SECRET'] = consumer_secret
    c['SECRET_KEY'] = environ.get('SECRET_KEY', consumer_secret)
    c['SQLALCHEMY_DATABASE_URI'] = environ.get('DB_URI', 'sqlite:////data/bom-iae-auth.sqlite')

    # Load optional test_config                     # For automated tests
    if test_config:
        app.config.update(test_config)

    # Initialize Flask extensions
    babel = Babel(app)                              # Initialize Flask-Babel
    db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy
    mail = Mail(app)                                # Initialize Flask-Mail

    @babel.localeselector
    def get_locale():
        translations = [str(translation) for translation in babel.list_translations()]
        return request.accept_languages.best_match(translations)

    # JSON Web Token generator
    def generate_token(user_id):
        return jwt.encode({
          'consumerKey': app.config['CONSUMER_KEY'],
          'userId': user_id,
          'issuedAt': _now().isoformat() + 'Z',
          'ttl': app.config['CONSUMER_TTL']
        }, app.config['CONSUMER_SECRET'])

    def ajax_login_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if app.login_manager._login_disabled:
                return func(*args, **kwargs)
            elif not current_user.is_authenticated():
                return jsonify({'redirect': login_url(url_for('user.login'), request.url)})
            return func(*args, **kwargs)
        return decorated_view

    def _now():
        return datetime.datetime.now(iso8601.iso8601.UTC).replace(microsecond=0)
        # return datetime.datetime.utcnow().replace(microsecond=0)

    # Define User model. Make sure to add flask.ext.user UserMixin!!
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column(db.Boolean(), nullable=False, default=False)
        username = db.Column(db.String(50), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, default='')
        email = db.Column(db.String(255), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime())
        reset_password_token = db.Column(db.String(100), nullable=False, default='')
        annotator_token = db.Column(db.String(100), nullable=True)

    # Create all database tables
    db.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(db,  User)       # Select database adapter
    user_manager = UserManager(db_adapter, app)     # Init Flask-User and bind to app

    # Display Login page or Profile page
    # @app.route('/')
    # def home_page():
    #     if current_user.is_authenticated():
    #         return redirect(url_for('profile_page'))
    #     else:
    #         return redirect(url_for('user.login'))

    # The '/profile' page requires a logged-in user
    @app.route('/user/profile')
    @login_required
    def profile_page():
        return render_template_string("""
            {% extends "base.html" %}
            {% block content %}
                <h2>{% trans %}Profile Page{% endtrans %}</h2>
                <p> {% trans %}Hello{% endtrans %}
                    {{ current_user.username or current_user.email }},</p>
                <p> <a href="{{ url_for('user.change_username') }}">
                    {% trans %}Change username{% endtrans %}</a></p>
                <p> <a href="{{ url_for('user.change_password') }}">
                    {% trans %}Change password{% endtrans %}</a></p>
                <p> <a href="{{ url_for('user.logout') }}?next={{ url_for('user.login') }}">
                    {% trans %}Sign out{% endtrans %}</a></p>
            {% endblock %}
            """)

    # Generate a token for AnnotateIt authentication
    @app.route('/user/token')
    @ajax_login_required
    def get_token():
        return jsonify({'token': generate_token(current_user.id)})

    @app.route('/')
    def send_root():
        return send_from_directory(os.path.join(app.root_path, '..', 'build'), 'index.html')

    @app.route('/<path:filename>')
    def send_static(filename):
        return send_from_directory(os.path.join(app.root_path, '..', 'build'), filename)

    return app

# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
