from django.conf.urls import url
from apps.user import views
urlpatterns = [
    url(r'^register$', views.register, name='register')  # 注册
]