from typing import Any, AsyncGenerator, Final

from coveo_settings import StringSetting
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

DATABASE_USERNAME: Final = StringSetting("database.username", fallback="postgres")
DATABASE_PASSWORD: Final = StringSetting("database.password", fallback="postgres")
DATABASE_ENDPOINT: Final = StringSetting("database.endpoint", fallback="localhost")
DATABASE_NAME: Final = StringSetting("database.name", fallback="postgres")
DATABASE_URL: Final = (
    f"postgresql+asyncpg://{str(DATABASE_USERNAME)}:{str(DATABASE_PASSWORD)}@{str(DATABASE_ENDPOINT)}"
    f"/{str(DATABASE_NAME)}"
)
DATABASE_CONNECTION_ATTEMPTS: Final = 5
DATABASE_CONNECTION_MINIMUM_WAIT_SECOND: Final = 1

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@retry(
    retry=retry_if_exception_type(ConnectionError),
    stop=stop_after_attempt(DATABASE_CONNECTION_ATTEMPTS),
    wait=wait_exponential(min=DATABASE_CONNECTION_MINIMUM_WAIT_SECOND),
    reraise=True,
)
async def setup_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
