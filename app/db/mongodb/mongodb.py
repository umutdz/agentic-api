import logging

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import config

logger = logging.getLogger(__name__)


class MongoDB:
    client: AsyncIOMotorClient = None
    mongodb_uri = (
        f"mongodb://{config.MONGO_USER}:{config.MONGO_PASSWORD}"
        f"@{config.MONGO_HOST}:{config.MONGO_PORT}/{config.MONGO_DB}"
        "?authSource=admin"
    )

    @classmethod
    async def connect(cls):
        """Connect to MongoDB."""
        try:
            if cls.client is None:
                cls.client = AsyncIOMotorClient(cls.mongodb_uri)
                # Test the connection
                await cls.client.admin.command("ping")
                logger.info("Successfully connected to MongoDB")
            return cls.client
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            # Reset client on error
            cls.client = None
            raise

    @classmethod
    async def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            logger.info("MongoDB connection closed")

    @classmethod
    async def get_database(cls):
        """Get MongoDB database instance."""
        try:
            if cls.client is None:
                await cls.connect()
            db = cls.client[config.MONGO_DB]
            return db
        except Exception as e:
            logger.error(f"Failed to get database: {str(e)}")
            # Try to reconnect
            await cls.connect()
            return cls.client[config.MONGO_DB]
