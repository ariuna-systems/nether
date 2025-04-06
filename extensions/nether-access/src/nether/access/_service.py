__all__ = ["AccessService", "MicrosoftOnlineService"]


import base64
from collections.abc import Iterable
import logging
import sys
import uuid
from datetime import UTC, datetime, timedelta

import aiohttp
import jwt
import pyotp
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from nether.common import Event
from nether.exceptions import ServiceError
from nether.service import Service

from ..account import Account

from ..account import AccountRepository
from ._domain import (
  AccessControlledCommand,
  AccountSession,
  AccountValidated,
  Authorize,
  Authorized,
  JWTValidated,
  MicrosoftOnlineJWTValidated,
  OneTimePasswordValidated,
  Unauthorized,
  ValidateAccount,
  ValidateAccountFailure,
  ValidateAccountOneTimePassword,
  ValidateAccountOneTimePasswordFailure,
  ValidateJWT,
  ValidateJWTFailure,
  ValidateMicrosoftOnlineJWT,
  ValidateMicrosoftOnlineJWTFailure,
)
from ._storage import AccessRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class AccessServiceError(ServiceError): ...


class AccessService(Service[Authorize | ValidateAccount | ValidateAccountOneTimePassword | ValidateJWT]):
  def __init__(
    self,
    *,
    account_repository: AccountRepository,
    access_repository: AccessRepository,
    key: str = "DEV",
    enable_rsa_with_signing_key: str | None = None,
    _authorize_all: bool = False,
  ) -> None:
    """
    Uses HMAC by default.

    To enable RSA, set `key` to public key,
    set `enable_rsa_with_signing_key` to private key.
    """
    self._account_repository = account_repository
    self._access_repository = access_repository
    self._is_running = False
    self._key = key
    self._private_key = enable_rsa_with_signing_key or key
    self._algorithm = "RS256" if enable_rsa_with_signing_key else "HS256"
    self._authorize_all = _authorize_all

  async def start(self) -> None:
    try:
      if self._authorize_all:
        admin_account = Account(
          identifier=uuid.NAMESPACE_DNS,
          name="admin",
          email="admin@admin.admin",
          password_hash="admin",
          secret=base64.b32encode(b"admin").decode('utf-8').rstrip('='),  # MFSG22LO
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
            result_event = JWTValidated(self._validate_jwt(cmd.token))
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
      expires_at = datetime.now(tz=UTC) + timedelta(minutes=5)
      account_session = AccountSession(account_id=account.identifier, identifier=session_id, expires_at=expires_at)
      await self._access_repository.create_account_session(cursor=cursor, account_session=account_session)

    return session_id

  async def _validate_one_time_password(self, *, account_session_id: uuid.UUID, one_time_password: str) -> str:
    account = await self._account_repository.search_by_session_id(account_session_id)

    if account is None or account.session is None:
      raise AccessServiceError("Session not found")
    if account.session.expires_at < datetime.now(tz=UTC):
      raise AccessServiceError("Session expired")

    if not pyotp.TOTP(account.secret).verify(one_time_password):
      raise AccessServiceError("Invalid OTP")

    async with self._access_repository.transaction() as cursor:
      await self._access_repository.delete_account_session(cursor=cursor, account_session_id=account_session_id)

    token = jwt.encode(
      {"account_id": str(account.identifier), "exp": datetime.now(tz=UTC) + timedelta(hours=24)},
      self._private_key,
      algorithm=self._algorithm,
    )
    return token

  def _validate_jwt(self, token: str, /) -> uuid.UUID:
    try:
      payload = jwt.decode(token, self._key, algorithms=[self._algorithm])
      return uuid.UUID(payload["account_id"])
    except jwt.ExpiredSignatureError as error:
      raise AccessServiceError("Token expired") from error
    except jwt.InvalidTokenError as error:
      raise AccessServiceError("Invalid token") from error
    except Exception as error:
      raise AccessServiceError(str(error)) from error

  async def _authorize_command(self, cmd: AccessControlledCommand) -> uuid.UUID:
    account_id = self._validate_jwt(cmd.jwt_token)
    async with self._access_repository.transaction() as cursor:
      assets_to_check: list[uuid.UUID] = []
      for field in cmd.fields:
        field_value = getattr(cmd, field)
        if isinstance(field_value, Iterable):
          assets_to_check.extend(field_value)
        else:
          assets_to_check.append(field_value)
      for asset in assets_to_check:
        if not await self._access_repository.check_account_permission(
          account_id=account_id, asset_id=asset, cursor=cursor
        ):
          raise AccessServiceError(f"Permission denied for asset `{asset}` to account `{account_id}`")
    return account_id


class MicrosoftOnlineService(Service[ValidateMicrosoftOnlineJWT]):
  def __init__(self, *, tenant_id: str, client_id: str):
    self._tenant_id = tenant_id
    self._client_id = client_id
    self._keys: list = []
    self._last_fetch: datetime = datetime.fromtimestamp(0, tz=UTC)
    self._cache_duration = timedelta(hours=1)
    self._is_running = False

  async def handle(self, message, *, dispatch, **_) -> None:
    if not isinstance(message, self.supports):
      return

    result_event: Event
    try:
      match message:
        case ValidateMicrosoftOnlineJWT():
          result_event = MicrosoftOnlineJWTValidated(await self._validate(message.jwt_token))
    except Exception as error:
      match message:
        case ValidateMicrosoftOnlineJWT():
          result_event = ValidateMicrosoftOnlineJWTFailure(error)
    finally:
      await dispatch(result_event)

  async def _fetch_keys(self) -> None:
    url = f"https://login.microsoftonline.com/{self._tenant_id}/discovery/v2.0/keys"
    async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
        if response.status != 200:
          raise ValueError(f"Failed to fetch JW Keys: {response.status}")
        self._keys = (await response.json())["keys"]
        self._last_fetch = datetime.now(tz=UTC)

  async def _current_keys(self) -> list:
    current_time = datetime.now(tz=UTC)
    if 0 == len(self._keys) or (current_time - self._last_fetch > self._cache_duration):
      await self._fetch_keys()
    return self._keys

  async def _validate(self, jwt_token: str) -> dict:
    keys = await self._current_keys()

    unverified_header = jwt.get_unverified_header(jwt_token)
    kid = unverified_header["kid"]

    signing_key = next((key for key in keys if key["kid"] == kid), None)
    if not signing_key:
      raise ValueError("No matching key found")

    pem_key = f"-----BEGIN CERTIFICATE-----\n{signing_key['x5c'][0]}\n-----END CERTIFICATE-----"
    cert = x509.load_pem_x509_certificate(pem_key.encode(), default_backend())
    public_key = (
      cert.public_key()
      .public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
      .decode("utf-8")
    )
    return jwt.decode(
      jwt_token,
      key=public_key,
      algorithms=["RS256"],
      audience=self._client_id,
      issuer=f"https://login.microsoftonline.com/{self._tenant_id}/v2.0",
      options={
        "verify_signature": True,
        "verify_exp": True,
        "verify_aud": True,
        "verify_iss": True,
      },
    )
