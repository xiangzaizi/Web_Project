from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU

# /cart/add
class CartAddView(View):
    """添加购物车记录"""
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({"res": 0, "errmsg": "请先登录"})

        # 1.获取参数, 商品id + 数量
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 2.校验参数的完整性
        if not all([sku_id, count]):
            return JsonResponse({"res": 1, "errmsg": "数据不完整"})

        # 3.校验商品id
        try:
            sku = GoodsSKU.objects.get(sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({"res": 2, "errmsg": "商品信息错误"})

        # 校验商品数据count
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({"res": 3, "errmsg": "商品信息必须为有效数字"})

        # 业务处理: 购物车记录添加
        # 获取redis连接
        conn = get_redis_connection("default")

        # 拼接key, 购物车id就是此用户的id
        cart_key = 'cart_%d' % user.id

        # 将数据存入redis
        cart_count = conn.hget(cart_key)
        if cart_count:
            # 如果用户的购物车中已经添加过sku_id商品, 购物车中对应的商品数目需要进行累加
            count += int(cart_count)

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({"res": 4, "errmsg": "商品库存不足"})

        # 设置用户购物车中sku_id商品的数量
        # hset(key, field, value) 存在就是修改,不存在就是新增
        conn.hset(cart_key, sku_id, count)

        # 返回响应数据
        return JsonResponse({"res": 5, "cart_count": cart_count, "errmsg": "添加购物车记录成功"})



