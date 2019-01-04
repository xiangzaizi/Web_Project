# 1. user cart good order 模块中
"""
1. celery异步发送邮件 & celery生成静态文件
2. 修改django认证系统使用的用户模型类, AUTH_USER_MODEL = 'user.User'
3. 在模型类中添加方法,用户可以直接调用like token信息的生成(在MALL)项目上有使用
业务处理步骤: 接收参数 校验参数 业务处理:登录校验
4. 页面分页的处理, like用户订单页分页
5. order中给某对象增加属性, like增加合计的属性:sku.amount=amount
6. order中是如何处理订单事务
"""

# 2.redis 处理的数据
"""
1. 用户购物车中的记录信息
2.

"""

# 其他知识
"""
1. fdfs + nginx, 配置图片文件的上传
2. 支付宝接口的接入
3. 全文检索框架
"""