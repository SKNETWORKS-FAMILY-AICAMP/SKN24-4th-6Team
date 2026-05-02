#!/usr/bin/env python
"""Django CLI entry point. Defaults to dev settings — override via env for prod."""

import os
import sys


def main() -> None:
  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
  try:
    from django.core.management import execute_from_command_line
  except ImportError as exc:
    raise ImportError(
      "Couldn't import Django. Activate the venv (uv sync / pip install -r requirements.txt)."
    ) from exc
  execute_from_command_line(sys.argv)


if __name__ == "__main__":
  main()
