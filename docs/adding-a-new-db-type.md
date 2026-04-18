# Adding a New Database Type

This guide walks through adding a new database type (Redis is used as the example throughout).

---

## Backend — 2 files

### 1. Create the type descriptor

Create `backend/app/registry/types/redis.py`:

```python
from app.registry.db_type_registry import DBTypeDescriptor, register_db_type

register_db_type(
    DBTypeDescriptor(
        canonical_name="redis",
        aliases=["redis"],          # any chart name variants that should map to this type
        display_label="Redis",
        icon_name="redis",
        helm_chart_url="https://gitlab.internal/dbaas/charts/redis",  # your real URL
        helm_chart_version="7.2.4",                                    # current version
    )
)
```

**Fields:**

| Field | Purpose |
|---|---|
| `canonical_name` | Internal key used everywhere — must be lowercase, no spaces |
| `aliases` | Chart names the scanner may encounter in GitLab `Chart.yaml` files |
| `display_label` | Human-readable name shown in the UI |
| `icon_name` | Frontend icon key (see frontend step below) |
| `helm_chart_url` | Link shown in the Parent Helm Charts section and on chart version clicks |
| `helm_chart_version` | Current version of the parent chart |

### 2. Register the module

Add one import line to `backend/app/registry/types/__init__.py`:

```python
from app.registry.types import elasticsearch, mongodb, postgresql, redis

__all__ = ["elasticsearch", "mongodb", "postgresql", "redis"]
```

That's all the backend needs. The scanner will now recognise Redis chart names and the API will include it in `/api/v1/databases/types`.

---

## Frontend — 2 files

### 3. Add a badge color

In `frontend/src/components/fields/DBTypeField.tsx`, add an entry to `TYPE_COLORS`:

```ts
const TYPE_COLORS: Record<string, string> = {
  elasticsearch: "bg-yellow-100 text-yellow-800",
  mongodb:       "bg-green-100 text-green-800",
  postgresql:    "bg-blue-100 text-blue-800",
  redis:         "bg-red-100 text-red-800",   // ← add this
};
```

### 4. Add a card color in the Parent Charts section

In `frontend/src/components/databases/ParentChartsSection.tsx`, add entries to both color maps:

```ts
const TYPE_COLORS: Record<string, string> = {
  elasticsearch: "border-yellow-200 bg-yellow-50",
  mongodb:       "border-green-200 bg-green-50",
  postgresql:    "border-blue-200 bg-blue-50",
  redis:         "border-red-200 bg-red-50",   // ← add this
};

const BADGE_COLORS: Record<string, string> = {
  elasticsearch: "bg-yellow-100 text-yellow-800",
  mongodb:       "bg-green-100 text-green-800",
  postgresql:    "bg-blue-100 text-blue-800",
  redis:         "bg-red-100 text-red-800",    // ← add this
};
```

If you omit these, the type will still work — it just falls back to gray.

---

## Environment variable

Set the console URL template so the Connect link works in the Manage column:

```env
CONSOLE_REDIS_URL=https://redis-commander.internal/{db_name}
```

The placeholder `{db_name}` is replaced at render time. See `ConsoleSettings` in `backend/app/config.py` for the full list of supported placeholders.

---

## Checklist

- [ ] `backend/app/registry/types/redis.py` created
- [ ] `backend/app/registry/types/__init__.py` updated
- [ ] `DBTypeField.tsx` — badge color added
- [ ] `ParentChartsSection.tsx` — card colors added
- [ ] `CONSOLE_REDIS_URL` set in `.env`
