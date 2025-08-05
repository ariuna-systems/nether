import pytest

from nether.mediator import Mediator


@pytest.fixture
def mediator():
  return Mediator()


def test_mediator_calls_handler(mediator):
  assert False
