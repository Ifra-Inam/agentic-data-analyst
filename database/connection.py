import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="Adventureworks",
        user="postgres",
        password=os.getenv("DB_PASSWORD")
    )