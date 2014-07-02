from setuptools import setup, find_packages

setup(
    name = 'annotate-auth',
    version = '0.1',
    packages = find_packages(),

    install_requires = [
        'Flask==0.9',
        'Flask-Mail==0.7.2',
        'Flask-SQLAlchemy==0.16',
        'Flask-WTF==0.8',
        'Flask-User==0.5.0',
        'Flask-Babel',
        'SQLAlchemy==0.7.8',
        'sqlalchemy-migrate==0.7.2',
        'decorator==3.3.3',
        'iso8601==0.1.4',
        'PyJWT==0.1.4',
        'itsdangerous'
    ],
)
