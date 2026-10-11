# license-lint

Офлайн-проверка лицензий репозитория: находит файл `LICENSE`, определяет его тип по тексту, сверяет с лицензией, указанной в `pyproject.toml`, `Cargo.toml` или `package.json`, и может запрещать выбранные лицензии. Без зависимостей, Python 3.10+.

## Быстрый старт

```bash
python -m license_lint /path/to/repo
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
