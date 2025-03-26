from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from nether.access import (
  MicrosoftOnlineService,
  ValidateMicrosoftOnlineJWT,
)


class AsyncContextManagerMock:
  def __init__(self, return_value=None):
    self.return_value = return_value

  async def __aenter__(self):
    return self.return_value

  async def __aexit__(self, exc_type, exc, tb):
    pass


@pytest.fixture
def service():
  return MicrosoftOnlineService(tenant_id="test-tenant", client_id="test-client")


@pytest.mark.asyncio
async def test_init(service):
  assert service._tenant_id == "test-tenant"
  assert service._client_id == "test-client"
  assert service._keys == []
  assert not service._is_running


@pytest.mark.asyncio
async def test_start_stop(service):
  await service.start()
  assert service._is_running
  await service.stop()
  assert not service._is_running


@pytest.mark.asyncio
async def test_handle_valid_jwt(service):
  with patch.object(service, "_validate", AsyncMock(return_value={"sub": "user1"})):
    dispatch = AsyncMock()
    message = ValidateMicrosoftOnlineJWT(jwt_token="test.token")
    await service.handle(message, dispatch=dispatch)
    dispatch.assert_awaited_once()
    event = dispatch.await_args.args[0]
    assert event.__class__.__name__ == "MicrosoftOnlineJWTValidated"
    assert event.decoded_payload == {"sub": "user1"}


@pytest.mark.asyncio
async def test_handle_wrong_message(service):
  dispatch = AsyncMock()
  await service.handle("wrong_type", dispatch=dispatch)
  dispatch.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_keys_success(service):
  # Mock response
  mock_response = MagicMock()
  mock_response.status = 200
  mock_response.json = AsyncMock(return_value={"keys": [{"kid": "k1"}]})

  # Mock session.get() to return a context manager
  mock_session = MagicMock()
  mock_session.get.return_value = AsyncContextManagerMock(mock_response)

  # Patch ClientSession to return a context manager wrapping the session
  with patch("aiohttp.ClientSession", return_value=AsyncContextManagerMock(mock_session)):
    await service._fetch_keys()
    assert service._keys == [{"kid": "k1"}]
    assert isinstance(service._last_fetch, datetime)


@pytest.mark.asyncio
async def test_fetch_keys_failure(service):
  # Mock response
  mock_response = MagicMock()
  mock_response.status = 400

  # Mock session.get() to return a context manager
  mock_session = MagicMock()
  mock_session.get.return_value = AsyncContextManagerMock(mock_response)

  # Patch ClientSession to return a context manager wrapping the session
  with patch("aiohttp.ClientSession", return_value=AsyncContextManagerMock(mock_session)):
    with pytest.raises(ValueError) as exc:
      await service._fetch_keys()
    assert "Failed to fetch JW Keys: 400" in str(exc.value)


@pytest.mark.asyncio
async def test_current_keys_fetch(service):
  with patch.object(service, "_fetch_keys", AsyncMock()) as mock_fetch:
    service._keys = []
    await service._current_keys()
    mock_fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_no_key(service):
  with patch.object(service, "_current_keys", AsyncMock(return_value=[{"kid": "k2", "x5c": ["cert"]}])):
    with patch("jwt.get_unverified_header", return_value={"kid": "k1"}):
      with pytest.raises(ValueError) as exc:
        await service._validate("test.token")
      assert "No matching key found" in str(exc.value)
