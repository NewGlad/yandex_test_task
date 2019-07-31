from .views import imports
from aiohttp import web
def setup_routes(app):
    app.router.add_route('POST', '/', imports.imports)
