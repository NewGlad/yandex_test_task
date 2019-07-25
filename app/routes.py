from .views import imports
def setup_routes(app):
    app.router.add_route('GET', '/', imports)
