from django.conf.urls import url
from apps.user import views
from apps.user.views import RegisterView, ActiveView, LoginView,LogoutView
urlpatterns = [
    # 注册用户的三种方式
    # url(r'^register$', views.register_1, name='register')  # 注册
    # 项目中的注册
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),


]