from django.conf.urls import url

from . import views

# Valid952HostnameRegex = "(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])";

app_name = 'display'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r"^(?P<hostname>(.*))/(?P<username>([a-zA-Z0-9]+))/show/$", views.show, name='show'),
]
