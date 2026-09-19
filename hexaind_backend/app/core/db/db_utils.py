from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config.env_vars import environment


def get_db_async() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(environment.mongo_details)


def get_db_sync():
    client = MongoClient(environment.mongo_details)
    return client


def close_db_sync(client: MongoClient):
    try:
        client.close()
    except Exception as e:
        print("Unable to close the sync connection: ", str(e))
        pass


async def get_database_client():
    client = MongoClient(environment.mongo_details)
    return client


def get_thermocalc_db_async() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(environment.thermocalc_mongo_detail)


def get_thermocalc_db_sync():
    client = MongoClient(environment.thermocalc_mongo_detail)
    return client
