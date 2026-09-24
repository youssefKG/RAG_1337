def main() -> None:
    import os
    from typing import cast
    from fire import Fire

    _ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")
    import django

    django.setup()

    from src.core.rage_against_machine import RageAgainstMachine

    _: object = cast(object, Fire(RageAgainstMachine))

    # set_student_search_result()


if __name__ == "__main__":
    main()
