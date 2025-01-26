"""linklibrary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.urls import include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("", RedirectView.as_view(url="rsshistory/")),
    path("rsshistory/", include("rsshistory.urls")),
    path("robots.txt", RedirectView.as_view(url="rsshistory/robots.txt")),
    path("opensearch.xml", RedirectView.as_view(url="rsshistory/opensearch.xml")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
