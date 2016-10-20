from django.conf.urls import url

from . import views

app_name = 'manage'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^ssh$', views.ssh, name='ssh'),
]
