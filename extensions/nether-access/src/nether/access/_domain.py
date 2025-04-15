__all__ = ["AccountSession"]


from collections.abc import Iterable
from typing import ClassVar
import uuid
from dataclasses import dataclass
from datetime import datetime

from nether.common import Command, FailureEvent, SuccessEvent


@dataclass(frozen=True, kw_only=True, slots=True)
class AccountSession:
  identifier: uuid.UUID
  account_id: uuid.UUID
  expires_at: datetime


## MESSAGES ##


@dataclass(frozen=True, kw_only=True)
class SignedCommand(Command):
  jwt_token: str


@dataclass(frozen=True, kw_only=True)
class AccessControlledCommand(SignedCommand):
  fields: ClassVar[Iterable[str]]


@dataclass(frozen=True, kw_only=True)
class ValidateAccount(Command):
  email: str | None
  account_name: str | None
  password_hash: str


@dataclass(frozen=True)
class AccountValidated(SuccessEvent):
  account_session_id: uuid.UUID


@dataclass(frozen=True)
class ValidateAccountFailure(FailureEvent): ...


@dataclass(frozen=True, kw_only=True)
class ValidateAccountOneTimePassword(Command):
  account_session_id: uuid.UUID
  one_time_password: str


@dataclass(frozen=True)
class OneTimePasswordValidated(SuccessEvent):
  token: str


@dataclass(frozen=True)
class ValidateAccountOneTimePasswordFailure(FailureEvent): ...


@dataclass(frozen=True)
class ValidateJWT(Command):
  token: str


@dataclass(frozen=True)
class JWTValidated(SuccessEvent):
  account_id: uuid.UUID


@dataclass(frozen=True)
class ValidateJWTFailure(FailureEvent): ...


@dataclass(frozen=True)
class Authorize(Command):
  cmd: AccessControlledCommand


@dataclass(frozen=True)
class Authorized(SuccessEvent):
  account_id: uuid.UUID


@dataclass(frozen=True)
class Unauthorized(FailureEvent): ...


# Microsoft Online


@dataclass(frozen=True)
class ValidateMicrosoftOnlineJWT(Command):
  jwt_token: str


@dataclass(frozen=True)
class MicrosoftOnlineJWTValidated(SuccessEvent):
  decoded_payload: dict


class ValidateMicrosoftOnlineJWTFailure(FailureEvent): ...
