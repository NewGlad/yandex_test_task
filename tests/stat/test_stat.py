import json
from collections import defaultdict
from datetime import date, timedelta, datetime
import numpy as np
DATE_FORMAT = '%d.%m.%Y'
INVALID_REQUEST_CODE = 400



async def test_stat_counting(test_cli, samples_list):
    for import_id, sample_path in enumerate(samples_list, 1):
        with open(sample_path, 'r') as f:
            sample_json = json.load(f)

        response = await test_cli.post('/imports', json=sample_json)
        assert response.status == 201
        response_json = await response.json()
        import_id = response_json['data']['import_id']
        

        age_by_town = defaultdict(list)
        for citizen_dict in sample_json['citizens']:
            town = citizen_dict['town']
            
            birth_date = datetime.strptime(citizen_dict['birth_date'], DATE_FORMAT).date()
            age = (date.today() - birth_date) // timedelta(days=365.2425)
            
            age_by_town[town].append(age)

            
        required_percentiles = [50, 75, 99]
        expected_result = []
        for town, ages_list in age_by_town.items():
            town_percentiles = {'town': town}
            for item in required_percentiles:
                town_percentiles[f'p{item}'] =np.percentile(ages_list, item, interpolation='linear')
            expected_result.append(town_percentiles)
        
        
        response = await test_cli.get(f'/imports/{import_id}/towns/stat/percentile/age', json=sample_json)
        

        assert response.status == 200
        response_json = await response.json()
        response_json = response_json['data']
        
        response_json.sort(key=lambda x: x['town'])
        expected_result.sort(key=lambda x: x['town'])

        assert response_json == expected_result


async def test_stat_invalid_import_id(test_cli, samples_list):
    for import_id, sample_path in enumerate(samples_list, 1):
        with open(sample_path, 'r') as f:
            sample_json = json.load(f)

        response = await test_cli.post('/imports', json=sample_json)
        assert response.status == 201
        response_json = await response.json()
        import_id = response_json['data']['import_id']
        

        response = await test_cli.get('/imports/123/towns/stat/percentile/age', json=sample_json)
        

        assert response.status == 400
        response_text = await response.text()
        
        assert response_text == 'Import with given import_id does not exist'