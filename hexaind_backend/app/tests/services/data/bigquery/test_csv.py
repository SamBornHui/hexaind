# import unittest
# from unittest.mock import MagicMock
from app.services.data.assets.datasets.service import DatasetsService
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def temp_directories(tmpdir_factory):
    mounted = tmpdir_factory.mktemp("mounted")
    print(type(mounted))
    mounted.join("test.csv")
    (mounted/'test.csv').write("testing")
    return Path(mounted)

def test_list_dir(temp_directories):
    data = DatasetsService.list_directory(temp_directories)
    structure = {
        "name": temp_directories.name,
        "full_path": temp_directories.absolute(),
        "type": "folder",
        "children": [
            {
                "name": "test.csv",
                "full_path": (temp_directories/'test.csv').absolute(),
                "type": "file"
            }
        ]
    }
    assert data==structure
