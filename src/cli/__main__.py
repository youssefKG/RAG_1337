import os

FILES: list[tuple[str, float]] = [
    ("/home/user/project/main.py", 1756281600.123),
    ("/home/user/project/config.py", 1756281665.456),
    ("/home/user/project/utils.py", 1756281720.789),
    ("/home/user/project/models/user.py", 1756281801.234),
    ("/home/user/project/models/product.py", 1756281855.678),
    ("/home/user/project/models/order.py", 1756281920.901),
    ("/home/user/project/api/routes.py", 1756281988.345),
    ("/home/user/project/api/auth.py", 1756282042.567),
    ("/home/user/project/api/users.py", 1756282100.789),
    ("/home/user/project/tests/test_main.py", 1756282165.123),
    ("/home/user/project/tests/test_api.py", 1756282201.456),
    ("/home/user/project/tests/test_models.py", 1756282250.789),
    ("/home/user/project/data/input.json", 1756282305.234),
    ("/home/user/project/data/output.json", 1756282355.567),
    ("/home/user/project/data/cache.db", 1756282400.890),
    ("/home/user/project/logs/app.log", 1756282455.123),
    ("/home/user/project/logs/error.log", 1756282501.456),
    ("/home/user/project/docs/README.md", 1756282550.789),
    ("/home/user/project/docs/API.md", 1756282605.234),
    ("/home/user/project/static/style.css", 1756282655.567),
    ("/home/user/project/static/app.js", 1756282700.890),
    ("/home/user/project/templates/index.html", 1756282755.123),
    ("/home/user/project/templates/login.html", 1756282801.456),
    ("/home/user/project/templates/dashboard.html", 1756282850.789),
    ("/home/user/project/.env", 1756282905.234),
    ("/home/user/project/requirements.txt", 1756282955.567),
    ("/home/user/project/Dockerfile", 1756283000.890),
    ("/home/user/project/docker-compose.yml", 1756283055.123),
    ("/home/user/project/scripts/deploy.sh", 1756283101.456),
    ("/home/user/project/scripts/backup.sh", 1756283150.789),
]


def setup_django() -> None:
    _ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

    import django

    django.setup()


def insert_file(path: str, last_updated_time: float) -> None:
    from src.server.models import FileModel

    _ = FileModel.objects.create(path=path, last_modified_at=last_updated_time)


def display_files() -> None:
    from src.server.models import FileModel

    for file in FileModel.objects.all():
        print(file)


def delete_file(paths: list[str]) -> None:
    from src.server.models import FileModel

    objects, count = FileModel.objects.filter(path__in=paths).delete()
    print(objects, count)


def create_files() -> None:
    from src.server.models import FileModel

    _ = FileModel.objects.bulk_create(
        [FileModel(path=file[0], last_modified_at=file[1]) for file in FILES]
    )


def delete_by_path(paths: list[str]) -> None:
    from src.server.models import FileModel

    count, objects = FileModel.objects.filter(path__in=paths).delete()
    print(count)
    print(objects)
    for obj in objects:
        print(obj)


def main():
    setup_django()
    create_files()
    # insert_file("file_path_2", 400.0)
    display_files()
    print("*" * 4, "DELETE", "*" * 4)
    delete_by_path([file[0] for file in FILES])
    display_files()


if __name__ == "__main__":
    main()
