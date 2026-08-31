import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

connection = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="Adventureworks",
    user="postgres",
    password=os.getenv("DB_PASSWORD")
)

print("Connection successful!")

connection.close()