import os

from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
PORT = int(os.getenv("PORT", "8000"))

""" SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "not_set") """
