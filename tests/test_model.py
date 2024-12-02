def test_get_all_models(client):
    client.login('user1', 'user1')

    response = client.get('/model')
    assert isinstance(response.get_json(), list)
