import shutil

from app.services.micron.data_catalog.fd_trace.dummy_files import (
    _DUMMY_FILES_FOLDER,
    DUMMY_FILES_FOLDER,
)


def main():
    shutil.rmtree(DUMMY_FILES_FOLDER)
    DUMMY_FILES_FOLDER.mkdir(exist_ok=True, parents=True)
    shutil.copytree(_DUMMY_FILES_FOLDER, DUMMY_FILES_FOLDER, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
