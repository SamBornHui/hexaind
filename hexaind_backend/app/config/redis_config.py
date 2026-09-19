from aioredis import ConnectionPool as AsyncConnectionPool
from aioredis import Redis as AsyncRedis
from redis import ConnectionPool as SyncConnectionPool
from redis import Redis as SyncRedis

from app.config.env_vars import celery_environment

# Sync Redis Client
sync_pool = SyncConnectionPool.from_url(
    url=str(celery_environment.celery_result_backend_url)
)


def get_sync_redis_client() -> SyncRedis:
    return SyncRedis(connection_pool=sync_pool)


# Async Redis Client
async_pool = AsyncConnectionPool.from_url(
    url=str(celery_environment.celery_result_backend_url)
)


def get_async_redis_client() -> AsyncRedis:
    return AsyncRedis(connection_pool=async_pool)
