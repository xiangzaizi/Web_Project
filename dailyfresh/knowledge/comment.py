# 订单评论
"""GET
1. 当前用户user + order_id 存在为前提
2. 获取此订单信息
3. 给订单添加一个属性order_skus
"""
# POST:
# 1. 设定评论的条数(获取评论条数)
# total_count = request.POST.get('total_count')
# total_count = int(total_count)
# 2. 循环获取订单商品的评论内容
# for i in range(1, total_count + 1):
"""id和商品信息连接起来"""
#     # 获取评论的商品的id
#     sku_id = request.POST.get('sku_%d' % i)
#     # 获取评论的商品的内容
#     content = request.POST.get('content_%d' % i, '')
#
#     try:
#         order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
#     except OrderGoods.DoesNotExist:
#         continue
#
#     # 订单评论
#     order_goods.comment = content
#     order_goods.save()



