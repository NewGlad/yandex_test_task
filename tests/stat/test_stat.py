import json
from collections import defaultdict
from datetime import date, timedelta, datetime
import numpy as np
from tests.utils import upload_json_file
from app.handlers.stat import utils

DATE_FORMAT = '%d.%m.%Y'
INVALID_REQUEST_CODE = 400


async def test_stat_counting(test_cli, samples_list):
    for sample_path in samples_list:
        sample_json, import_id = await upload_json_file(sample_path, test_cli)

        age_by_town = defaultdict(list)
        for citizen_dict in sample_json['citizens']:
            town = citizen_dict['town']

            birth_date = datetime.strptime(
                citizen_dict['birth_date'], DATE_FORMAT).date()
            age = utils.calculate_age(birth_date)

            age_by_town[town].append(age)

        required_percentiles = [50, 75, 99]
        expected_result = []
        for town, ages_list in age_by_town.items():
            town_percentiles = {'town': town}
            for item in required_percentiles:
                town_percentiles[f'p{item}'] = np.percentile(
                    ages_list, item, interpolation='linear')
            expected_result.append(town_percentiles)

        response = await test_cli.get(f'/imports/{import_id}/towns/stat/percentile/age', json=sample_json)

        assert response.status == 200
        response_json = await response.json()
        response_json = response_json['data']

        response_json.sort(key=lambda x: x['town'])
        expected_result.sort(key=lambda x: x['town'])

        assert response_json == expected_result


async def test_stat_invalid_import_id(test_cli, samples_list):
    for sample_path in samples_list:
        sample_json, import_id = await upload_json_file(sample_path, test_cli)

        response = await test_cli.get('/imports/123/towns/stat/percentile/age', json=sample_json)

        assert response.status == 400
        response_text = await response.text()

        assert response_text == 'Import with given import_id does not exist'
