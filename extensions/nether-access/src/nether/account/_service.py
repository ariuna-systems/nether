import uuid

import pyotp

from arjuna.nether.common import ServiceError, Event
from arjuna.nether.mediator import BaseService

from ._domain import (
  Account,
  AccountCreated,
  AccountDeleted,
  AccountExists,
  CheckAccountExists,
  CheckAccountExistsFailure,
  CreateAccount,
  CreateAccountFailure,
  CreateAccountWithDefaultRole,
  DeleteAccount,
  DeleteAccountFailure,
)
from ._storage import AccountRepository


class AccountServiceError(ServiceError): ...


class AccountService(BaseService[CreateAccount | CreateAccountWithDefaultRole | DeleteAccount | CheckAccountExists]):
  def __init__(self, *, account_repository: AccountRepository) -> None:
    self._repository = account_repository
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
        case CreateAccount() as cmd:
          result_event = AccountCreated(
            await self._create_account(
              account_name=cmd.account_name,
              email=cmd.email,
              password_hash=cmd.password_hash,
              role_ids=cmd.role_ids,
            ),
          )
        case CreateAccountWithDefaultRole() as cmd:
          result_event = AccountCreated(
            await self._create_account(
              account_name=cmd.account_name,
              email=cmd.email,
              password_hash=cmd.password_hash,
              role_ids=[],
            ),
          )
        case DeleteAccount() as cmd:
          await self._delete_account(cmd.account_id)
          result_event = AccountDeleted()
        case CheckAccountExists() as cmd:
          result_event = AccountExists(await self._repository.exists(cmd.account_id))
    except Exception as error:
      match message:
        case CreateAccount() | CreateAccountWithDefaultRole():
          result_event = CreateAccountFailure(error)
        case DeleteAccount():
          result_event = DeleteAccountFailure(error)
        case CheckAccountExists():
          result_event = CheckAccountExistsFailure(error)
    finally:
      await dispatch(result_event)

  async def _create_account(
    self, *, account_name: str, email: str, password_hash: str, role_ids: list[uuid.UUID]
  ) -> str:
    """
    Vytvoří nového uživatele s daným uživatelským jménem a heslem,
    vygeneruje a vrátí tajný klíč pro dvoufázové ověření.

    :returns: Tajný klíč pro dvoufázové ověření
    """
    # Validace existence uživatele
    saved_account = await self._repository.search_by_name(account_name)
    if saved_account is not None:
      raise AccountServiceError("Account with the same name already exists")

    # Vytvoření uživatele
    roles = await self._repository.read_roles(role_ids)
    account = Account(
      identifier=uuid.uuid4(),
      email=email,
      name=account_name,
      password_hash=password_hash,
      secret=pyotp.random_base32(),
      session=None,
      roles=roles,
    )
    await self._repository.create(account)

    return account.secret

  async def _delete_account(self, account_id: uuid.UUID, /) -> None:
    raise NotImplementedError("Method `_delete_account` not implemented")
