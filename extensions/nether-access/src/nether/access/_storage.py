__all__ = ["AccessRepository"]


import uuid

import psycopg
import psycopg.rows

from nether.common import AsyncConnectorProtocol

from ._domain import AccountSession


class AccessRepositoryError(Exception): ...


class AccessRepository:
  def __init__(
    self,
    *,
    postgres_connector: AsyncConnectorProtocol[psycopg.AsyncCursor[psycopg.rows.DictRow], psycopg.AsyncConnection],
  ):
    self.transaction = postgres_connector.transaction

  async def check_account_permission(
    self, *, account_id: uuid.UUID, asset_id: uuid.UUID, cursor: psycopg.AsyncCursor[psycopg.rows.DictRow]
  ) -> bool:
    await cursor.execute(
      """
        WITH account_role AS (SELECT role_id FROM account_role WHERE account_id = %(account_id)s)
        SELECT EXISTS(
          SELECT 1 FROM access_entry
          LEFT JOIN account_role ON access_entry.role_id = account_role.role_id
          WHERE access_entry.asset_id = %(asset_id)s AND (access_entry.account_id = %(account_id)s OR account_role.role_id IS NOT NULL)
        )
      """,
      {"account_id": account_id, "asset_id": asset_id},
    )
    result = await cursor.fetchone()
    if result is None:
      return False

    return result["exists"]

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
