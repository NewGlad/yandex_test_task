from aiohttp import web
from webargs.aiohttpparser import use_args
from app.handlers.imports.validation import update_citizen_info_args
from app.handlers.config import config


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
            keys = list(args.keys())
            base_query = "UPDATE citizen_info SET "
            base_query += ", ".join([f"{key} = ${idx}" for idx, key in enumerate(keys, 1)])
            base_query += f'WHERE import_id = ${len(keys) + 1} AND citizen_id = ${len(keys) + 2} RETURNING *'
            result = await connection.fetchrow(base_query, *[args[k] for k in keys], import_id, citizen_id)
            if result is None:
                return web.Response(
                    status=request.app['config']['invalid_request_http_code'],
                    text='Invalid import_id or citizen_id'
                )
            updated_citizen_info = dict(result)
            updated_citizen_info.pop('import_id')
            if relatives is not None:
                # Если заданы родственники - удалить старые данные из базы и
                # заполнить новыми
                await connection.execute('''
                DELETE FROM citizen_relation WHERE
                import_id = $1 AND (relation_id = $2 OR citizen_id = $2);
                ''', import_id, citizen_id)

                #  citizen_id | import_id | relation_id
                new_relatives_data = []
                relatives = list(set(relatives))  # удаляем возможные дубликаты
                for relative_id in relatives:
                    new_relatives_data.append(
                        (citizen_id, import_id, relative_id))
                    if relative_id != citizen_id:
                        # Добавим обратную связь, если id отличаются,
                        # иначе связь человека самим с собой добавилась бы два
                        # раза
                        new_relatives_data.append(
                            (relative_id, import_id, citizen_id))

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
