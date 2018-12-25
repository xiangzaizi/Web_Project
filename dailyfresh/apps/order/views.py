from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django.db import transaction

from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo
from apps.user.models import Address
from utils.mixin import LoginRequiredMixin
# Create your views here.


# 提交订单页面视图
# /order/place  提交订单准备结算的页面
# 参数: 商品信息 商品总额 数量 地址 运费 付款费用
class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单的页面"""
    def post(self, request):
        # 获取登录用户
        user = request.user

        # 获取用户要购买的商品的id
        sku_ids = request.POST.getlist('sku_ids')

        # 获取用户收货地址的信息
        addrs = Address.objects.filter(user=user)

        # 获取redis连接
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d' % user.id

        # 遍历sku_ids获取用户所需要购买的商品的信息
        skus = []
        total_count = 0
        total_amount = 0
        for sku_id in sku_ids:
            # 根据id查找商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)

            # 在从redis中获取用户所要购买的商品的数量
            count = conn.hget(cart_key, sku_id)

            # 计算商品的小计
            amount = sku.price * int(count)

            # 给sku对象增加属性count 和 amount
            # 分别保存用户要购买的商品的数目和小计
            sku.count = count
            sku.amount = amount

            # 追加商品的信息
            skus.append(sku)

            # 累计计算用户要购买的商品的总件数和总金额
            total_count += int(count)
            total_amount += amount

        # 运费(手动固定.狗头JPG)
        transit_price = 10

        # 实付费
        total_pay = total_amount + transit_price

        # 组织返回数据
        context = {
            'addrs': addrs,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'sku_ids': ','.join(sku_ids)
        }

        # 返回响应数据
        return render(request, 'place_order.html', context)


# 一个订单创建的分析
# /order/commit
# 前端传递的参数: 收货地址id(addr_id) 付款的方式 用户所要购买的全部商品的id(sku_ids)
"""订单创建的流程
    1) 接收参数
    2）参数校验
    3) 组织订单信息
    4) 向df_order_info中添加一条记录
    5) 订单中包含几个商品需要向df_order_goods中添加几条记录
        5.1 将sku_ids分割成一个列表
        5.2 遍历sku_ids, 向df_order_goods中添加记录
            5.2.1 根据id获取商品的信息
            5.2.2 从redis中获取用户要购买的商品的数量
            5.2.3 向df_order_goods中添加一条记录
            5.2.4 减少商品库存,增加销量
            5.2.5 累加计算订单中商品的总数目和总价格
    6) 更新订单信息中商品的总数目和总价格
    7) 删除购物车中对应的记录
"""
# 订单事务

class OrderCommitView(View):
    """订单创建"""
    @transaction.atomic
    def post(self, request):
        # 判断 用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, "errmsg": '参数不完整'})

        # 校验地址id
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 3, 'errmsg': '非法的支付方式'})

        # 组织订单信息
        # 组织订单id: 20180316115930+用户id
        from datetime import datetime
        order_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(user.id)

        # 运费
        transit_price = 10
        # 总数目和总价格
        total_count = 0
        total_price = 0

        # 设置事物保存点
        sid = transaction.savepoint()

        try:
            # 1. todo: 向df_order_info中添加一条记录
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_count=total_count,
                total_price=total_price,
                transit_price=transit_price
            )
            # 2. todo: 订单中包含几个商品需要向df_order_goods中添加几条记录
            # 连接redis
            connt = get_redis_connection('default')
            # 拼接key
            cart_key = 'cart_%d' % user.id

            # 将sku_ids 分割成一个列表
            sku_ids = sku_ids.split(',')  # [3,4]

            # 3. todo 遍历sku_ids, 向df_order_goods中添加记录
            for sku_id in sku_ids:
                for i in range(3):
                    # 根据id获取商品的信息
                    try:
                       sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 回滚事务到sid保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})
        except:
            pass




