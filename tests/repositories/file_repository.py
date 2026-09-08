import django
import os


_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")
django.setup()


import pytest

from src.server.models import FileModel
from src.server.repositories.file_repository import File, FileRepository


@pytest.fixture
def repository():
    return FileRepository()


def test_create_one(repository: FileRepository):
    file = repository.create_one(
        path="/tmp/test.txt",
        last_modified_at=123.45,
    )

    assert file.id > 0
    assert file.path == "/tmp/test.txt"
    assert file.last_modified_at == 123.45

    model = FileModel.objects.get(pk=file.id)

    assert model.path == "/tmp/test.txt"
    assert model.last_modified_at == 123.45


def test_get_by_path_returns_file(repository: FileRepository):
    model = FileModel.objects.create(
        path="/tmp/test.txt",
        last_modified_at=123.45,
    )

    file = repository.get_by_path("/tmp/test.txt")

    assert file is not None
    assert file.id == model.pk
    assert file.path == model.path
    assert file.last_modified_at == model.last_modified_at


def test_get_by_path_returns_none_when_missing(db, repository):
    assert repository.get_by_path("/does/not/exist.txt") is None


def test_delete_by_path_deletes_single_file(db, repository):
    FileModel.objects.create(
        path="/tmp/test.txt",
        last_modified_at=123.45,
    )

    repository.delete_by_path("/tmp/test.txt")

    assert not FileModel.objects.filter(path="/tmp/test.txt").exists()


def test_delete_by_path_deletes_multiple_files(repository: FileRepository):
    FileModel.objects.create(
        path="/tmp/a.txt",
        last_modified_at=100.0,
    )
    FileModel.objects.create(
        path="/tmp/b.txt",
        last_modified_at=200.0,
    )
    FileModel.objects.create(
        path="/tmp/c.txt",
        last_modified_at=300.0,
    )

    repository.delete_by_path(
        [
            "/tmp/a.txt",
            "/tmp/b.txt",
        ]
    )

    assert not FileModel.objects.filter(path="/tmp/a.txt").exists()

    assert not FileModel.objects.filter(path="/tmp/b.txt").exists()

    assert FileModel.objects.filter(path="/tmp/c.txt").exists()


def test_create_many(db, repository):
    files = [
        File("/tmp/a.txt", 100.0),
        File("/tmp/b.txt", 200.0),
    ]

    result = repository.create_many(files)

    assert result is files
    assert files[0].id > 0
    assert files[1].id > 0

    assert FileModel.objects.filter(
        pk=files[0].id,
        path="/tmp/a.txt",
    ).exists()

    assert FileModel.objects.filter(
        pk=files[1].id,
        path="/tmp/b.txt",
    ).exists()


def test_delete_by_id(db, repository):
    model = FileModel.objects.create(
        path="/tmp/test.txt",
        last_modified_at=123.45,
    )

    repository.delete_by_id(str(model.pk))

    assert not FileModel.objects.filter(pk=model.pk).exists()


def test_get_model_by_id_returns_model(db, repository):
    model = FileModel.objects.create(
        path="/tmp/test.txt",
        last_modified_at=123.45,
    )

    result = repository.get_model_by_id(model.pk)

    assert result == model


def test_get_model_by_id_returns_none_when_missing(db, repository):
    assert repository.get_model_by_id(999999) is None
