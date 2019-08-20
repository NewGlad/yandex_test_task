import json


async def upload_json_file(filepath, test_cli):
    with open(filepath, 'r') as f:
        sample_json = json.load(f)

    response = await test_cli.post('/imports', json=sample_json)
    assert response.status == 201
    response_json = await response.json()
    import_id = response_json['data']['import_id']

    return sample_json, import_id
