import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        connection_params = psycopg2.extensions.parse_dsn(database_url)
        connection_params.setdefault("sslmode", "require")
        return psycopg2.connect(**connection_params)

    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "Adventureworks"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
    )