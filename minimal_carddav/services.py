# services.py
from django.db import transaction
from .models import Contact
from .utils import make_uid


@transaction.atomic
def upsert_contact(
    source_id: str,
    display_name: str,
    last_name: str = "",
    first_name: str = "",
    title: str = "",
    phone_short: str = "",
    phone_mobile: str = "",
    email: str = "",
):
    uid = make_uid(source_id)

    fields = {
        "display_name": display_name,
        "last_name": last_name,
        "first_name": first_name,
        "title": title,
        "phone_short": phone_short,
        "phone_mobile": phone_mobile,
        "email": email,
    }

    obj, created = Contact.objects.get_or_create(uid=uid, defaults=fields)

    if not created:
        changed = False
        for field, val in fields.items():
            if getattr(obj, field) != val:
                setattr(obj, field, val)
                changed = True

        if obj.is_deleted:
            obj.is_deleted = False
            changed = True

        if changed:
            obj.revision += 1
            obj.save()

    return obj


@transaction.atomic
def delete_contact(source_id: str):
    uid = make_uid(source_id)
    try:
        obj = Contact.objects.get(uid=uid)
        obj.is_deleted = True
        obj.revision += 1
        obj.save()
        return True
    except Contact.DoesNotExist:
        return False