from database import engine

try:
    with engine.connect() as connection:
        print("Successfully connected to PostgreSQL!")
except Exception as e:
    print("Database connection failed:")
    print(e)