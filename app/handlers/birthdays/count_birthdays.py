from datetime import datetime
import collections
from aiohttp import web


async def count_birthdays(request):
    import_id = int(request.match_info['import_id'])
    async with request.app['db'].acquire() as connection:
        count_recors = await connection.fetchval('''
        SELECT count(*) FROM citizen_info WHERE import_id = $1;
        ''', import_id)

        if count_recors == 0:
            return web.Response(
                status=request.app['config']['invalid_request_http_code'],
                text='Import with given import_id does not exist'
            )

        result = await connection.fetch('''
            WITH relatives_ids AS (
                SELECT t1.citizen_id, t2.relation_id, t1.import_id
                FROM citizen_info t1 JOIN citizen_relation t2
                ON t1.import_id = t2.import_id AND t1.citizen_id = t2.citizen_id
                WHERE t1.import_id = $1
            )

            SELECT relatives_ids.citizen_id, citizen_info.birth_date FROM relatives_ids
            JOIN citizen_info
            ON relatives_ids.relation_id = citizen_info.citizen_id AND relatives_ids.import_id = citizen_info.import_id;
            ''', import_id)

        response = {str(month): [] for month in range(1, 12 + 1)}
        for item in result:
            citizen_id = item['citizen_id']
            birth_date = item['birth_date']
            month = str(
                datetime.strptime(
                    birth_date,
                    request.app['config']['birth_date_format']).month)
            response[month].append(citizen_id)

        for month, month_array in response.items():
            response[month] = [{'citizen_id': citizen_id, 'presents': presents}
                               for citizen_id, presents in collections.Counter(month_array).items()]

        return web.json_response({'data': response})
