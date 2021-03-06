from aiohttp import web
from asyncpg.exceptions import UniqueViolationError
from webargs.aiohttpparser import use_args
from app.handlers.config import config
from app.handlers.imports.utils import check_relatives
from app.handlers.imports.validation import recieve_import_data_args


@use_args(
    recieve_import_data_args,
    error_status_code=config['invalid_request_http_code']
)
async def recieve_import_data(request, args):
    relatives = {}
    citizens_list = args['citizens']
    if len(citizens_list) == 0:
        return web.json_response(
            text='List of citizens cannot be empty!',
            status=request.app['config']['invalid_request_http_code']
        )

    for citizen in citizens_list:
        relatives[int(citizen['citizen_id'])] = citizen['relatives']

    relatives_is_correct = check_relatives(relatives)
    if not relatives_is_correct:
        return web.Response(
            status=request.app['config']['invalid_request_http_code'],
            text='Relatives between citizens is not correct'
        )

    town, street, building, apartment, name, birth_date, gender, citizen_id = zip(
        *[
            (
                item['town'],
                item['street'],
                item['building'],
                item['apartment'],
                item['name'],
                item['birth_date'],
                item['gender'],
                item['citizen_id']
            )
            for item in citizens_list
        ]
    )
    citizen_ids_set = set(citizen_id)
    relatives_ids_set = set()
    for relatives_list in relatives.values():
        relatives_ids_set.union(set(relatives_list))
    
    
    all_citizen_ids_unique = len(list(citizen_ids_set)) == len(citizen_id)
    all_relatives_ids_in_citizen_ids_set = citizen_ids_set.issuperset(relatives_ids_set)
    if not (all_citizen_ids_unique and all_relatives_ids_in_citizen_ids_set):
        return web.Response(
            status=request.app['config']['invalid_request_http_code'],
            text='Citizen identifiers invalid'
        )

    data = [
        town,
        street,
        building,
        apartment,
        name,
        birth_date,
        gender,
        citizen_id]

    async with request.app['db'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchval('''
                SELECT insert_import_data_to_citizen_info($1, $2, $3, $4, $5, $6, $7, $8);
                ''', *data)

            current_import_id = result
            relatives_data = []
            for citizen_id, relatives_list in relatives.items():
                # удаление возможных дубликатов
                relatives_list = list(set(relatives_list))
                for relative_id in relatives_list:
                    relatives_data.append(
                        (citizen_id, current_import_id, relative_id)
                    )

            await connection.copy_records_to_table(
                'citizen_relation', records=relatives_data)


    response = {
        'data': {
            'import_id': current_import_id
        }
    }

    return web.json_response(response, status=201)
