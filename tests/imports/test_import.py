import json

async def test_health_check_on(test_cli):
    resp = await test_cli.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert text == 'Privetik :)'
