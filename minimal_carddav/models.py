from django.db import models
from django.utils import timezone


class Contact(models.Model):
    uid = models.CharField(max_length=255, unique=True)

    display_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=50, blank=True)
    phone_short = models.CharField(max_length=50, blank=True)  # Kurzwahl
    phone_mobile = models.CharField(max_length=50, blank=True) # Vodafone-Nummer
    email = models.EmailField(blank=True)

    is_deleted = models.BooleanField(default=False)
    revision = models.PositiveBigIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def touch(self):
        self.revision += 1
        self.updated_at = timezone.now()
        self.save(update_fields=["revision", "updated_at"])

    @property
    def etag(self):
        return f'"{self.revision}"'
    
    def to_vcf(self):
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"UID:{self.uid}",
        ]

        if self.last_name:
            lines.append(f"N:{self.last_name};{self.first_name};;{self.title}")
        else:
            lines.append(f"N:{self.display_name};;;;")

        lines.append(f"FN:{self.display_name}")

        if self.phone_short:
            lines.append(f"TEL;TYPE=WORK,VOICE:{self.phone_short}")
        if self.phone_mobile:
            lines.append(f"TEL;TYPE=CELL,VOICE:{self.phone_mobile}")
        if self.email:
            lines.append(f"EMAIL:{self.email}")

        lines.append(f"REV:{self.updated_at.strftime('%Y%m%dT%H%M%SZ')}")
        lines.append("END:VCARD")
        return "\r\n".join(lines) + "\r\n"

    def __str__(self):
        return self.display_name