import json
from datetime import datetime
import collections
from tests.utils import upload_json_file

DATE_FORMAT = '%d.%m.%Y'


async def test_birthdays_count(test_cli, samples_list):
    '''
        Загрузка данных, проверка корректности подсчёта подарков
    '''
    for sample_path in samples_list:
        sample_json, import_id = await upload_json_file(sample_path, test_cli)

        citizen_by_month = {str(month): [] for month in range(1, 12 + 1)}
        for citizen_dict in sample_json['citizens']:
            month = str(
                datetime.strptime(
                    citizen_dict['birth_date'],
                    DATE_FORMAT).month)
            citizen_by_month[month].append(citizen_dict)

        expected_result = {}
        for month, citizens_list in citizen_by_month.items():
            expected_result[month] = []
            for citizen_dict in citizens_list:
                expected_result[month] += citizen_dict['relatives']

        for month in expected_result.keys():
            expected_result[month] = [
                {
                    'citizen_id': citizen_id,
                    'presents': presents} for citizen_id,
                presents in collections.Counter(
                    expected_result[month]).items()]

        # сортировка значений в ожидаемом результате
        for key in expected_result.keys():
            expected_result[key] = sorted(
                expected_result[key], key=lambda x: x['citizen_id'])
        expected_result = dict(sorted(expected_result.items()))

        response = await test_cli.get(f'/imports/{import_id}/citizens/birthdays', json=sample_json)

        # сортировка значений в полученном ответе
        response_json = await response.json()
        response_json = response_json['data']
        for key in response_json.keys():
            response_json[key] = sorted(
                response_json[key], key=lambda x: x['citizen_id'])
        response_json = dict(sorted(response_json.items()))

        assert response.status == 200
        assert response_json == expected_result


async def test_birthdays_count_invalid_import_id(test_cli, one_citizen_sample):
    '''
        Проверка кода 400 при несуществующем import_id
    '''
    sample_json, import_id = await upload_json_file(one_citizen_sample, test_cli)

    response = await test_cli.get(f'/imports/123/citizens/birthdays')

    assert response.status == 400
    assert await response.text() == 'Import with given import_id does not exist'
