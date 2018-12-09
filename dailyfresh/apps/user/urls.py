from django.conf.urls import url
from apps.user import views
from apps.user.views import RegisterView
urlpatterns = [
    # 注册用户的三种方式
    # url(r'^register$', views.register_1, name='register')  # 注册
    # 项目中的注册
    url(r'', RegisterView.as_view(), name='register')
]