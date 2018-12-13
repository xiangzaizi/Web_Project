from django.conf.urls import url
from apps.user import views
from apps.user.views import RegisterView, ActiveView, LoginView, LogoutView, UserInfoView
urlpatterns = [
    # 注册用户的三种方式
    # url(r'^register$', views.register_1, name='register')  # 注册
    # 项目中的注册
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),

    # 方式一: 用户登录校验 login_required  一个样式
    # from django.contrib.auth.decorators import login_required
    # url(r'^order/<?P(page)>\d+$', login_required(UserOrderView.as_view()), name='order')

    # 方式二:  mixin
    url('^$', UserInfoView.as_view(), name='user')  # 用户中心页




]