import re

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.core.mail import send_mail

from apps.user.models import User
from dailyfresh import settings


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
