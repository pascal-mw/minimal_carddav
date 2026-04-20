# minimal_carddav

A minimal, read-only CardDAV server implemented as a reusable Django app. Designed for organizations (universities, clubs, companies) that want to publish a shared address book — maintained server-side — and sync it to Android and iPhone devices automatically.

**Philosophy:** No full CardDAV implementation. Clients can only read. The server manages all contacts programmatically via a simple `upsert_contact` / `delete_contact` API.

---

## Features

- Read-only CardDAV addressbook (clients cannot write)
- Compatible with iOS, Android (DAVx⁵), and Thunderbird (CardBook)
- Supports persons (with structured name + title) and function phones (free-form name)
- Two phone numbers per contact: internal short dial + mobile (important for caller ID)
- Upsert/delete API for integration into existing Django projects
- Admin interface with automatic revision tracking
- HTTP Basic Auth

---

## Requirements

- Python 3.10+
- Django 4.2+

---

## Installation

**1. Copy the app into your project:**

```
your_project/
├── manage.py
├── your_project/
└── minimal_carddav/      ← place here
```

**2. Add to `INSTALLED_APPS` in `settings.py`:**

```python
INSTALLED_APPS = [
    ...
    "minimal_carddav",
]
```

**3. Add middleware to `settings.py`:**

The BasicAuth middleware must come after Django's `SecurityMiddleware` but before everything else. It protects all CardDAV endpoints.

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "minimal_carddav.middleware.DjangoBasicAuthMiddleware",  # ← add here
    ...
]
```

**4. Include URLs in your project's `urls.py`:**

```python
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("minimal_carddav.urls")),  # ← add this
    ...
]
```

**5. Run migrations:**

```bash
python manage.py migrate
```

**6. Create a Django user for CardDAV authentication:**

```bash
python manage.py createsuperuser
```

---

## Usage

### Adding and updating contacts

Use `upsert_contact` from your existing Django app or management commands:

```python
from minimal_carddav.services import upsert_contact, delete_contact

# Person with title
upsert_contact(
    source_id="person_42",          # stable internal ID — never change this
    display_name="Dr. John Doe",
    last_name="Doe",
    first_name="John",
    title="Dr.",
    phone_short="12345",            # internal short dial
    phone_mobile="+49123123456789",  # carrier number
    email="doe@example.com",
    department="Institute of Thermodynamics",
)

# Person without title
upsert_contact(
    source_id="person_17",
    display_name="Jane Doe",
    last_name="Doe",
    first_name="Jane",
    phone_short="12345",
    phone_mobile="+49123123456789",
)

# Function phone (no structured name)
upsert_contact(
    source_id="funcphone_gh_oa",
    display_name="Important Function",
    phone_short="12345",
    phone_mobile="+49123123456789",
)
```

`upsert_contact` is fully idempotent — call it as often as you like. It only increments the revision (and triggers a client sync) when data actually changed.

### Deleting contacts

```python
delete_contact("person_42")
```

The contact is soft-deleted (`is_deleted=True`). Clients will drop it on their next sync. Hard deletion happens automatically after a long-enough period of time (all clients need to have synced once) if you run a cleanup command (see below).

### Important: `source_id` must be stable

The `source_id` is hashed into a permanent UID. **Never change it** — if you do, a new contact is created instead of updating the existing one. Always use a stable internal database ID, not a name:

```python
# ✅ Good
upsert_contact(source_id=f"person_{person.pk}", ...)

# ❌ Bad — breaks on name change (marriage, etc.)
upsert_contact(source_id="doe_jane", ...)
```

### Updating after a name change

Just call `upsert_contact` with the same `source_id` and the new data:

```python
upsert_contact(
    source_id="person_17",      # same ID as before
    display_name="Smith Jane",
    last_name="Smith",
    first_name="Jane",
    phone_short="12345",
    phone_mobile="+49123123456789",
)
```

---

## Cleanup deleted contacts

Soft-deleted contacts stay in the database so clients that were offline can still sync the deletion. After a while they can be removed.

---

## Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET/PROPFIND` | `/.well-known/carddav` | Redirects to `/carddav/` |
| `PROPFIND` | `/carddav/` | DAV root, returns current-user-principal |
| `PROPFIND` | `/carddav/principals/users/1/` | Principal, returns addressbook-home-set |
| `PROPFIND/REPORT` | `/carddav/addressbook/` | Addressbook with all contacts |
| `GET` | `/carddav/contact/<uid>.vcf` | Single vCard |

---

## Client Setup

### iPhone / iPad (iOS)

1. **Settings** → **Contacts** → **Accounts** → **Add Account** → **Other**
2. Tap **Add CardDAV Account**
3. Enter:
   - **Server:** `https://yourdomain.com`
   - **User name:** your Django username
   - **Password:** your Django password
   - **Description:** e.g. "Work Contacts"
4. Tap **Next** — iOS will auto-discover the addressbook via `/.well-known/carddav`

> **Note:** iOS requires HTTPS. Self-signed certificates must be trusted manually under Settings → General → About → Certificate Trust Settings. For internal networks, consider using a proper certificate via Let's Encrypt or your institution's CA.

> **Sync interval:** iOS syncs automatically when the app is opened. There is no manual "sync now" button in the default Contacts app. Changes typically appear within a few minutes.

### Android (DAVx⁵) — recommended

DAVx⁵ is the standard CardDAV client for Android and available on [F-Droid](https://f-droid.org/packages/at.bitfire.davdroid/) (free) and Google Play.

1. Install **DAVx⁵**
2. Tap **+** → **Login with URL and user name**
3. Enter:
   - **Base URL:** `https://yourdomain.com/carddav/`
   - **User name:** your Django username
   - **Password:** your Django password
4. Tap **Login** → select the addressbook → **Create account**
5. Set sync interval under account settings (e.g. every 1 hour)

> **Tip:** DAVx⁵ syncs into the native Android Contacts app. Contacts will appear in phone dialer with caller ID for both the short dial number and the mobile number — as long as both `TEL` fields are present in the vCard, which this app handles automatically.

---

## Security notes

- All CardDAV endpoints require HTTP Basic Auth
- Use HTTPS in production — Basic Auth over plain HTTP sends credentials in base64 (not encrypted)
- The middleware blocks all requests without valid credentials, including `/.well-known/carddav`
- Clients are read-only by design: PUT, DELETE, and MKCOL are not implemented

---

## Extending the app

The app is intentionally minimal. Common extensions:

**Import from CSV:**
```python
import csv
from minimal_carddav.services import upsert_contact

with open("contacts.csv") as f:
    for row in csv.DictReader(f):
        upsert_contact(
            source_id=f"csv_{row['id']}",
            display_name=row["display_name"],
            last_name=row.get("last_name", ""),
            first_name=row.get("first_name", ""),
            phone_short=row.get("phone_short", ""),
            phone_mobile=row.get("phone_mobile", ""),
        )
```

**Sync from your existing Django model:**
```python
from minimal_carddav.services import upsert_contact, delete_contact
from myapp.models import Employee

def sync_to_carddav():
    active_ids = set()
    for emp in Employee.objects.filter(active=True):
        upsert_contact(
            source_id=f"employee_{emp.pk}",
            display_name=emp.full_name,
            last_name=emp.last_name,
            first_name=emp.first_name,
            title=emp.title,
            phone_short=emp.extension,
            phone_mobile=emp.mobile,
            email=emp.email,
        )
        active_ids.add(emp.pk)

    # delete contacts for deactivated employees
    for emp in Employee.objects.filter(active=False):
        delete_contact(f"employee_{emp.pk}")
```

---

## License

MIT
