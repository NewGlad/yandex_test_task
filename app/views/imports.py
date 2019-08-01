from aiohttp import web
from webargs import fields
from webargs.aiohttpparser import parser, use_args
from marshmallow import Schema, validate
from datetime import datetime
from functools import partial
import json
import asyncpg


DATE_FORMAT = '%d.%m.%Y'
VALID_GENDER_LIST = ["male", "female"]


def check_valid_date(value, date_format):
    try:
        datetime.strptime(value, date_format)
        return True
    except ValueError:
        return False

citizen_info = {
    "citizen_id": fields.Int(required=True),
    "town": fields.Str(required=True),
    "street": fields.Str(required=True),
    "building": fields.Str(required=True),
    "apartment": fields.Int(required=True),
    "name": fields.Str(required=True),
    "birth_date": fields.Str(
        validate=partial(check_valid_date, date_format=DATE_FORMAT),
        required=True
        ),
    "gender": fields.Str(
        validate=validate.OneOf(VALID_GENDER_LIST),
        required=True
    ),
    "relatives": fields.List(
        fields.Int(),
        required=True
    )
}

recieve_import_data_args = {
    "citizens" : fields.List(
        fields.Nested(citizen_info, required=True),
        required=True
    )
}

def check_relatives(relatives: dict):
    for citizen in relatives:
        relatives_list = relatives[citizen]
        for item in relatives_list:
            if item not in relatives or citizen not in relatives[item]:
                return False
    return True

@use_args(recieve_import_data_args)
async def recieve_import_data(request, args):
    relatives = {}
    citizens_list = args['citizens'] 
    for citizen in citizens_list:
        relatives[int(citizen['citizen_id'])] = citizen['relatives']
    
    relatives_is_correct = check_relatives(relatives)
    if not relatives_is_correct:
        return web.Response(status=400, text='Relatives between citizens is not correct')
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
    
    data = [town, street, building, apartment, name, birth_date, gender, citizen_id]
    
    async with request.app['db'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetch('''
                SELECT insert_import_data_to_citizen_info($1, $2, $3, $4, $5, $6, $7, $8);
                ''', *data
            )
            current_import_id = result[0][0]
            relatives_data = []
            for citizen_id, relatives_list in relatives.items():
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


update_citizen_info_args = {
    "town": fields.Str(),
    "street": fields.Str(),
    "building": fields.Str(),
    "apartment": fields.Int(),
    "name": fields.Str(),
    "birth_date": fields.Str(
        validate=partial(check_valid_date, date_format=DATE_FORMAT)
        ),
    "gender": fields.Str(
        validate=validate.OneOf(VALID_GENDER_LIST)
    ),
    "relatives": fields.List(
        fields.Int()
    )
}

@use_args(update_citizen_info_args)
async def update_citizen_info(request, args):
    if len(args) == 0:
        return web.Response(status=400, text='Empty data to update')

    import_id = int(request.match_info['import_id'])
    citizen_id = int(request.match_info['citizen_id'])
    relatives = args.pop('relatives', None)
    
    async with request.app['db'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetch('''
                SELECT name, gender, birth_date, town, street,
                building, apartment, citizen_id
                FROM citizen_info WHERE import_id = $1 AND citizen_id = $2;
                ''', import_id, citizen_id)
            
            try:
                citizen_info = dict(result[0])
            except IndexError:
                # В случае, если result это пустой список, т.е. ничего не нашлось в базе
                return web.Response(status=400, text='Invalid import_id or citizen_id')

            updated_citizen_info = {**citizen_info, **args}
            await connection.execute('''
            UPDATE citizen_info SET name = $1, gender = $2, birth_date = $3,
            town = $4, street = $5, building = $6, apartment = $7
            WHERE citizen_id = $8 AND import_id = $9;
            ''',
            updated_citizen_info['name'],
            updated_citizen_info['gender'],
            updated_citizen_info['birth_date'],
            updated_citizen_info['town'],
            updated_citizen_info['street'],
            updated_citizen_info['building'],
            updated_citizen_info['apartment'],
            citizen_id,
            import_id
            )

            if relatives is not None:
                # Если заданы родственники - удалить старые данные из базы и заполнить новыми
                await connection.execute('''
                DELETE FROM citizen_relation WHERE 
                import_id = $1 AND (relation_id = $2 OR citizen_id = $2);
                ''', import_id, citizen_id)
            
                #  citizen_id | import_id | relation_id
                new_relatives_data = []
                for relative_id in relatives:
                    new_relatives_data.append((citizen_id, import_id, relative_id))
                    if relative_id != citizen_id:
                        # Добавим обратную связь, если id отличаются,
                        # иначе связь человека самим с собой добавилась бы два раза
                        new_relatives_data.append((relative_id, import_id, citizen_id))    
                try:
                    await connection.copy_records_to_table('citizen_relation', records=new_relatives_data)
                except asyncpg.exceptions.ForeignKeyViolationError:
                    return web.Response(status=400, text='Invalid relatives list')

            # получаем актуальный список родственников
            relatives = await connection.fetch('''
            SELECT relation_id FROM citizen_relation WHERE import_id = $1 AND citizen_id = $2;
            ''', import_id, citizen_id)
            updated_citizen_info['relatives'] = [item[0] for item in relatives]

    return web.json_response(updated_citizen_info)