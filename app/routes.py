from .views import imports
from aiohttp import web
def setup_routes(app):
    app.router.add_route('POST', '/imports', imports.recieve_import_data)
    app.router.add_route('PATCH', '/imports/{import_id:\d+}/citizens/{citizen_id:\d+}', imports.update_citizen_info)
    app.router.add_route('GET', '/imports/{import_id:\d+}/citizens', imports.get_all_citizens)