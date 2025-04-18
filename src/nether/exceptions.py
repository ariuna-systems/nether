"""
This module contains custom error classes and functions.
"""

__all__ = ["wrap_base_exception", "DomainError", "ServiceError", "StorageError", "NotFoundError", "AlreadyExistsError"]


def wrap_base_exception(error: BaseException) -> Exception:
  """
  Použij pro bezpečnost při odchytávání obecné :class:`BaseException`.

  :param: Zachycená obecná základní výjimka.
  :return: Chybu obalenou v :class:`Exception`.

  Propaguje výjimku, když je chyba :class:`GeneratorExit`, :class:`KeyboardInterrupt`, :class:`SystemExit`.

  .. note::
    Knihovna Polars občas vyhazuje výjimku :class:`pyo3_runtime.PanicException`, která
    nedědí z :class:`Exception`, ale přímo z :class:`BaseException`. Proto při snaze o
    zachycení :class:`BaseException` dochází i k nechtěnému zachytávání kritických chyb
    tj. :class:`GeneratorExit`, :class:`KeyboardInterrupt`, :class:`SystemExit`.
    Z tohoto důvodu tyto chyby propagujeme dále a ostatní chyby měníme přebalujeme
    na :class:`Exception`.
  """
  if isinstance(error, GeneratorExit | KeyboardInterrupt | SystemExit):
    raise error
  wrapped_error = Exception(error)
  wrapped_error.with_traceback(error.__traceback__)
  return wrapped_error


class DomainError(Exception): ...


class ServiceError(Exception): ...


class StorageError(Exception): ...


class NotFoundError(ServiceError): ...


class AlreadyExistsError(ServiceError): ...
