from aiohttp import web
from webargs.aiohttpparser import use_args
from app.views.imports.validation import update_citizen_info_args
from app.views.config import config


@use_args(update_citizen_info_args,
    error_status_code=config['invalid_request_http_code']
)
async def update_citizen_info(request, args):
    if len(args) == 0:
        return web.Response(
            status=request.app['config']['invalid_request_http_code'],
            text='Empty data to update'
        )

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
                return web.Response(
                    status=request.app['config']['invalid_request_http_code'],
                    text='Invalid import_id or citizen_id'
                )

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
                relatives = list(set(relatives)) # удаляем возможные дубликаты
                for relative_id in relatives:
                    new_relatives_data.append((citizen_id, import_id, relative_id))
                    if relative_id != citizen_id:
                        # Добавим обратную связь, если id отличаются,
                        # иначе связь человека самим с собой добавилась бы два раза
                        new_relatives_data.append((relative_id, import_id, citizen_id))    
                
                await connection.copy_records_to_table('citizen_relation', records=new_relatives_data)

            # получаем актуальный список родственников
            relatives = await connection.fetch('''
            SELECT relation_id FROM citizen_relation WHERE import_id = $1 AND citizen_id = $2;
            ''', import_id, citizen_id)
            updated_citizen_info['relatives'] = [item[0] for item in relatives]

    response = {
        'data': updated_citizen_info
    }
    return web.json_response(response)