import os, shutil, json, time
from pathlib import Path
import pandas as pd
import mimetypes
import difflib

class FileUtils:

    @staticmethod
    def is_file_exist(file_path: str) -> bool:
        return os.path.exists(file_path)

    @staticmethod
    def SaveTabularFileToDisk(
        data: pd.DataFrame, destination_path: str = ""
    ):  # TODO This is for temporary, able to save any kind of tabular data(pandas, rdd, parquet, etc)
        """
        util function for saving the data to disk
        NOTE: able to save any kind of tabular data(pandas, rdd, parquet, etc), but for now accepting only pandas as source data
        """
        try:
            if data is None or type(data) != pd.DataFrame:
                raise Exception(f"SaveTabularFileToDisk is expecting pandas data. But got: {type(data)}")

            if not destination_path or (not destination_path.endswith(".csv")):
                raise Exception(f"No destination path provided to save the data or provided path not ends with .csv")

            if FileUtils.is_file_exist(destination_path):
                raise Exception(
                    f"Trying to save the data at {destination_path}. But already file exists at {destination_path}"
                )

            data.to_csv(destination_path, index=False)

        except Exception as e:
            raise Exception(f"File writing failed: {e}")

    @staticmethod
    def create_deep_copy_file_or_folder(source_path: str, dest_path: str, dirs_exist_ok: bool = False):
        """
        Utility function for creating deep copies of files or directories on disk.
        """
        try:
            # Check if the destination folder exists, create it if it doesn't
            destination_folder = os.path.dirname(dest_path)
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)

            if os.path.isfile(source_path):
                shutil.copyfile(source_path, dest_path)
                if FileUtils.is_file_exist(dest_path) and os.path.getsize(source_path) == os.path.getsize(dest_path):
                    pass
                else:
                    raise Exception("File copy failed: Destination file does not match the source")
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path, dirs_exist_ok=dirs_exist_ok)
                if FileUtils.is_file_exist(dest_path):
                    pass
                else:
                    raise Exception("Directory copy failed: Destination directory does not match the source")
            else:
                raise Exception("Source path is neither a file nor a directory.")
        except FileNotFoundError:
            raise Exception("Copy failed: Source or destination path not found.")
        except PermissionError:
            raise Exception("Copy failed: Permission denied.")
        except Exception as e:
            raise Exception(f"Copy failed: {e}")

    @staticmethod
    def createDeepCopyOfFile(source_file_path: str, dest_file_path: str):
        """
        util function for creating file copies on disk
        """
        try:
            # # Check if the destination folder exists, create it if it doesn't
            destination_folder = os.path.dirname(dest_file_path)

            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)

            # Copy the file
            shutil.copyfile(source_file_path, dest_file_path)

            # Check if the destination file exists and compare sizes
            if FileUtils.is_file_exist(dest_file_path) and os.path.getsize(source_file_path) == os.path.getsize(
                dest_file_path
            ):
                pass
            else:
                raise Exception("File copy failed: Destination file does not match the source")

        except FileNotFoundError:
            raise Exception("File copy failed: Source or destination path not found.")
        except PermissionError:
            raise Exception("File copy failed: Permission denied.")
        except Exception as e:
            raise Exception(f"File copy failed: {e}")

    @staticmethod
    def is_json_serializable(obj):
        """
        This is the helper function to verify the data is compatible to save in json or not
        """
        try:
            json.dumps(obj)
            return True
        except (TypeError, OverflowError):
            return False

    @staticmethod
    def save_to_json(data, dest_file_path: str):

        try:
            # Create the folder if it doesn't exist
            destination_folder = os.path.dirname(dest_file_path)
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)

            # Save the data to the file
            with open(dest_file_path, "w") as file:
                json.dump(data, file, indent=4)

        except Exception as e:
            raise Exception(f"Data copy to json failed: {e}")

    @staticmethod
    def read_from_json(json_file_path: str):
        try:
            if not os.path.exists(json_file_path):
                raise Exception("JSON file path not found.")

            with open(json_file_path, "r") as file:
                json_data = json.load(file)

            return json_data

        except Exception as e:
            raise Exception(f"Data read from json failed: {e}")

    @staticmethod
    def remove_path(file_or_folder_path: str):
        file_path = Path(file_or_folder_path)
        if file_path.exists():
            if file_path.is_file():
                os.remove(file_path)
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                raise Exception(f"{file_path} is neither file not folder.")

    @staticmethod
    def add_timestamp_to_filename(filepath):
        # Split the filepath into directory, base filename, and extension
        dirname, basename = os.path.split(filepath)
        filename, ext = os.path.splitext(basename)

        # Get current time in nanoseconds
        timestamp = time.time_ns()

        # Construct the new filename with the timestamp
        new_filename = f"{filename}_{timestamp}{ext}"
        new_filepath = os.path.join(dirname, new_filename)

        return new_filepath

    @staticmethod
    def is_text_file(filepath) -> bool:

        # get MIME type of the file based on its extension
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type and mime_type.startswith("text"):
            return True

        # Try to open the file and decode it as UTF-8
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                file.read()  # Attempt to read the file
            return True
        except (UnicodeDecodeError, FileNotFoundError):
            return False

    @staticmethod
    def read_file_segment(file_path: str, offset: int, length: int, decode_type: str = 'utf-8') -> str:
        """Generator to read a segment of a file based on file path, starting from a specific offset."""
        with open(file_path,"rb") as file:
            file.seek(offset)
            chunk = file.read(length)
            return chunk.decode(decode_type)

    @staticmethod
    def file_diff(file_path1: str, file_path2: str):

        with open(file_path1, 'r') as file1, open(file_path2, 'r') as file2:
            # file1_lines = file1.readlines()
            # file2_lines = file2.readlines()
            # differ = difflib.Differ() # TODO: check if creating single differ instance may speed up performance
            # return list(differ.compare(file1_lines, file2_lines))
            if file1.read() == file2.read():
                return None
            else:
                return True  # some diff is present.



