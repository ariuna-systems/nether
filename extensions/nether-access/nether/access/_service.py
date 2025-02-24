__all__ = ["AccessService"]


import uuid
from datetime import datetime, timedelta
from typing import get_args
from zoneinfo import ZoneInfo

import jwt
import pyotp

from nether.common import Event, ServiceError
from nether.mediator import BaseService

from ..account import AccountRepository
from ._domain import (
  AccountSession,
  AccountValidated,
  JWTValidated,
  OneTimePasswordValidated,
  ValidateAccount,
  ValidateAccountFailure,
  ValidateAccountOneTimePassword,
  ValidateAccountOneTimePasswordFailure,
  ValidateJWT,
  ValidateJWTFailure,
)
from ._storage import AccessRepository


class AccessServiceError(ServiceError): ...


class AccessService(BaseService[ValidateAccount | ValidateAccountOneTimePassword | ValidateJWT]):
  @property
  def supports(self):
    return get_args(self.__orig_bases__[0])[0]

  def __init__(self, *, account_repository: AccountRepository, access_repository: AccessRepository) -> None:
    self._account_repository = account_repository
    self._access_repository = access_repository
    self._is_running = False

  def set_mediator(self, *_) -> None: ...

  async def start(self) -> None:
    self._is_running = False

  async def stop(self) -> None:
    self._is_running = False

  async def handle(self, message, *, dispatch, **_) -> None:
    if not isinstance(message, self.supports):
      return

    result_event: Event
    try:
      match message:
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
          result_event = JWTValidated(
            await self._validate_jwt(token=cmd.token),
          )
    except Exception as error:
      match message:
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

  async def _validate_jwt(self, *, token: str) -> uuid.UUID:
    try:
      payload = jwt.decode(token, "TODO SECRET", algorithms=["HS256"])
      return uuid.UUID(payload["account_id"])
    except jwt.ExpiredSignatureError as error:
      raise AccessServiceError("Token expired") from error
    except jwt.InvalidTokenError as error:
      raise AccessServiceError("Invalid token") from error
    except Exception as error:
      raise AccessServiceError(str(error)) from error
