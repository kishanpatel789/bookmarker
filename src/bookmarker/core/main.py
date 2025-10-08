from .config import set_up_logging
from .database import get_repo

set_up_logging()


def main():
    repo = get_repo()
    repo.create_db_and_tables()


if __name__ == "__main__":  # pragma: no cover
    main()
