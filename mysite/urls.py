from django.conf.urls import url

from mysite.core import views


urlpatterns = [
    url(r'^$', views.UsersListView.as_view(), name='users_list'),
    url(r'^generate/$', views.GenerateRandomUserView.as_view(), name='generate'),
]
