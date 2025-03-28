def wrap_base_exception(error: BaseException) -> Exception:
  """
  Použij pro bezpečnost při odchytávání obecné BaseException.
  Vrací chybu obalenou v Exception.

  Propaguje výjimku, když je chyba GeneratorExit | KeyboardInterrupt | SystemExit.

  PŘÍBĚH:
    Knihovna Polars občas vyhazuje výjimku pyo3_runtime.PanicException, která
    nedědí z Exception, ale přímo z BaseException. Proto při snaze o
    zachycení BaseException dochází i k nechtěnému zachytávání kritických chyb
    tj. GeneratorExit, KeyboardInterrupt, SystemExit. Z tohoto důvodu tyto
    chyby propagujeme dále (reraise) a ostatní chyby přebalujeme do Exception.
  """
  if isinstance(error, GeneratorExit | KeyboardInterrupt | SystemExit):
    raise error
  wrapped_error = Exception(error)
  wrapped_error.with_traceback(error.__traceback__)
  return wrapped_error


class DomainError(Exception): ...


class ServiceError(Exception): ...
