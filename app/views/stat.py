import collections
from aiohttp import web
from datetime import datetime, date, timedelta
import numpy as np
from collections import defaultdict


async def count_percentile(request):
    import_id = int(request.match_info['import_id'])
    async with request.app['db'].acquire() as connection:
        count_recors = await connection.fetch('''
        SELECT count(*) FROM citizen_info WHERE import_id = $1;
        ''', import_id)
        if count_recors[0][0] == 0:
            return web.Response(status=request.app['config']['invalid_request_http_code'], text='Import with given import_id does not exist')
        
        result = await connection.fetch('''
        SELECT town, birth_date FROM citizen_info 
        WHERE import_id = $1;
        ''', import_id)

    ages_in_town = defaultdict(list)
    for item in result:
        town = item['town']
        birth_date = datetime.strptime(item['birth_date'], request.app['config']['birth_date_format']).date()
        
        age = (date.today() - birth_date) // timedelta(days=365.2425)
        ages_in_town[town].append(age)
    
    required_percentiles = [50, 75, 99]
    percentile_by_town = []
    for town, ages_list in ages_in_town.items():
        result = {
            'town': town
        }
        for item in required_percentiles:
            result[f'p{item}'] =np.percentile(ages_list, item, interpolation='linear')
        percentile_by_town.append(result)
    
    return web.json_response({'data': percentile_by_town})