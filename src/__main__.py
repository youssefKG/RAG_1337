def main() -> None:
    import os
    # from src.core.utils import INIT_DB
    from typing import cast
    from fire import Fire

    _ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")
    import django

    django.setup()
    # INIT_DB()

    from src.core.rage_against_machine import RageAgainstMachine

    _: object = cast(object, Fire(RageAgainstMachine))

if __name__ == "__main__":
    main()
