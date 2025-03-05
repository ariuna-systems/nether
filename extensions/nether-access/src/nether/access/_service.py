__all__ = ["AccessService"]


import logging
import sys
import uuid
from datetime import datetime, timedelta
from typing import get_args
from zoneinfo import ZoneInfo

import jwt
import pyotp

from nether.common import Event, ServiceError
from nether.mediator import BaseService

from ..account import Account

from ..account import AccountRepository
from ._domain import (
  AccessControlledCommand,
  AccountSession,
  AccountValidated,
  Authorize,
  Authorized,
  JWTValidated,
  OneTimePasswordValidated,
  Unauthorized,
  ValidateAccount,
  ValidateAccountFailure,
  ValidateAccountOneTimePassword,
  ValidateAccountOneTimePasswordFailure,
  ValidateJWT,
  ValidateJWTFailure,
)
from ._storage import AccessRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class AccessServiceError(ServiceError): ...


class AccessService(BaseService[Authorize | ValidateAccount | ValidateAccountOneTimePassword | ValidateJWT]):
  @property
  def supports(self):
    return get_args(self.__orig_bases__[0])[0]

  def __init__(
    self, *, account_repository: AccountRepository, access_repository: AccessRepository, _authorize_all: bool = False
  ) -> None:
    self._account_repository = account_repository
    self._access_repository = access_repository
    self._is_running = False
    self._authorize_all = _authorize_all

  def set_mediator_context_factory(self, *_) -> None: ...

  async def start(self) -> None:
    try:
      if self._authorize_all:
        admin_account = Account(
          identifier=uuid.NAMESPACE_DNS,
          name="admin",
          email="admin@admin",
          password_hash="admin",
          secret="admin",
          session=None,
          roles=[],
        )
        await self._account_repository.create(admin_account)
    except Exception as error:
      logger.warning(f"Issue creating admin account, maybe it already exists: {error}")

    self._is_running = True

  async def stop(self) -> None:
    self._is_running = False

  async def handle(self, message, *, dispatch, **_) -> None:
    if not isinstance(message, self.supports):
      return

    result_event: Event
    try:
      match message:
        case Authorize() as cmd:
          if self._authorize_all:
            result_event = Authorized(uuid.NAMESPACE_DNS)
          else:
            result_event = Authorized(await self._authorize_command(cmd.cmd))
        case ValidateAccount() as cmd:
          result_event = AccountValidated(
            await self._validate_account(
              email=cmd.email, account_name=cmd.account_name, password_hash=cmd.password_hash
            ),
          )
        case ValidateAccountOneTimePassword() as cmd:
          result_event = OneTimePasswordValidated(
            await self._validate_one_time_password(
              account_session_id=cmd.account_session_id, one_time_password=cmd.one_time_password
            ),
          )
        case ValidateJWT() as cmd:
          if self._authorize_all:
            result_event = JWTValidated(uuid.NAMESPACE_DNS)
          else:
            result_event = JWTValidated(await self._validate_jwt(cmd.token))
    except Exception as error:
      match message:
        case Authorize():
          result_event = Unauthorized(error)
        case ValidateAccount():
          result_event = ValidateAccountFailure(error)
        case ValidateAccountOneTimePassword():
          result_event = ValidateAccountOneTimePasswordFailure(error)
        case ValidateJWT():
          result_event = ValidateJWTFailure(error)
    finally:
      await dispatch(result_event)

  async def _validate_account(self, *, email: str | None, account_name: str | None, password_hash: str) -> uuid.UUID:
    if email is None and account_name is None:
      raise AccessServiceError("Email or account name must be provided")

    if account_name is not None:
      account = await self._account_repository.search_by_name(account_name)
    if email is not None:
      account = await self._account_repository.search_by_email(email)

    if account is None:
      raise AccessServiceError("Account not found")
    if password_hash != account.password_hash:
      raise AccessServiceError("Invalid password")

    async with self._access_repository.transaction() as cursor:
      await self._access_repository.delete_account_session(cursor=cursor, account_id=account.identifier)
      session_id = uuid.uuid4()
      expires_at = datetime.now(ZoneInfo("UTC")) + timedelta(minutes=5)
      account_session = AccountSession(account_id=account.identifier, identifier=session_id, expires_at=expires_at)
      await self._access_repository.create_account_session(cursor=cursor, account_session=account_session)

    return session_id

  async def _validate_one_time_password(self, *, account_session_id: uuid.UUID, one_time_password: str) -> str:
    account = await self._account_repository.search_by_session_id(account_session_id)

    if account is None or account.session is None:
      raise AccessServiceError("Session not found")
    if account.session.expires_at < datetime.now(ZoneInfo("UTC")):
      raise AccessServiceError("Session expired")

    if not pyotp.TOTP(account.secret).verify(one_time_password):
      raise AccessServiceError("Invalid OTP")

    async with self._access_repository.transaction() as cursor:
      await self._access_repository.delete_account_session(cursor=cursor, account_session_id=account_session_id)

    token = jwt.encode(
      {"account_id": str(account.identifier), "exp": datetime.now() + timedelta(hours=24)},
      "TODO SECRET",
      algorithm="HS256",
    )
    return token

  async def _validate_jwt(self, token: str, /) -> uuid.UUID:
    try:
      payload = jwt.decode(token, "TODO SECRET", algorithms=["HS256"])
      return uuid.UUID(payload["account_id"])
    except jwt.ExpiredSignatureError as error:
      raise AccessServiceError("Token expired") from error
    except jwt.InvalidTokenError as error:
      raise AccessServiceError("Invalid token") from error
    except Exception as error:
      raise AccessServiceError(str(error)) from error

  async def _authorize_command(self, cmd: AccessControlledCommand) -> uuid.UUID:
    account_id = await self._validate_jwt(cmd.jwt_token)
    async with self._access_repository.transaction() as cursor:
      for field in cmd.fields:
        if not await self._access_repository.check_account_permission(
          account_id=account_id, item_id=getattr(cmd, field), cursor=cursor
        ):
          raise AccessServiceError(f"Permission denied for item `{getattr(cmd, field)}` to account `{account_id}`")
    return account_id
