import beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .dataset import Dataset, DataTypeEnum, FileTypeEnum, MetaData, Data, Flags, Errors
from .job import Job, JobState, StateName
from .jupyter_notebook import JupyterNotebook
from .jupyter_notebook_template import JupyterNotebookTemplate
from .project import Project
from .user import User
from .temp_ds import Temp_ds


async def init_beanie(client: AsyncIOMotorClient):
    await beanie.init_beanie(
        database=client.get_default_database(),
        document_models=[
            Job,
            JupyterNotebook,
            JupyterNotebookTemplate,
            User,
            Project,
            Dataset,
            Temp_ds
        ]
    )

__all__ = [
    Job, JobState, StateName,
    JupyterNotebook,
    JupyterNotebookTemplate,
    User,
    Project,
    Dataset, DataTypeEnum, FileTypeEnum, MetaData, Data, Flags, Errors,
    Temp_ds,
    init_beanie
]
