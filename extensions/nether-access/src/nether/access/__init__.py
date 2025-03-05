"""
This module is responsible for account access control management: authentication and authorization.
"""

__all__ = [
  "AccountSession",
  "AccessService",
  "AccessRepository",
  "AccountValidated",
  "OneTimePasswordValidated",
  "ValidateAccount",
  "ValidateAccountFailure",
  "ValidateAccountOneTimePassword",
  "ValidateAccountOneTimePasswordFailure",
  "ValidateJWT",
  "JWTValidated",
  "ValidateJWTFailure",
  "Authorize",
  "Authorized",
  "Unauthorized",
  "SignedCommand",
  "AccessControlledCommand",
  "PermissionError",
]


from ._domain import (
  AccountSession,
  AccountValidated,
  OneTimePasswordValidated,
  ValidateAccount,
  ValidateAccountFailure,
  ValidateAccountOneTimePassword,
  ValidateAccountOneTimePasswordFailure,
  ValidateJWT,
  JWTValidated,
  ValidateJWTFailure,
  Authorize,
  Authorized,
  Unauthorized,
  SignedCommand,
  AccessControlledCommand,
  PermissionError,
)
from ._service import AccessService
from ._storage import AccessRepository
