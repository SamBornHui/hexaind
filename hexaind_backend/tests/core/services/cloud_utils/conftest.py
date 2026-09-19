import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_logger():
    with patch('logging.getLogger'):
        yield 