"""La estructura del proyecto y la higiene de los secretos."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    ".env.example",
    ".gitignore",
    "README.md",
    "app/__init__.py",
    "app/main.py",
    "app/config.py",
    "app/routers/__init__.py",
    "app/routers/estimations.py",
    "app/services/__init__.py",
    "app/services/llm_service.py",
    "app/services/prompt_builder.py",
    "app/context/__init__.py",
    "app/context/examples.py",
    "app/schemas/__init__.py",
    "app/schemas/estimation.py",
]

ENV_VARIABLES = [
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "APP_ENV", "LOG_LEVEL",
]


@pytest.mark.parametrize("path", REQUIRED)
def test_required_file_exists(path):
    assert (ROOT / path).is_file(), f"falta {path}"


def test_there_is_a_test_transcription():
    transcriptions = list((ROOT / "transcripciones").glob("*.txt"))
    assert transcriptions, "falta una transcripción de prueba en transcripciones/"
    assert all(len(path.read_text(encoding="utf-8")) > 500 for path in transcriptions)


def test_env_is_ignored_by_git():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in ignored and "!.env.example" in ignored


def test_env_example_lists_every_variable_without_values():
    values = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    assert sorted(values) == sorted(ENV_VARIABLES)
    assert all(value == "" for value in values.values()), "el .env.example no debe llevar valores"


def test_no_api_key_in_the_code():
    pattern = re.compile(r"sk-(ant-)?[A-Za-z0-9_-]{20,}")
    for path in (ROOT / "app").rglob("*.py"):
        assert not pattern.search(path.read_text(encoding="utf-8")), f"posible clave en {path}"


def test_importing_the_app_does_not_need_an_api_key():
    """En un proceso aparte y sin variables: importar no carga la configuración."""
    code = "import app.main, app.services.llm_service; from app.config import get_settings; " \
           "assert get_settings.cache_info().currsize == 0"
    env = {"PATH": "", "PYTHONPATH": str(ROOT)}
    command = [sys.executable, "-c", code]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
