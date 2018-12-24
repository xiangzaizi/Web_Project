from django.http import JsonResponse
from django.shortcuts import render
from django.views import View


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

