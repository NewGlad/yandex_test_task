import json
import os
import random
import copy
from tests.utils import upload_json_file


async def test_upload_import(test_cli, samples_list):
    '''
        Загрузка данных, проверка полученного import_id
    '''
    for expected_import_id, sample_path in enumerate(samples_list, 1):
        sample_json, import_id = await upload_json_file(sample_path, test_cli)
        assert import_id == expected_import_id


async def test_upload_missing_data(test_cli):
    '''
        Обращение к обработчику без данных, проверка статуса 400
    '''
    # Если не задаем данные вообще
    response = await test_cli.post('/imports')
    assert response.status == 400

    # Если задаем пустой список
    response = await test_cli.post('/imports', json={'citizens': []})
    assert response.status == 400
    response_text = await response.text()
    assert response_text == 'List of citizens cannot be empty!'


async def test_upload_import_incorrect_relatives(test_cli, one_citizen_sample):
    '''
        Загрузка данных с неправильным списком родственников, проверка статуса 400
    '''
    sample_json, import_id = await upload_json_file(one_citizen_sample, test_cli)

    citizen = sample_json['citizens'][0]
    citizen['relatives'].append(123)
    response = await test_cli.post('/imports', json=sample_json)
    assert response.status == 400


async def test_upload_import_missing_field(test_cli, one_citizen_sample):
    '''
        Загрузка данных с пропущенными полями, проверка статуса 400
    '''
    sample_json, import_id = await upload_json_file(one_citizen_sample, test_cli)
    citizen = sample_json['citizens'][0]
    for key in citizen.keys():
        broken_citizen = copy.deepcopy(citizen)
        broken_citizen.pop(key)
        broken_request = {'citizens': [broken_citizen]}
        response = await test_cli.post('/imports', json=broken_request)
        assert response.status == 400


async def test_download_consistency(test_cli, samples_list):
    '''
        Загрузка данных, проверка эквивалентности загруженного и возвращенного из сервиса
    '''
    for sample_path in samples_list:
        sample_json, import_id = await upload_json_file(sample_path, test_cli)

        get_response = await test_cli.get(f'/imports/{import_id}/citizens')
        get_response_json = await get_response.json()
        get_response_content = get_response_json['data']

        for item_dict in sample_json['citizens']:
            item_dict['relatives'].sort()
        for item_dict in get_response_content:
            item_dict['relatives'].sort()
        # Записи возвращаются в произвольном порядке, отсортируем для
        # корректного сравнения
        get_response_content.sort(key=lambda value: value['citizen_id'])
        assert get_response_content == sample_json['citizens']


async def test_download_invalid_import_id(test_cli, samples_list):
    '''
        Обращение к сервису с несуществующим import_id, проверка статуса 400
    '''
    get_response = await test_cli.get('/imports/123/citizens')
    assert get_response.status == 400
    get_response_text = await get_response.text()
    assert get_response_text == 'Import with given id does not exist'


async def test_patch(test_cli, samples_list):
    '''
        Загрузка данных, изменение случайных полей на случайные значения, проверка
    '''
    for sample_path in samples_list:
        sample_json, import_id = await upload_json_file(sample_path, test_cli)

        import datetime
        import numpy as np

        def get_random_date():
            return datetime.date(
                random.randint(
                    1960, 2019), random.randint(
                    1, 12), random.randint(
                    1, 28)).strftime("%d.%m.%Y")

        def generate_relatives_list():
            result = []
            relatives_amount = random.randint(0, 10)
            for _ in range(relatives_amount):
                result.append(random.randint(1, len(sample_json['citizens'])))
            return sorted(result)

        changes_map = {
            'name': lambda: random.choice(['Иван', 'Алексей', "Варвара", "Юлия"]),
            'gender': lambda: random.choice(['male', 'female']),
            'town': lambda: random.choice(["Москва", 'Пермь', "Омск"]),
            'street': lambda: random.choice(["Ленина", "Дедюкина", "Борчанинова"]),
            'building': lambda: f'{random.randint(1, 100)}к{random.randint(1, 100)}стр{random.randint(1, 100)}',
            'apartment': lambda: random.randint(1, 100),
            'relatives': generate_relatives_list,
            'birth_date': get_random_date
        }

        citizens_patch_amount = random.randint(
            0, min(len(sample_json['citizens']), 10))

        for _ in range(citizens_patch_amount):
            random_citizen = random.choice(sample_json['citizens'])
            citizen_id = random_citizen.pop('citizen_id')

            for field, function in changes_map.items():
                assert callable(function), changes_map
                if random.random() < 0.7:
                    # с некоторым шансом пропускаем изменение поля
                    continue
                random_citizen[field] = function()

            patch_response = await test_cli.patch(f'/imports/{import_id}/citizens/{citizen_id}', json=random_citizen)

            assert patch_response.status == 200, await patch_response.text()

            random_citizen['citizen_id'] = citizen_id
            patch_response_json = await patch_response.json()
            patch_response_json['data']['relatives'].sort()

            random_citizen['citizen_id'] = citizen_id
            random_citizen['relatives'] = sorted(
                list(set(random_citizen['relatives'])))
            assert patch_response_json['data'] == random_citizen


async def test_patch_missing_field(test_cli, one_citizen_sample):
    '''
        Запрос на изменение с пустым телом, проверка статуса 400
    '''

    sample_json, import_id = await upload_json_file(one_citizen_sample, test_cli)
    citizen_id = sample_json['citizens'][0]['citizen_id']
    empty_patch_request = {}

    patch_response = await test_cli.patch(f'/imports/{import_id}/citizens/{citizen_id}', json=empty_patch_request)

    assert patch_response.status == 400
    patch_response_text = await patch_response.text()
    assert patch_response_text == 'Empty data to update'


async def test_patch_wrong_url(test_cli, one_citizen_sample):
    '''
        Запрос на изменение с несуществующими import_id или citizen_id, проверка статуса 400
    '''

    sample_json, import_id = await upload_json_file(one_citizen_sample, test_cli)

    # неправильный import_id
    patch_response = await test_cli.patch(f'/imports/{3}/citizens/{1}', json={'name': 'hello'})
    assert patch_response.status == 400
    assert await patch_response.text() == 'Invalid import_id or citizen_id'

    # неправильный citizen_id
    patch_response = await test_cli.patch(f'/imports/{1}/citizens/{2}', json={'name': 'hello'})
    assert patch_response.status == 400
    assert await patch_response.text() == 'Invalid import_id or citizen_id'

    # неправильный import_id и citizen_id
    patch_response = await test_cli.patch(f'/imports/{10}/citizens/{2}', json={'name': 'hello'})
    assert patch_response.status == 400
    assert await patch_response.text() == 'Invalid import_id or citizen_id'


async def test_patch_non_existing_relative(test_cli, one_citizen_sample):
    '''
        Изменение данных гражданина с несуществующим relative_id в списке родственников
    '''
    sample_json, import_id = await upload_json_file(one_citizen_sample, test_cli)
    patch_response = await test_cli.patch(f'/imports/{import_id}/citizens/1',
        json={
            'name': 'Hello World',
            'relatives': [2,3]
        }
    )

    assert patch_response.status == 400
    assert await patch_response.text() == 'Invalid relatives list'


async def test_import_non_unique_citizen_id(test_cli, one_citizen_sample):
    '''
        Добавление записей с неуникальными citizen_id
    '''
    with open(one_citizen_sample) as f:
        data = json.load(f)
    data['citizens'].append(data['citizens'][0])

    response = await test_cli.post('/imports', json=data)

    assert response.status == 400
    assert await response.text() == 'Citizen identifiers invalid'


async def test_import_wrong_date_format(test_cli, one_citizen_sample):
    '''
        Добавление записей с неправильно отформатированным временем
    '''
    with open(one_citizen_sample) as f:
        data = json.load(f)

    wrong_samples = [
        '24-02-1996',
        '29.02.1995', # не високосный год
        '1 АПР 1865',
    ]

    for sample in wrong_samples:
        data['citizens'][0]['birth_date'] = sample
        response = await test_cli.post('/imports', json=data)
        assert response.status == 400
