from fastapi.testclient import TestClient


def test_test_endpoint(test_client: TestClient) -> None:
    response = test_client.get("/test/test")
    assert response.status_code == 200
    assert response.json() == {"response": "hello world"}
