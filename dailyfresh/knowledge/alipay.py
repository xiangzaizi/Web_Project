from alipay import AliPay
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from apps.order.models import OrderInfo
from dailyfresh import settings
from utils.mixin import LoginRequiredMixin


# alipay支付
# 订单支付
# 采用ajax post请求
# 前端需要传递的参数: order_id(订单id)
# /order/pay


class OrderPayView(View):
    """订单支付"""
    def post(self, request):
        # 登录验证
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '缺少参数'})

        # 校验订单id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1,  # 待支付
                                          pay_method=3,  # 支付宝支付
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '无效订单id'})

        # 业务处理: 调用支付宝python SDK中的api_alipay_trade_page_pay函数
        # 初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APP_ID,  # 应用APPID
            app_notify_url=settings.ALIPAY_APP_NOTIFY_URL,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,  # 应用私钥文件路径
            # 支付宝的公钥文件，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False，False代表线上环境，True代表沙箱环境
        )

        # 调用支付宝pythonSDK中的api_alipay_trade_page_pay函数
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 订单id
            total_amount=str(total_pay), # 订单实付款
            subject='天天生鲜%s' % order_id, # 订单标题
            return_url='http://127.0.0.1:8000/order/check',
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        pay_url = settings.ALIPAY_GATEWAY_URL + order_string
        print(pay_url)
        return JsonResponse({'res': 3, 'pay_url': pay_url, 'errmsg': 'OK'})


# /order/check
class OrderCheckView(LoginRequiredMixin, View):
    """订单支付结果"""
    def get(self, request):
        # 获取登录用户
        user = request.user

        # 获取用户订单id
        order_id = request.GET.get('out_trade_no')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '缺少参数'})

        # 校验订单id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1,  # 待支付
                                          pay_method=3,  # 支付宝支付
                                          )
        except OrderInfo.DoesNotExist:
            return HttpResponse('订单信息错误')

        # 业务处理: 调用Python SDK中的交易查询的接口
        # 初始化
        alipay = AliPay(
            appid=settings.ALIPAY_APP_ID,  # 应用APPID
            app_notify_url=settings.ALIPAY_APP_NOTIFY_URL,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,  # 应用私钥文件路径
            # 支付宝的公钥文件，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False，False代表线上环境，True代表沙箱环境
        )

        # 调用Python SDK 中api_alipay_trade_query

        # {
        #     "trade_no": "2017032121001004070200176844", # 支付宝交易号
        #     "code": "10000", # 网关返回码
        #     "invoice_amount": "20.00",
        #     "open_id": "20880072506750308812798160715407",
        #     "fund_bill_list": [
        #         {
        #             "amount": "20.00",
        #             "fund_channel": "ALIPAYACCOUNT"
        #         }
        #     ],
        #     "buyer_logon_id": "csq***@sandbox.com",
        #     "send_pay_date": "2017-03-21 13:29:17",
        #     "receipt_amount": "20.00",
        #     "out_trade_no": "out_trade_no15",
        #     "buyer_pay_amount": "20.00",
        #     "buyer_user_id": "2088102169481075",
        #     "msg": "Success",
        #     "point_amount": "0.00",
        #     "trade_status": "TRADE_SUCCESS", # 支付状态
        #     "total_amount": "20.00"
        # }

        # 调用Python SDK 中api_alipay_trade_query
        response = alipay.api_alipay_trade_query(out_trade_no=order_id)
        # 获取支付宝网关的返回码
        res_code = response.get('code')

        if res_code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
            # 支付成功
            # 更新订单的支付状态和支付宝交易号
            order.order_status = 4 # 待评价
            order.trade_no = response.get('trade_no')
            order.save()

            # 返回结果
            return render(request, 'pay_result.html', {'pay_result': '支付成功'})
        else:
            # 支付失败
            return render(request, 'pay_result.html', {'pay_result': '支付失败'})
