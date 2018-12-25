from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU
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
