import contextlib
import importlib.util
import inspect
import logging
import os
import sys
import uuid
import zipfile
from pathlib import Path
import pandas as pd

from app.services.workflows.designer.schemas import CustomFunctionAcceptedPythonClasses
from app.utils.file_utils import FileUtils
from app.core.celery.celery_worker import create_celery_app

from app.services.data.assets.modules.schemas import (
    CustomCodeMetadata,
    FunctionArgument,
)

logger = logging.getLogger(__package__)


@contextlib.contextmanager
def sys_path_append(path: Path):
    sys.path.append(str(path))
    yield
    sys.path.remove(str(path))


@contextlib.contextmanager
def change_working_directory(path: Path):
    _oldCWD = os.getcwd()
    os.chdir(str(path.absolute()))
    try:
        yield
    finally:
        os.chdir(_oldCWD)


@contextlib.contextmanager
def redirect_print_to_file(file_path):
    original_stdout = sys.stdout
    with open(file_path, "a") as file:
        sys.stdout = file
        try:
            yield
        finally:
            sys.stdout = original_stdout


@contextlib.contextmanager
def updated_environ(**kwargs):
    _environ = os.environ.copy()
    try:
        os.environ.update(kwargs)
        yield
    finally:
        os.environ.clear()
        os.environ.update(_environ)


def find_files_in_zip(zip_file_path: Path):
    files_in_zip = []
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        files_in_zip = zip_ref.namelist()
    return files_in_zip


def extract_zip_file(source_file: Path, destination_dir: Path) -> None:
    with zipfile.ZipFile(source_file, "r") as zip_ref:
        zip_ref.extractall(destination_dir)


def import_module_from_path(module_path, module_name=None):
    # Check if the file exists
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Module not found: {module_path}")

    # Check if the file is a Python file (.py)
    if not module_path.endswith(".py"):
        raise ValueError(f"Module is not a Python file: {module_path}")

    # Get the directory path and file name
    directory, file_name = os.path.split(module_path)

    # Create a custom module name if not provided
    if module_name is None:
        # Extract the base name (filename) from the full path
        module_name = os.path.basename(module_path)

        # Remove the '.py' extension, if it exists
        if module_name.endswith(".py"):
            module_name = module_name[:-3]

    # Check if the module exists in sys.modules
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])

    # Create a spec for the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)

    # Create the module
    module = importlib.util.module_from_spec(spec)

    # Load the module
    spec.loader.exec_module(module)

    # Return the loaded module
    return module


def function_signature_to_dict(func):
    signature = inspect.signature(func)
    parameters = signature.parameters
    input_params = []

    if len(parameters) < 1:
        logger.error(f"No parameters found for the function {signature}")
        raise ValueError(
            "Desired hexaind_custom_widget_function found, but no parameters found for the function"
        )

    for param_name, param in parameters.items():
        arg_details = FunctionArgument(
            name=str(param_name),
            type=str(param.annotation),
            default_value=str(param.default),
            kind=str(param.kind.name),
        )
        input_params.append(arg_details)

        if (
            arg_details.type != CustomFunctionAcceptedPythonClasses.STRING
            and arg_details.type != CustomFunctionAcceptedPythonClasses.INTEGER
            and arg_details.type != CustomFunctionAcceptedPythonClasses.FLOAT
            and arg_details.type != CustomFunctionAcceptedPythonClasses.PANDAS
            and arg_details.type != CustomFunctionAcceptedPythonClasses.STRINGS_LIST
            and arg_details.type != CustomFunctionAcceptedPythonClasses.FLOATS_LIST
            and arg_details.type != CustomFunctionAcceptedPythonClasses.INTEGERS_LIST
            and arg_details.type != CustomFunctionAcceptedPythonClasses.DICTIONARY
            and arg_details.type != CustomFunctionAcceptedPythonClasses.PATHLIB_PATH
        ):

            logger.error(
                f"Function argument is not in {signature} in {[cfapc.name for cfapc in CustomFunctionAcceptedPythonClasses]}"
            )
            raise ValueError(
                f"Desired hexaind_custom_widget_function found, but function input is invalid {arg_details.type}"
            )

    return_types = []
    if signature.return_annotation is inspect._empty:
        logger.error(f"No return type was found for the function")
        raise ValueError(
            "Desired hexaind_custom_widget_function found, but return type of the function is empty"
        )
    elif isinstance(signature.return_annotation, tuple):
        return_types = [
            str(rvalue) for _, rvalue in enumerate(signature.return_annotation)
        ]
    elif signature.return_annotation is not None:
        return_types = [str(signature.return_annotation)]
    return str(signature), input_params, return_types


def get_function_to_call(file_path: str, function_name: str, base_file_name: str):
    module = import_module_from_path(module_path=file_path)
    if not hasattr(module, function_name):
        raise Exception(
            f"Unable to find {function_name} signature in {base_file_name}."
        )
    return getattr(module, function_name)


def get_pydoc_string(func):
    return inspect.getdoc(func)


def get_metadata_for_python_file(file_path: str, function_name: str, file_names=None):
    base_file_name = Path(file_path).name
    custom_function_to_call = get_function_to_call(
        file_path, function_name, base_file_name
    )
    signature_str, input_details, output_details = function_signature_to_dict(
        custom_function_to_call
    )
    pydoc_string = get_pydoc_string(custom_function_to_call)
    return CustomCodeMetadata(
        file_names=[base_file_name] if file_names is None else file_names,
        function_name=function_name,
        entry_file=base_file_name,
        function_signature=signature_str,
        function_inputs=input_details,
        function_outputs=output_details,
        pydoc_string=pydoc_string,
    )


def extract_zip_in_new_location(file_path: str):
    # extract files to a new folder
    old_destination = Path(file_path)
    new_destination = old_destination.parent / f"{uuid.uuid4()}"
    new_destination = new_destination / f"{old_destination.name.split('.')[0]}"
    extract_zip_file(old_destination, new_destination)  # extract files
    return new_destination


def get_files_from_module_path(file_path: str):
    if file_path.endswith(".py"):
        return [Path(file_path).name]
    elif file_path.endswith(".zip"):
        return find_files_in_zip(Path(file_path))
    raise ValueError(f"Only .py and .zip files are allowed.")


def get_metadata_from_files(python_files, function_name, file_names):
    signatures_found = {}
    exceptions_found = []

    # preference given to main.py
    if "main.py" in python_files:
        try:
            signatures_found["main.py"] = get_metadata_for_python_file(
                "main.py", function_name, file_names
            )

            return signatures_found, exceptions_found
        except Exception as e:
            logger.exception(f"{str(e)}")
            exceptions_found.append(f"Unable to get metadata from main.py: {e}")
        python_files.remove("main.py")

    for python_file in python_files:
        try:
            signatures_found[python_file] = get_metadata_for_python_file(
                python_file, function_name, file_names
            )
        except ValueError as e:
            raise Exception(e.args[0])
        except Exception as e:
            exceptions_found.append(f"Unable to get metadata from {python_file}: {e}")

    return signatures_found, exceptions_found


def get_custom_code_metadata(
    file_path: str, function_name: str
) -> (bool, CustomCodeMetadata):
    if file_path.endswith(".py"):
        return get_metadata_for_python_file(file_path, function_name)
    elif file_path.endswith(".zip"):
        # extract zip to new location
        new_destination = extract_zip_in_new_location(file_path)
        all_python_files_names = [x.name for x in list(new_destination.glob("*.py"))]
        file_names = [x.name for x in list(new_destination.glob("*.*"))]
        if len(all_python_files_names) == 0:
            raise Exception(
                "Make a zip file containing the necessary files(.py + others) without any sub-folders."
            )
        # get metadata from extracted files
        with (
            change_working_directory(new_destination),
            sys_path_append(new_destination),
        ):
            signatures_found, exception_found = get_metadata_from_files(
                all_python_files_names, function_name, file_names
            )
        # remove extracted zip
        FileUtils.remove_path(str(new_destination.parent))

        if len(signatures_found.keys()) != 1:
            logger.error(
                f"Found {len(signatures_found.keys())} instead of 1 signature "
                + f"in files {list(signatures_found.keys())}"
            )
            raise Exception(str(exception_found))

        return list(signatures_found.values())[0]
    else:
        raise Exception("Expecting only .py or .zip files")


def run_custom_code(
    file_path: str, function_name: str, custom_code_metadata: CustomCodeMetadata, kwargs
):
    # create_celery_app(name="random").log.redirect_stdouts(name="app.workers")
    if file_path.endswith(".py"):
        entry_file_name = Path(file_path).name
        custom_function_to_call = get_function_to_call(
            file_path, function_name, entry_file_name
        )
        return custom_function_to_call(**kwargs)  # actual run for python file
    elif file_path.endswith(".zip"):
        new_destination = extract_zip_in_new_location(file_path)  # extract zip to files
        if custom_code_metadata is None or custom_code_metadata.entry_file is None:
            raise Exception(
                f"Missing elements in custom code metadata: {custom_code_metadata}"
            )
        with (
            change_working_directory(new_destination),
            sys_path_append(new_destination),
        ):
            entry_file_name = custom_code_metadata.entry_file
            custom_function_to_call = get_function_to_call(
                entry_file_name, function_name, entry_file_name
            )
            results = custom_function_to_call(
                **kwargs
            )  # actual run for python file in zip file

        FileUtils.remove_path(str(new_destination.parent))  # remove extracted zip files
        return results
    else:
        raise Exception("Entered file_path is neither .py not .zip")


def convert_custom_code_results_to_list(results):
    if results is None:
        return []
    if isinstance(results, tuple):
        return list(results)
    else:
        return [results]
