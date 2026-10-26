"""Engine dan factory session async untuk API serta startup.

Session request dibagikan melalui get_db; service/repository menentukan
batas commit.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Pinjamkan session database selama satu request.

    Tidak commit otomatis, exception diteruskan.

    Yields:
        AsyncSession yang ditutup setelah request selesai.
    """
    async with AsyncSessionLocal() as session:
        yield session