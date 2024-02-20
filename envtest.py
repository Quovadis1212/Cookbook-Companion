import os

database_host = os.environ.get('DATABASE_HOST')
database_user = os.environ.get('DATABASE_USER')
database_password = os.environ.get('DATABASE_PASSWORD')


print(f"DATABASE_HOST: {database_host}")
print(f"DATABASE_USER: {database_user}")
print(f"DATABASE_PASSWORD: {database_password}")