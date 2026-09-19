import uuid

import pytest
import tempfile
import shutil
import zipfile
import pandas
import os
from pathlib import Path
from app.services.data.assets.modules.utils import (
    find_files_in_zip, extract_zip_file, import_module_from_path, function_signature_to_dict,
    get_function_to_call, get_metadata_for_python_file, extract_zip_in_new_location, get_files_from_module_path,
    get_metadata_from_files, get_custom_code_metadata, run_custom_code, convert_custom_code_results_to_list
)


@pytest.fixture(scope="module")
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def create_zip_file(zip_file_path, file_list):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file_name in file_list:
            zipf.write(file_name)


def test_find_files_in_zip(temp_dir):
    files_to_zip = [str(Path(__file__).parent.parent.parent.parent.parent / "resources/input1.csv"),
                    str(Path(__file__).parent.parent.parent.parent.parent / "resources/input2.csv"),
                    str(Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv")]
    zip_file_path = os.path.join(temp_dir, 'test.zip')
    create_zip_file(zip_file_path, files_to_zip)
    files_in_zip = find_files_in_zip(Path(zip_file_path))
    assert len(files_in_zip) == len(files_to_zip)


def test_extract_zip_file(temp_dir):
    files_to_zip = [str(Path(__file__).parent.parent.parent.parent.parent / "resources/input1.csv"),
                    str(Path(__file__).parent.parent.parent.parent.parent / "resources/input2.csv"),
                    str(Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv")]
    zip_file_path = os.path.join(temp_dir, 'test.zip')
    create_zip_file(zip_file_path, files_to_zip)

    extraction_dir = os.path.join(temp_dir, 'extracted')
    extract_zip_file(Path(zip_file_path), Path(extraction_dir))

    for i in range(3):
        assert os.path.exists(os.path.join(extraction_dir, files_to_zip[i]))


def test_import_module_from_path(temp_dir):
    module_file = os.path.join(temp_dir, 'test_module.py')
    with open(module_file, 'w') as f:
        f.write('def my_function():\n    return "Hello, World!"')

    full_module_path = f"{__package__}.test_module"
    test_module = import_module_from_path(module_file, full_module_path)
    assert hasattr(test_module, 'my_function')
    assert callable(test_module.my_function)
    assert test_module.my_function() == 'Hello, World!'

def test_function_signature_to_dict():
    def test_function(arg1: str, arg2: str="default") -> str:
        return ''

    signature, input_params, return_types = function_signature_to_dict(test_function)
    assert signature == "(arg1: str, arg2: str = 'default') -> str"
    assert len(input_params) == 2
    assert input_params[0].name == "arg1"
    assert input_params[1].name == "arg2"
    assert input_params[0].type == "<class 'str'>"
    assert input_params[0].kind == "POSITIONAL_OR_KEYWORD"
    assert input_params[1].default_value == "default"
    assert return_types == ["<class 'str'>"]


def test_get_function_to_call():
    curr_dir = Path(__file__).resolve().parent
    module_file = os.path.join(curr_dir, f'test_module_{uuid.uuid4()}.py')
    with open(module_file, 'w') as f:
        f.write('def my_function():\n    return "Hello, World!"')
    full_module_path = f"{__package__}.test_module"
    test_module = import_module_from_path(module_file, full_module_path)

    function_to_call = get_function_to_call(module_file, 'my_function', 'test_module')
    os.remove(module_file)
    assert function_to_call() == test_module.my_function()


def test_get_metadata_for_python_file(temp_dir):
    curr_dir = Path(__file__).resolve().parent
    module_file = os.path.join(curr_dir, f'test_module_{uuid.uuid4()}.py')
    with open(module_file, 'w') as f:
        f.write('import pandas as pd\ndef my_function(a: pd.DataFrame, b:str) -> str:\n    return "Hello, World!"')

    metadata = get_metadata_for_python_file(module_file, 'my_function')
    os.remove(module_file)
    file_name = Path(module_file).name
    assert metadata.file_names == [file_name]
    assert metadata.entry_file == file_name
    assert metadata.function_signature == "(a: pandas.core.frame.DataFrame, b: str) -> str"
    assert len(metadata.function_inputs) == 2
    assert len(metadata.function_outputs) == 1


def test_extract_zip_in_new_location(temp_dir):
    files_to_zip = [str(Path(__file__).parent.parent.parent.parent.parent / "resources/input1.csv"),
                    str(Path(__file__).parent.parent.parent.parent.parent / "resources/input2.csv")]
    zip_file_path = os.path.join(temp_dir, 'test.zip')
    create_zip_file(zip_file_path, files_to_zip)
    new_destination = extract_zip_in_new_location(zip_file_path)
    assert os.path.exists(new_destination)
    assert os.path.isdir(new_destination)
    count = 0
    for _, _, files in os.walk(new_destination):
        count += len(files)
    assert count == len(files_to_zip)


def test_get_files_from_module_path():
    python_file_path = 'test_module.py'
    assert get_files_from_module_path(python_file_path) == ['test_module.py']


def test_get_metadata_from_files(temp_dir):
    signatures_found, exceptions_found = get_metadata_from_files(
        [str(Path(__file__).parent.parent.parent.parent.parent / "resources/test_module.py")],
        'hexaind_custom_widget_function', ['test_module.py'])
    assert len(signatures_found) == 1
    assert len(exceptions_found) == 0


def test_get_custom_code_metadata(temp_dir):
    curr_dir = Path(__file__).resolve().parent
    module_file = os.path.join(curr_dir, f'test_module_{uuid.uuid4()}.py')

    with open(module_file, 'w') as f:
        f.write('def my_function(a: str) -> str:\n    return "Hello, World!"')

    metadata = get_custom_code_metadata(module_file, 'my_function')
    os.remove(module_file)
    file_name = Path(module_file).name
    assert metadata.file_names == [file_name]
    assert metadata.entry_file == file_name
    assert metadata.function_signature == "(a: str) -> str"
    assert len(metadata.function_inputs) == 1
    assert len(metadata.function_outputs) == 1


def test_run_custom_code_python(temp_dir):
    curr_dir = Path(__file__).resolve().parent
    module_file = os.path.join(curr_dir, f'test_module_{uuid.uuid4()}.py')

    with open(module_file, 'w') as f:
        f.write('def my_function(value):\n    return value * 2')

    results = run_custom_code(module_file, 'my_function', None, {'value': 5})
    os.remove(module_file)
    assert results == 10


def test_run_custom_code_zip(temp_dir):
    join_module_zipfile = str(Path(__file__).parent.parent.parent.parent.parent / "resources/join_module.zip")
    metadata = get_custom_code_metadata(join_module_zipfile, "hexaind_custom_widget_function")
    kwargs = {
        "df1": pandas.read_csv(str(Path(__file__).parent.parent.parent.parent.parent / "resources/input1.csv")),
        "df2": pandas.read_csv(str(Path(__file__).parent.parent.parent.parent.parent / "resources/input2.csv")),
        "column_names": "ID",
        "how": "inner"
    }
    results = run_custom_code(join_module_zipfile, 'hexaind_custom_widget_function', metadata, kwargs)
    results = convert_custom_code_results_to_list(results)
    expected_output = pandas.read_csv(str(Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv"))
    assert all(results[0] == expected_output)


def test_convert_custom_code_results_to_list():
    assert convert_custom_code_results_to_list(None) == []
    assert convert_custom_code_results_to_list(5) == [5]
    assert convert_custom_code_results_to_list((1, 2, 3)) == [1, 2, 3]
    assert convert_custom_code_results_to_list([1, 2, 3]) == [[1, 2, 3]]
