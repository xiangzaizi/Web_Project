import re
from django_redis import get_redis_connection
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.core.mail import send_mail
from itsdangerous import SignatureExpired  # 过期的异常

from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from apps.user.models import User, Address
from dailyfresh import settings
from utils.mixin import LoginRequiredMixin


def register_1(request):
    return render(request, 'register.html')

# 项目开发的简单流程
# 1.接收参数
# 2.参数校验(后端校验)
# 3.业务处理
# 4.返回应答

# user/register_handle
def register_2(request):
    """注册处理"""
    # 1. 接受参数
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')

    # 2. 参数校验(后端校验)
    # 校验数据的完整性
    if not all([username, password, email]):
        return render(request, 'register.html', {'error':'数据完整'})

    # 校验邮箱格式
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'error':'邮箱有误'})

    # 校验用户名是否注册
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None

    if user is not None:
        return render(request, 'register.html', {"errmsg":"用户名已注册"})

    # 校验邮箱是否被注册

    # 3. 业务处理:注册
    user = User.objects.create_user(username, password, email)
    user.is_active = 0
    user.save()

    # 4.返回应答:跳转到首页
    return redirect(reverse('good:index'))

# /user/register
# get: 显示注册页面
# post: 进行页面注册处理
# request.method -->GET POST
def register_3(request):
    """注册"""
    if request.method == 'GET':
        # 显示注册页面
        return render(request, 'register.html')
    else:
        # 进行注册处理
        # 1.接收参数
        username = request.POST.get('user_name')  # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2.参数校验(后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱格式
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否已注册
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is not None:
            return render(request, 'register.html', {'errmsg': '用户名已注册'})

        # 校验邮箱是否被注册...

        # 3.业务处理：注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 4.返回应答: 跳转到首页
        return redirect(reverse('goods:index'))

# /user/register
class RegisterView(View):
    """注册"""
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """注册处理"""
        print('----post----')
        # 1.接收参数
        username = request.POST.get('user_name')  # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2.参数校验(后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱格式
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否已注册
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is not None:
            return render(request, 'register.html', {'errmsg': '用户名已注册'})

        # 校验邮箱是否被注册...

        # 3.业务处理：注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 注册之后, 需要给用户的注册邮箱发送激活邮件, 邮件中包含这激活邮件
        # 激活链接, /user/active/用户ID
        # 存在问题: 其他用户恶意请求网站进行用户激活操作
        # 解决问题:对用户的信息进行加密，把加密后的信息放在激活链接中，激活的时候在进行解密
        # /user/active/加密后token信息

        # 对用户的身份信息进行加密, 激活生成token信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        # 返回bytes类型
        token = serializer.dumps(info)
        # str
        token = token.decode()

        # 1.组织邮件信息
        # subject = 'Welcome'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = """
        #     <h1>%s,欢迎您成为天天生鲜注册会员</h1>
        #     请点击一下链接激活您的账号(1小时之内有效)<br/>
        #     <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
        #
        # """ %(username, token, token)

        # 2.send_email参数
        # send_mail(
        #     subject='邮件标题',
        #     message='邮件正文',
        #     from_email='发件人',
        #     recipient_list='收件人列表',
        # )
        # 模拟send_mail发送邮件
        # import time
        # time.sleep(5)
        # send_mail(subject, message, sender, receiver, html_message=html_message)

        # 使用celery 发送邮件任务
        from celery_tasks.tasks import send_register_active_email
        send_register_active_email.delay(email, username, token)

        # 4. 返回应答: 跳转首页
        return redirect(reverse('good:index'))

# /user/active/加密token
class ActiveView(View):
    """激活"""
    def get(self, request, token):
        # 创建serializer对象
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:

            # 解密
            info = serializer.loads(token)
            # 获取待激活用户Id
            user_id = info['confirm']
            # 激活用户
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转登录页面
            return redirect(reverse('user:logi'))
        except SignatureExpired as e:
            # 激活链接已失效
            # 实际开发:返回页面,再次点击链接发送激活邮件
            return HttpResponse('激活链接已失效')

# user/login
class LoginView(View):
    """登录"""
    def get(self, request):
        """显示"""
        # 判断用户是否记住用户名
        username = request.COOKIES.get('username')

        checked = 'checked'
        if username is None:
            # 没有记住用户名
            username = ''
            checked = ''

        # 使用模板, 记住用户名
        return render(request, 'login.html', {'username': username, 'checked': checked})
    def post(self, request):
        """登录校验"""
        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')  # None

        # 2.参数校验(后端校验)
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '参数不完整'})

        # 3.业务处理:登录校验
        user = authenticate(username=username, password=password)

        if user is not None:
            # 用户名和密码正确
            if user.is_active:
                # 用户已激活, 记住用户的登录状态
                login(request, user)

                # 获取用户登录之前访问的url,默认跳转到首页
                next_url = request.GET.get('next', reverse('good:index'))
                # print(next_url)
                # 定向跳转到首页
                response = redirect(next_url)  # HttpResponseRedirect

                # 判断是否记住用户名
                if remember == 'on':
                    # 设置cookie set name
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')
                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'用户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


class LogoutView(View):
    """退出"""
    def get(self, request):
        # 清楚用户登录状态
        logout(request)
        # 跳转到登录
        return redirect(reverse('user:login'))


# mixin 两种不一样的视图校验
# UserInfoView----->在URL中校验 login_required(), login_required(UserInfoView)
# 方式二:
# class UserInfoView(LoginRequiredView):--->View
# class UserInfoView(LoginRequiredMixin, View):----> object

class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        """显示"""
        user = request.user
        address = Address.objects.get_default_address(user)

        conn = get_redis_connection('default')
        # 拼接key
        history_key = 'history_%d' % user.id
        sku_ids = conn.lrange(history_key, 0, 4)
        skus = []
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            skus.append(sku)

        # 模板内容
        context = {
            'address': address,
            'skus': skus,
            'page': 'user'
        }

        return render(request, 'user_center_info.html', context)


#  /user/order/页码
class UserOrderView(LoginRequiredMixin, View):
    """用户定带你中心页"""
    def get(self, request, page):
        # 获取登录用户
        user = request.user
        # 获取用户的所有订单信息
        orders = OrderInfo.objects.filter(user=user).order_by()

        # 遍历获取每一个订单对应的订单商品的信息
        for order in orders:
            # 获取订单商品的信息
            order_skus = OrderGoods.objects.filter(order=order)

            # 遍历order_skus计算订单中每件商品的小计
            for order_sku in order_skus:
                # 计算订单商品的小计
                amount = order_sku.price * order_sku.count
                # 给order_sku增加属性amount, 保存订单中每个商品的小计
                order_sku.amount = amount
            # 获取订单状态名称和计算订单实付款
            order.status_title = OrderInfo.ORDER_STATUS[order.order_status]
            order.total_pay = order.total_price + order.transit_price

            # 给order对象增加属性order_skus,包含订单中订单商品的信息
            order.order_skus = order_skus




