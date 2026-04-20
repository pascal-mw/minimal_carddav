from django.urls import path
from . import views

urlpatterns = [
    path(".well-known/carddav", views.root),
    path("carddav/", views.root),
    path("carddav/principals/users/1/", views.principal),
    path("carddav/addressbook/", views.addressbook),
    path("carddav/contact/<str:uid>.vcf", views.contact_vcf),
]