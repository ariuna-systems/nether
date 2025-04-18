import uuid

import psycopg
from nether.common import AsyncConnectorProtocol

from ..access import AccountSession
from ._domain import Account, AccountRole

__all__ = ["AccountRepository"]


class AccountRepositoryError(Exception): ...


class AccountRepository:
  def __init__(
    self,
    *,
    postgres_connector: AsyncConnectorProtocol[psycopg.AsyncCursor[psycopg.rows.DictRow], psycopg.AsyncConnection],
  ):
    self.transaction = postgres_connector.transaction

  @staticmethod
  async def _query_account_secret(
    cursor: psycopg.AsyncCursor[psycopg.rows.DictRow], account_id: uuid.UUID
  ) -> str | None:
    await cursor.execute(
      "SELECT secret FROM account_secret WHERE account_id = %s",
      (account_id,),
    )
    if (select_result := await cursor.fetchone()) is None:
      return None
    return select_result["secret"]

  @staticmethod
  async def _query_roles(
    cursor: psycopg.AsyncCursor[psycopg.rows.DictRow], role_ids: list[uuid.UUID]
  ) -> list[AccountRole]:
    await cursor.execute(
      "SELECT (id, name) FROM role WHERE id = ANY(%s)",
      (role_ids,),
    )
    role_query = await cursor.fetchall()
    roles = []
    for role in role_query:
      roles.append(AccountRole(identifier=role["id"], name=role["name"]))

    return roles

  @staticmethod
  async def _query_account_roles(
    cursor: psycopg.AsyncCursor[psycopg.rows.DictRow], account_id: uuid.UUID
  ) -> list[AccountRole]:
    await cursor.execute(
      "SELECT * FROM account_role WHERE account_id = %s",
      (account_id,),
    )
    role_ids = [role["role_id"] for role in await cursor.fetchall()]
    return await AccountRepository._query_roles(cursor=cursor, role_ids=role_ids)

  @staticmethod
  async def _query_account_session(
    cursor: psycopg.AsyncCursor[psycopg.rows.DictRow], account_id: uuid.UUID
  ) -> AccountSession | None:
    await cursor.execute(
      "SELECT * FROM account_session WHERE account_id = %s",
      (account_id,),
    )
    if (result := await cursor.fetchone()) is None:
      return None
    return AccountSession(
      identifier=result["id"],
      account_id=result["account_id"],
      expires_at=result["expires_at"],
    )

  async def search(self, account_id: uuid.UUID, /) -> Account | None:
    async with self.transaction() as cursor:
      await cursor.execute(
        "SELECT * FROM account WHERE id = %s",
        (account_id,),
      )
      account_query = await cursor.fetchone()
      if account_query is None:
        return None

      account_secret = await self._query_account_secret(account_id=account_query["id"], cursor=cursor)
      if account_secret is None:
        raise AccountRepositoryError("Account's 2FA secret not found")

      account_session_id = await self._query_account_session(account_id=account_query["id"], cursor=cursor)
      roles = await self._query_account_roles(cursor=cursor, account_id=account_query["id"])

    return Account(
      identifier=account_query["id"],
      name=account_query["name"],
      email=account_query["email"],
      password_hash=account_query["password_hash"],
      secret=account_secret,
      session=account_session_id,
      roles=roles,
    )

  async def search_by_name(self, account_name: str, /) -> Account | None:
    async with self.transaction() as cursor:
      await cursor.execute(
        "SELECT * FROM account WHERE name = %s",
        (account_name,),
      )
      account_query = await cursor.fetchone()
      if account_query is None:
        return None

      account_secret = await self._query_account_secret(account_id=account_query["id"], cursor=cursor)
      if account_secret is None:
        raise AccountRepositoryError("Account's 2FA secret not found")

      account_session = await self._query_account_session(account_id=account_query["id"], cursor=cursor)
      roles = await self._query_account_roles(cursor=cursor, account_id=account_query["id"])

    return Account(
      identifier=account_query["id"],
      name=account_query["name"],
      email=account_query["email"],
      password_hash=account_query["password_hash"],
      secret=account_secret,
      session=account_session,
      roles=roles,
    )

  async def search_by_email(self, email: str, /) -> Account | None:
    async with self.transaction() as cursor:
      await cursor.execute(
        "SELECT * FROM account WHERE email = %s",
        (email,),
      )
      account_query = await cursor.fetchone()
      if account_query is None:
        return None

      account_secret = await self._query_account_secret(cursor=cursor, account_id=account_query["id"])
      if account_secret is None:
        raise AccountRepositoryError("Account's 2FA secret not found")

      account_session = await self._query_account_session(account_id=account_query["id"], cursor=cursor)
      roles = await self._query_account_roles(cursor=cursor, account_id=account_query["id"])

    return Account(
      identifier=account_query["id"],
      name=account_query["name"],
      email=account_query["email"],
      password_hash=account_query["password_hash"],
      secret=account_secret,
      session=account_session,
      roles=roles,
    )

  async def search_by_session_id(self, account_session_id: uuid.UUID, /) -> Account | None:
    async with self.transaction() as cursor:
      await cursor.execute(
        "SELECT account_id FROM account_session WHERE id = %s",
        (account_session_id,),
      )
      account_id_query = await cursor.fetchone()
      if account_id_query is None:
        return None

      account_id = account_id_query["account_id"]
      await cursor.execute(
        "SELECT * FROM account WHERE id = %s",
        (account_id,),
      )
      account_query = await cursor.fetchone()
      if account_query is None:
        return None

      account_secret = await self._query_account_secret(cursor=cursor, account_id=account_query["id"])
      if account_secret is None:
        raise AccountRepositoryError("Account's 2FA secret not found")

      account_session = await self._query_account_session(account_id=account_query["id"], cursor=cursor)
      roles = await self._query_account_roles(cursor=cursor, account_id=account_query["id"])

    return Account(
      identifier=account_query["id"],
      name=account_query["name"],
      email=account_query["email"],
      password_hash=account_query["password_hash"],
      secret=account_secret,
      session=account_session,
      roles=roles,
    )

  async def read_roles(self, role_ids: list[uuid.UUID], /) -> list[AccountRole]:
    async with self.transaction() as cursor:
      return await self._query_roles(cursor=cursor, role_ids=role_ids)

  async def create(self, account: Account, /) -> None:
    zip_account_role = [(account.identifier, role.identifier) for role in account.roles]

    async with self.transaction() as cursor:
      await cursor.execute(
        "INSERT INTO account (id, email, name, password_hash) VALUES (%s, %s, %s, %s)",
        (account.identifier, account.email, account.name, account.password_hash),
      )
      await cursor.executemany(
        "INSERT INTO account_role (account_id, role_id) VALUES %s",
        zip_account_role,
      )
      await cursor.execute(
        "INSERT INTO account_secret (account_id, secret) VALUES (%s, %s)",
        (account.identifier, account.secret),
      )

  async def delete(self, account_id: uuid.UUID, /) -> None:
    async with self.transaction() as cursor:
      await cursor.execute("DELETE FROM account WHERE id = %s", (account_id,))

  async def exists(self, account_id: uuid.UUID, /) -> bool:
    return await self.search(account_id) is not None

  async def exists_by_name(self, account_name: str, /) -> bool:
    return await self.search_by_name(account_name) is not None
