from django.db import transaction
from django.http import JsonResponse
from django.views import View


class OrderCommitView(View):
    """订单创建, 订单事物的使用"""
    @transaction.atomic
    def post(self, request):
        # 1. 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户不存在'})

        # 2. 接受参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 以, 分割字符串

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})



