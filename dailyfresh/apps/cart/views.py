from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import GoodsSKU

# /cart/add
from utils.mixin import LoginRequiredMixin


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

        # 3.校验商品id, sku查询商品信息: 如sku.stock商品库存
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
        # 获取redis连接  default---默认的redis存储IP:PORT
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


# 购物车页面显示
# get /cart/

class CartInfoView(LoginRequiredMixin, View):
    """购物车页面显示"""
    def get(self, request):
        # 获取登录用户
        user = request.user

        # 从redis中获取用户的购物车记录信息
        conn = get_redis_connection('default')
        # 拼接key从redis中获取该key对应的自己购物车数据
        cart_key = "cart_%d" % user.id

        # cart_1:{'1':'2', '3':'1', '5':'2'}
        # hgetall(key) -> 返回是一个字典，字典键是商品id, 键对应值是添加的数目
        cart_dict = conn.hgetall(cart_key)

        total_count = 0
        total_amount = 0
        # 遍历获取购物车中商品的详细信息
        skus = []
        for sku_id, count in cart_dict.items():
            # 根据sku_id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)

            # 计算商品的小计
            amount = sku.price * int(count)

            # 给sku对象增加属性amount 和 count, 分别保存用户购物车中商品的小计和数量
            sku.count = count
            sku.amount = amount

            # 追缴商品的信息
            skus.append(sku)

            # 累加计算用户购物车中商品的总数目和价格
            total_count += int(count)
            total_amount += amount

        # 组织返回模板的信息
        context = {
            'total_count':total_count,
            'total_amount':total_amount,
            'skus': skus
        }

        # 返回数据
        return render(request, 'cart.html', context)


