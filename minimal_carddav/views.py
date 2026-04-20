from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from .models import Contact
from django.utils.html import escape


@csrf_exempt
def root(request):
    if request.method == "PROPFIND":
        xml = """<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/carddav/</d:href>
    <d:propstat>
      <d:prop>
        <d:current-user-principal>
          <d:href>/carddav/principals/users/1/</d:href>
        </d:current-user-principal>
        <d:resourcetype><d:collection/></d:resourcetype>
        <d:displayname>CardDAV Root</d:displayname>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>"""
        return HttpResponse(xml, content_type="application/xml; charset=utf-8", status=207)
    return HttpResponse("OK")


@csrf_exempt
def principal(request):
    if request.method != "PROPFIND":
        return HttpResponse(status=405)

    xml = """<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/carddav/principals/users/1/</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>User</d:displayname>
        <d:resourcetype><d:principal/></d:resourcetype>
        <card:addressbook-home-set>
          <d:href>/carddav/addressbook/</d:href>
        </card:addressbook-home-set>
        <d:current-user-principal>
          <d:href>/carddav/principals/users/1/</d:href>
        </d:current-user-principal>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>"""
    return HttpResponse(xml, content_type="application/xml; charset=utf-8", status=207)


@csrf_exempt
def addressbook(request):
    if request.method not in ("PROPFIND", "REPORT"):
        return HttpResponse(status=405)

    depth = request.META.get("HTTP_DEPTH", "0")

    if request.method == "PROPFIND" and depth == "0":
        xml = """<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/carddav/addressbook/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype>
          <d:collection/>
          <card:addressbook/>
        </d:resourcetype>
        <d:displayname>Contacts</d:displayname>
        <d:sync-token>1</d:sync-token>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>"""
        return HttpResponse(xml, content_type="application/xml; charset=utf-8", status=207)

    # REPORT oder PROPFIND Depth:1 → Kontakte mit vCard-Daten inline
    contacts = Contact.objects.filter(is_deleted=False)
    items = ""
    for c in contacts:
        items += f"""
  <d:response>
    <d:href>/carddav/contact/{c.uid}.vcf</d:href>
    <d:propstat>
      <d:prop>
        <d:getetag>{c.etag}</d:getetag>
        <d:resourcetype/>
        <card:address-data>{escape(c.to_vcf())}</card:address-data>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>"""

    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<d:multistatus xmlns:d="DAV:"
               xmlns:card="urn:ietf:params:xml:ns:carddav">
  <d:response>
    <d:href>/carddav/addressbook/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype>
          <d:collection/>
          <card:addressbook/>
        </d:resourcetype>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
{items}
</d:multistatus>"""
    return HttpResponse(xml, content_type="application/xml; charset=utf-8", status=207)


@csrf_exempt
def contact_vcf(request, uid):
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        c = Contact.objects.get(uid=uid, is_deleted=False)
    except Contact.DoesNotExist:
        return HttpResponse(status=404)

    resp = HttpResponse(c.to_vcf(), content_type="text/vcard; charset=utf-8")
    resp["ETag"] = c.etag
    return resp