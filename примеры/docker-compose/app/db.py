import os

from sqlalchemy import URL, create_engine

url = URL.create(
    "postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ.get("POSTGRES_PORT", "5432")),
    database=os.environ["POSTGRES_DB"],
)

engine = create_engine(url, pool_pre_ping=True)
