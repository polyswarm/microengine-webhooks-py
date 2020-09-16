
@pytest.fixture
def client():
    return application.test_client()
