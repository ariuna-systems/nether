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
  "MicrosoftOnlineService",
  "ValidateMicrosoftOnlineJWT",
  "ValidateMicrosoftOnlineJWTFailure",
  "MicrosoftOnlineJWTValidated",
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
  MicrosoftOnlineJWTValidated,
  ValidateMicrosoftOnlineJWT,
  ValidateMicrosoftOnlineJWTFailure,
)
from ._service import AccessService, MicrosoftOnlineService
from ._storage import AccessRepository
