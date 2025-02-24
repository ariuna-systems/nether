__all__ = ["AccessRepository"]


import uuid

import psycopg
import psycopg.rows

from arjuna.nether.common import AsyncConnectorProtocol

from ._domain import AccountSession


class AccessRepositoryError(Exception): ...


class AccessRepository:
  def __init__(self, *, postgres_connector: AsyncConnectorProtocol[psycopg.AsyncCursor[psycopg.rows.DictRow]]):
    self.transaction = postgres_connector.transaction

  async def create_account_session(
    self, *, cursor: psycopg.AsyncCursor[psycopg.rows.DictRow], account_session: AccountSession
  ) -> None:
    await cursor.execute(
      "INSERT INTO account_session (id, account_id, expires_at) VALUES (%s, %s, %s)",
      (account_session.identifier, account_session.account_id, account_session.expires_at),
    )

  async def delete_account_session(
    self,
    *,
    cursor: psycopg.AsyncCursor[psycopg.rows.DictRow],
    account_session_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
  ) -> None:
    if account_session_id is None and account_id is None:
      raise AccessRepositoryError("Either account_session_id or account_id must be provided")

    if account_session_id:
      filter_query = "id = %s"
      params = (account_session_id,)
    elif account_id:
      filter_query = "account_id = %s"
      params = (account_id,)

    await cursor.execute(
      f"DELETE FROM account_session WHERE {filter_query}",
      params,
    )
