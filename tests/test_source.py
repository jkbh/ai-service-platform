from conftest import SOURCE_ID


def test_get_sources(client):
    client.login('user2', 'user2')

    response = client.get('/source')

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_post_source(client):
    client.login('user2', 'user2')

    response = client.post(
        '/source', json={'name': 'd4356', 'password': 'source'})

    assert response.status_code == 201
    assert 'public_id' in response.get_json()


def test_delete_source(client):
    client.login('user2', 'user2')

    response = client.delete(f'/source/{SOURCE_ID}')

    assert response.status_code == 200
    assert 'public_id' in response.get_json()

    response = client.delete(f'/source/{SOURCE_ID}')

    assert response.status_code == 404
