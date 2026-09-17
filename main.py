from pprint import pprint

from src.tools import investigate_ip


def main():
    result = investigate_ip(
        "34.83.25.237",
        activity_limit=10,
    )

    pprint(result)


if __name__ == "__main__":
    main()