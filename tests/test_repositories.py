import tempfile
from pathlib import Path

import pytest

from zulip_write_only_proxy.models import AdminClient, ScopedClient
from zulip_write_only_proxy.repositories import JSONRepository


def test_file_creation():
    with tempfile.TemporaryDirectory() as f:
        path = Path(f) / "test.json"

        assert not path.exists()

        repository = JSONRepository(path=path)

        assert path.exists()

        assert len(repository.list()) == 0


def test_get_scoped_client(repository):
    result = repository.get("client1")

    assert isinstance(result, ScopedClient)
    assert result.stream == "Test Stream 1"
    assert result.proposal_no == 1

    with pytest.raises(KeyError):
        repository.get("invalid")


def test_get_admin_client(repository):
    result = repository.get("admin1")

    assert isinstance(result, AdminClient)
    assert result.admin is True


def test_put_scoped_client(repository):
    client = ScopedClient(
        key="client3",
        stream="Test Stream 3",
        proposal_no=3,
    )

    repository.put(client)

    result = repository.get(client.key)

    assert isinstance(result, ScopedClient)
    assert result.stream == "Test Stream 3"
    assert result.proposal_no == 3

    with pytest.raises(ValueError):
        repository.put(client)


def test_put_admin_client(repository):
    client = AdminClient(key="admin2", admin=True)

    repository.put_admin(client)

    result = repository.get(client.key)

    assert isinstance(result, AdminClient)
    assert result.admin is True


def test_list_clients(repository):
    result = repository.list()

    assert len(result) == 3

    assert isinstance(result[0], ScopedClient)
    assert result[0].stream == "Test Stream 1"
    assert result[0].proposal_no == 1

    assert isinstance(result[1], ScopedClient)
    assert result[1].stream == "Test Stream 2"
    assert result[1].proposal_no == 2

    assert isinstance(result[2], AdminClient)
    assert result[2].key == "admin1"
    assert result[2].admin is True