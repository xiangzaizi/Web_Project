from celery import Celery
from django.conf import settings
from django.core.mail import send_mail

# 初始化django运行所依赖的环境变量
# 这两行代码在启动worker一端打开
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', "dailyfresh.setting")
django.setup()


# 创建Celery类的对象
app = Celery('celery_tasks.tasks', broker='redis://192.168.88.128:6383/1')


# 封装任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = """
            <h1>%s, 欢迎您成为天天生鲜注册会员</h1>
            请点击一下链接激活您的账号(1小时之内有效)<br/>
            <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
        """ % (username, token, token)

    import time
    time.sleep(5)
    send_mail(subject, message, sender, receiver, html_message)
    # 异步启动celery监听主程序发邮件的请求

# 项目启动: celery -A 任务函数所在文件的路径 worker -l info


