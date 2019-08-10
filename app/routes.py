from app.views import imports, birthdays, stat
def setup_routes(app):
    app.router.add_route('POST', '/imports', imports.recieve_import_data)
    app.router.add_route('PATCH', '/imports/{import_id:\d+}/citizens/{citizen_id:\d+}', imports.update_citizen_info)
    app.router.add_route('GET', '/imports/{import_id:\d+}/citizens', imports.get_all_citizens)
    app.router.add_route("GET", '/imports/{import_id:\d+}/citizens/birthdays', birthdays.count_birthdays)
    app.router.add_route("GET", "/imports/{import_id:\d+}/towns/stat/percentile/age", stat.count_percentile)