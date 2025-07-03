import logging

import asyncpg


class TransactionContext:
  """Manages a single, lazy-loaded database transaction."""

  def __init__(self, *, logger: logging.Logger, pool: asyncpg.Pool):
    self._pool = pool
    self._connection: asyncpg.Connection | None = None
    self._transaction: asyncpg.Transaction | None = None
    self._started = False
    self._finished = False  # Tracks if commit/rollback has been called
    self._logger = logger

  @property
  async def connection(self) -> asyncpg.Connection:
    """Lazily acquires a connection and starts a transaction."""
    if self._finished:
      raise RuntimeError("Transaction has already been finished.")

    if self._connection is None:
      try:
        self._connection = await self._pool.acquire()
        self._transaction = self._connection.transaction()
        await self._transaction.start()
      except Exception as e:
        # If anything fails, clean up immediately
        if self._connection is not None:
          await self._pool.release(self._connection)
        self._connection = None
        self._transaction = None
        self._logger.error(f"Failed to acquire connection or start transaction: {e}")
        raise

    self._started = True
    return self._connection

  async def _cleanup(self):
    """A single, private method to release the connection back to the pool."""

    if self._started and self._connection is not None:
      try:
        await self._pool.release(self._connection)
      except Exception as e:
        self._logger.error(f"Failed to release connection: {e}")
      finally:
        self._connection = None
        self._transaction = None
    self._finished = True

  async def commit(self):
    """Commits the transaction and releases the connection."""
    if self._finished or not self._started or self._transaction is None:
      return

    try:
      try:
        await self._transaction.commit()
      except Exception as e:
        self._logger.error(f"Failed to commit transaction: {e}")
        raise
    finally:
      await self._cleanup()

  async def rollback(self):
    """Rolls back the transaction and releases the connection."""
    if self._finished or not self._started or self._transaction is None:
      return

    try:
      try:
        await self._transaction.rollback()
      except Exception as e:
        self._logger.error(f"Failed to roll back transaction: {e}")
        raise
    finally:
      await self._cleanup()


class TransactionManager:
  """Manages the database connection pool and creates transaction contexts."""

  def __init__(self, logger: logging.Logger, dsn: str, min_pool_size: int = 5, max_pool_size: int = 10):
    self._dsn = dsn
    self._min_size = min_pool_size
    self._max_size = max_pool_size
    self._pool: asyncpg.Pool | None = None
    self._logger = logger

  async def initialize(self):
    """Creates the database connection pool."""
    if self._pool:
      self._logger.warning("Pool is already initialized.")
      return
    try:
      self._pool = await asyncpg.create_pool(dsn=self._dsn, min_size=self._min_size, max_size=self._max_size)
    except Exception as e:
      self._logger.error(f"Failed to initialize database pool: {e}")
      raise

  async def close(self):
    """Closes the connection pool."""
    if self._pool:
      await self._pool.close()
      self._pool = None

  def context(self) -> TransactionContext:
    """Creates a new transaction context."""
    if not self._pool:
      raise RuntimeError("Pool is not initialized. Call initialize() first.")
    return TransactionContext(logger=self._logger, pool=self._pool)
