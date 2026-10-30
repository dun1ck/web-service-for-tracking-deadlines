# Тесты проекта

Автотесты на `pytest` для **блока 2 ТЗ** (авторизация, JWT, брутфорс, RBAC):

| Файл | Покрытие |
|------|----------|
| `test_auth.py` | TC-REG-01…05, TC-AUTH-01…04, TC-BRUTE-01…05 |
| `test_groups_rbac.py` | TC-RBAC-01…05 |

Запуск (нужен PostgreSQL после `alembic upgrade head`):

```bash
cd backend
KV_BACKEND=memory pytest -q
```

CI поднимает Postgres и гоняет те же тесты на pull request в `main`.
