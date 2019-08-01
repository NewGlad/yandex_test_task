from aiohttp import web
from webargs import fields
from webargs.aiohttpparser import parser, use_args
from marshmallow import Schema, validate
from datetime import datetime
from functools import partial
import json

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
        validate=partial(check_valid_date, date_format='%d.%m.%Y'),
        required=True
        ),
    "gender": fields.Str(
        validate=validate.OneOf(["male", "female"]),
        required=True
    ),
    "relatives": fields.List(
        fields.Int(),
        required=True
    )
}

citizens_list_args = {
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

@use_args(citizens_list_args)
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
                select insert_import_data_to_citizen_info($1, $2, $3, $4, $5, $6, $7, $8);
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
