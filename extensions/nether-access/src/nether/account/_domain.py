import uuid
from dataclasses import dataclass

__all__ = ["Account", "AccountRole", "AccountDomainError"]

from nether.common import Command, Event, FailureEvent
from nether.exceptions import DomainError

from ..access import AccountSession


class AccountDomainError(DomainError): ...


@dataclass(frozen=True, kw_only=True, slots=True)
class AccountRole:
  identifier: uuid.UUID
  name: str


class Account:
  def __init__(
    self,
    *,
    identifier: uuid.UUID,
    email: str,
    name: str,
    password_hash: str,
    secret: str,
    session: AccountSession | None,
    roles: list[AccountRole],
  ) -> None:
    self.identifier = identifier
    self.email = email
    self.name = name
    self.password_hash = password_hash
    self.secret = secret
    self.session = session
    self.roles = roles


## MESSAGES ##


@dataclass(frozen=True, kw_only=True)
class CreateAccount(Command):
  account_name: str
  email: str
  password_hash: str
  role_ids: list[uuid.UUID]


@dataclass(frozen=True, kw_only=True)
class CreateAccountWithDefaultRole(Command):
  account_name: str
  email: str
  password_hash: str


@dataclass(frozen=True)
class AccountCreated(Event):
  account_secret: str


@dataclass(frozen=True)
class CreateAccountFailure(FailureEvent): ...


@dataclass(frozen=True)
class DeleteAccount(Command):
  account_id: uuid.UUID


@dataclass(frozen=True)
class AccountDeleted(Event): ...


@dataclass(frozen=True)
class DeleteAccountFailure(FailureEvent): ...


@dataclass(frozen=True)
class CheckAccountExists(Command):
  account_id: uuid.UUID


@dataclass(frozen=True)
class AccountExists(Event):
  exists: bool


@dataclass(frozen=True)
class CheckAccountExistsFailure(FailureEvent): ...
