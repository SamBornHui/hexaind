from abc import ABC, abstractmethod

from google.cloud import bigquery
from google.oauth2 import service_account

from app.services.admin.connectors.schemas import BigQueryAuthType


class QueryExecutor(ABC):

    def __init__(self):
        self.__def_kwargs__ = {"dry_run": False, "use_query_cache": False}

    @abstractmethod
    def build_query_job(self, query, kwargs=None):
        pass

    @abstractmethod
    def execute_query(self, query, kwargs=None):
        pass


class ServiceAccountQueryExecutor(QueryExecutor):
    def __init__(self, auth_info):
        super().__init__()
        self.auth_info = auth_info

    def build_query_job(self, query, kwargs=None):
        credentials = service_account.Credentials.from_service_account_info(
            self.auth_info
        )
        client = bigquery.Client(
            credentials=credentials, project=credentials.project_id
        )

        kwargs = self.__def_kwargs__ if kwargs is None else kwargs
        job_config = bigquery.QueryJobConfig(**kwargs)

        query_job = client.query(query, job_config=job_config)
        return query_job

    def execute_query(self, query: str, kwargs=None):
        results = self.build_query_job(query, kwargs).result()
        return results


class UserAuthQueryExecutor(QueryExecutor):

    def __init__(self, auth_info):
        super().__init__()
        self.auth_info = auth_info

    def build_query_job(self, query, kwargs=None):
        raise NotImplementedError("Bigquery UserAuth not yet implemented")

    def execute_query(self, query: str, kwargs=None):
        raise NotImplementedError("Bigquery UserAuth not yet implemented")


class QueryExecutorFactory(ABC):
    @abstractmethod
    def create_query_executor(self):
        pass


class ServiceAccountQueryExecutorFactory(QueryExecutorFactory):

    def __init__(self, auth_info):
        self.auth_info = auth_info

    def create_query_executor(self):
        return ServiceAccountQueryExecutor(self.auth_info)


class UserAuthQueryExecutorFactory(QueryExecutorFactory):

    def __init__(self, auth_info):
        self.auth_info = auth_info

    def create_query_executor(self):
        return UserAuthQueryExecutor(self.auth_info)


def get_big_query_executor(authentication_type, kwargs):
    if authentication_type == BigQueryAuthType.SERVICE_ACCOUNT:
        factory = ServiceAccountQueryExecutorFactory(**kwargs)
    elif authentication_type == BigQueryAuthType.USER_AUTH:
        factory = UserAuthQueryExecutorFactory(**kwargs)
    else:
        raise ValueError("Invalid authentication type")

    return factory.create_query_executor()


class BqExecutorHelper:

    def __init__(self, bq_executor: QueryExecutor, query):
        self.query = query
        self.bq_executor = bq_executor

    def execute(self):
        results = self.bq_executor.execute_query(self.query)
        return results.to_dataframe()

    def dryrun(self):
        dryrun_kwargs = {"dry_run": True, "use_query_cache": False}
        query_job = self.bq_executor.build_query_job(self.query, kwargs=dryrun_kwargs)
        return query_job.schema, query_job.total_bytes_processed


class BqTableExecutorHelper(BqExecutorHelper):

    def __init__(self, bq_executor: QueryExecutor, table_id: str, dataset_id: str):
        super().__init__(bq_executor, f"SELECT * FROM `{dataset_id}.{table_id}`")
        self.table_id = table_id
        self.dataset_id = dataset_id
