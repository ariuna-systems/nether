from contextlib import asynccontextmanager
from pathlib import Path
import psycopg
import pytest
import pyotp

from nether.access import AccessRepository, AccessService
from nether.account import AccountRepository, AccountService
import pytest_asyncio

pytestmark = pytest.mark.asyncio

class AsyncPostgresConnector:
  def __init__(self, *, credentials: dict) -> None:
    self._credentials = credentials

  @asynccontextmanager
  async def transaction(self):
    conn = await psycopg.AsyncConnection.connect(**self._credentials, row_factory=psycopg.rows.dict_row, autocommit=True)
    try:
      cursor = conn.cursor()
      yield cursor
      await conn.commit()
    except Exception as error:
      await conn.rollback()
      raise error
    finally:
      await conn.close()


@pytest_asyncio.fixture()
async def connector():
  # Connect to default postgres database first
  connector = AsyncPostgresConnector(credentials={
    "host": "localhost",
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres"
  })
  
  test_db_name = "test_nether_access"
  async with connector.transaction() as cursor:
    await cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
    await cursor.execute(f"CREATE DATABASE {test_db_name}")
    
  db_connector = AsyncPostgresConnector(credentials={
    "host": "localhost",
    "dbname": test_db_name,
    "user": "postgres",
    "password": "postgres"
  })
  
  async with db_connector.transaction() as cursor:
    with (Path(__file__).parent / "schema.sql").open() as schema_file:
      await cursor.execute(schema_file.read())
  
  yield db_connector
  
  # Cleanup
  async with connector.transaction() as cursor:
    await cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")


async def test_access(connector):
  account_repository = AccountRepository(postgres_connector=connector)
  access_repository = AccessRepository(postgres_connector=connector)
  account_service = AccountService(account_repository=account_repository)
  access_service = AccessService(account_repository=account_repository, access_repository=access_repository)
  
  account_name = "test"
  password_hash = "password_hash"
  account_secret = await account_service._create_account(account_name=account_name, email="test@test", password_hash=password_hash, role_ids=[])
  assert (account := await account_repository.search_by_name(account_name)) is not None
  
  session_id = await access_service._validate_account(account_name=account_name, password_hash=password_hash, email=None)
  jwt_token = await access_service._validate_one_time_password(account_session_id=session_id, one_time_password=pyotp.TOTP(account_secret).now())
  assert await access_service._validate_jwt(jwt_token) == account.identifier
  
  
  
  
  