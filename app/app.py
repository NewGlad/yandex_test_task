import asyncpgsa
from aiohttp import web
from .routes import setup_routes


def create_app(config: dict):
    app = web.Application(client_max_size=1024**3)
    app['config'] = config
    setup_routes(app)
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_shutdown)
    return app


async def on_start(app):
    config = app['config']
    app['db'] = await asyncpgsa.create_pool(
        dsn=config['database_uri'],
        min_size=config['database_connection_amount'],
        max_size=config['database_connection_amount'],
        max_inactive_connection_lifetime=0

    )


async def on_shutdown(app):
    await app['db'].close()
