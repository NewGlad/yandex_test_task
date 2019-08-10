from collections import defaultdict
from aiohttp import web


async def get_all_citizens(request):
    import_id = int(request.match_info['import_id'])
    async with request.app['db'].acquire() as connection:
        result = await connection.fetch('''
        SELECT town, street, building, apartment, name, birth_date, gender, citizen_id
        FROM citizen_info WHERE import_id = $1;
        ''', import_id)
        if len(result) == 0:
            return web.Response(
                status=request.app['config']['invalid_request_http_code'],
                text='Import with given id does not exist'
            )

        result = [dict(result_item) for result_item in result]

        relatives = await connection.fetch('''
        SELECT citizen_id, relation_id FROM citizen_relation WHERE import_id = $1;
        ''', import_id)

        relatives_dict = defaultdict(list)
        for item in relatives:
            relatives_dict[item['citizen_id']].append(item['relation_id'])

        for citizen_info_dict in result:
            citizen_id = citizen_info_dict['citizen_id']
            relatives_list = relatives_dict.get(citizen_id, [])
            citizen_info_dict['relatives'] = relatives_list

        response = {
            'data': result
        }
    return web.json_response(response)
