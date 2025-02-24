__all__ = ["AccountSession"]


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
