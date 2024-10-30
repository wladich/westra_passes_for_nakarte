# coding: utf-8
import sys


def report_error(*fields: str, fatal: bool = False) -> None:
    assert fields
    print("\t".join(fields))
    if fatal:
        print("Error is fatal, exiting", file=sys.stderr)
        sys.exit(1)


def report_errors(errors: list[list[str]] | None, fatal: bool = False) -> None:
    if errors:
        for error in errors:
            report_error(*error)
        if fatal:
            print("Errors are fatal, exiting", file=sys.stderr)
            sys.exit(1)
