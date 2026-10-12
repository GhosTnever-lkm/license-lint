# license-lint

[![CI](https://github.com/GhosTnever-lkm/license-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/GhosTnever-lkm/license-lint/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/GhosTnever-lkm/license-lint)](https://github.com/GhosTnever-lkm/license-lint/releases/latest)

Офлайн-проверка лицензий репозитория: находит файл `LICENSE`, определяет его тип по тексту, сверяет с лицензией, указанной в `pyproject.toml`, `Cargo.toml` или `package.json`, и может запрещать выбранные лицензии. Без зависимостей, Python 3.10+.

## Быстрый старт

Скачайте wheel из [последнего релиза](https://github.com/GhosTnever-lkm/license-lint/releases/latest) и установите:

```bash
python -m pip install license_lint-0.1.2-py3-none-any.whl
```

Запустите проверку:

```bash
license-lint /path/to/repo
python -m license_lint . --deny GPL-3.0-only --json
python -m license_lint . --strict   # предупреждения тоже дают код 1
```

Пример вывода:

```text
license-lint: .
LICENSE file: LICENSE
Detected license: MIT
Declared in pyproject.toml: MIT
OK: no findings
```

## Проверки

`pyproject.toml` читается из таблицы `[project]`, `Cargo.toml` — из `[package]`, а `package.json` поддерживает строку `license` и совместимый объект с полем `type`.

| Код | Уровень | Смысл |
| --- | --- | --- |
| `LICENSE_MISSING` | error | файла лицензии нет |
| `LICENSE_MISMATCH` | error | манифест указывает другую лицензию, чем текст `LICENSE` |
| `DENIED_LICENSE` | error | найдена лицензия из `--deny` |
| `LICENSE_UNRECOGNIZED` | warning | текст не похож на известные лицензии |
| `MANIFEST_NO_LICENSE` | warning | в манифесте нет поля лицензии |
| `COPYLEFT` | info | проект под GPL/LGPL/AGPL |

Коды возврата: `0` — ошибок нет, `1` — есть ошибки (или предупреждения при `--strict`).

## Ограничения

- Определение по тексту — эвристика по ключевым фразам, а не полный сканер SPDX. Нестандартные тексты помечаются как `LICENSE_UNRECOGNIZED`.
- Проверяется только лицензия самого проекта, а не лицензии зависимостей.
- Это не юридическая консультация.

## Разработка

```bash
python -m unittest discover -s tests -t .
```

## Поддержка и Pro-версия

Базовая версия остаётся бесплатной; отдельный Pro-выпуск пока не опубликован. Нужна проверка дополнительных манифестов или собственных правил? [Опишите сценарий в запросе](https://github.com/GhosTnever-lkm/license-lint/issues/new).

## Лицензия

MIT — см. [LICENSE](LICENSE).

## История изменений

См. [CHANGELOG.md](CHANGELOG.md). Политика безопасности — в [SECURITY.md](SECURITY.md).

## Использование в CI

Фрагмент для GitHub Actions (Python 3.10+, без зависимостей):

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- name: license-lint
  run: python -m license_lint . --strict
```
