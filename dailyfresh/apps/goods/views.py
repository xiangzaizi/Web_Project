from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.order.models import OrderGoods

# http://127.0.0.1:8000
# /index
class IndexView(View):
    """首页"""
    def get(self, request):
        """显示"""
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')  # None pickle

        if context is None:
            # 获取商品的分类信息
            print("设置首页缓存")
            types = GoodsType.objects.all()

            # 获取首页的轮播商品的信息
            index_banner = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页的促销活动的信息
            promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品的展示信息
            for type in types:
                # 获取type种类在首页展示的图片商品的信息和文字商品的信息
                # QuerySet
                image_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
                title_banner = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

                # 给type对象增加属性title_banner, image_banner
                # 分别保存type种类在首页展示的文字商品和图片商品的信息
                type.title_banner = title_banner
                type.image_banner = image_banner

            # 缓存数据
            context = {
                'type': types,
                'index_banner': index_banner,
                'promotion_banner': promotion_banner,
                'cart_count': 0,
            }

            # 设置首页缓存
            cache.set('index_page_data', context, 3600)

        # 判断用户是否已登录
        cart_count = 0
        if request.user.is_authenticated():
            # 获取redis链接
            conn = get_redis_connection('default')
            print(request.user.id)

            # 拼接key
            cart_key = 'cart_%s' % request.user.id

            # 获取用户购物车中商品的条目数
            # hlen(key)-->返回属性的数目
            cart_count = conn.hlen(cart_key)

        # 组织返回数据
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)  # HttpResponse


# 详情页视图
# 前段传递的参数: 商品id(sku_id)
# 思路: 1) url捕获, /goods/商品id
    #  2) get传递  /goods?sku_id=商品id
    #  3） post传递


# /goods/00001
class DetailView(View):
    """详情页视图"""
    def get(self, request, sku_id):
        """显示"""
        # 获取商品的详情信息
        try:
            # sku,该商品
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在, 跳转到首页
            return redirect(reverse('goods:index'))

        # 获取商品分类的信息
        types = GoodsType.objects.all()

        # 1. 获取商品的评论信息  ,没有评论 + 评论安装更新的时间排序
        order_skus = OrderGoods.objects.filter(sku=sku).exclude(comment='').order_by('-update_time')

        # 获取和商品同一个SPU的其他规格的商品(同一商品不同的包装), sku.goods该商品的不同种类
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku_id)

        # 2. 获取和商品同一种类的两个新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 3. 如果用户登录, 获取用户购物车中的商品条目数
        cart_count = 0
        if request.user.is_authenticated():
            # 获取redis链接
            conn = get_redis_connection('default')

            # 拼接key
            cart_key = 'cart_%s' % request.user.id

            # 获取用户购物车中商品的条目数
            # hlen(key)-->返回属性的条目
            cart_count = conn.hlen(cart_key)

            # 添加用户的浏览记录
            # 拼接key
            history_key = 'history_%s' % request.user.id

            # 先尝试从redis对应列表中移除sku_id
            # lrem(key, count, value) 如果存在就移除,如果不存在什么都不做
            conn.lrem(history_key, 0, sku_id)

            # 把sku_id添加到redis对应列表左侧
            # lpush(key, *args)
            conn.lpush(history_key, sku_id)

            # 只保存用户最新浏览的5个商品的id
            # ltrim(key, start, stop)
            conn.ltrim(history_key, 0, 4)

        # 组织模板数据
        context = {
            'sku': sku,
            'types': types,
            'order_skus': order_skus,
            'same_spu_skus': same_spu_skus,
            'new_skus': new_skus,
            'cart_count': cart_count
        }

        # 返回响应
        return render(request, 'detail.html', context)

# 列表页
# 前端传递的参数: 种类id(type_id) 页码(page) 排序方式(sort)
# /list?type_id=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式

class ListView(View):
    """列表页"""
    def get(self, request, type_id, page):
        """显示"""
        # 获取type_id对应的商品种类的信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在，跳转到首页
            return redirect(reverse('goods:index'))

        # 获取所有商品种类的信息
        types = GoodsType.objects.all()

        # 获取排序方式
        # sort=price: 按照商品的价格(price)从低到高排序
        # sort=hot: 按照商品的人气(sales)从高到底排序
        # sort=default: 按照默认排序的方式(id)从高到低排序
        sort = request.GET.get('sort')

        # 获取type种类的商品信息
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort=='hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            # 按照默认顺序来排序
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 分页操作
        from django.core.paginator import Paginator
        paginator = Paginator(skus, 1)

        page = int(page)

        if page > paginator.num_pages:
            # 默认获取第一页的内容
            page = 1

        # 获取第page页内容, 返回Page类的实例对象
        skus_page = paginator.page(page)

        # 页码处理
        # 如果分页之后页码超过5页,最多在页面上只显示5个页码: 当前页前2页, 当前页, 当前页后2页
        # 1) 分页页码小于5页, 显示全部页码
        # 2) 当前页属于1-3页, 显示1-5页
        # 3) 当前页属于后3页, 显示后5页
        # 4) 其他请求, 显示当前页前2页, 当前页, 当前页后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            # 1-num_pages
            pages = range(1, num_pages+1)
        elif page<=3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            # num_page -4, num_pages
            pages = range(num_pages-4, num_pages+1)
        else:
            # page-2, page+2
            pages = range(page-2, page+3)

        # 获取type种类的2个新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 如果用户登录, 获取用户购物车中商品的条目数
        cart_count = 0
        if request.user.is_authenticated():
            # 获取redis链接
            conn = get_redis_connection('default')

            # 拼接key
            cart_key = 'cart_%s' % request.user.id

            # 获取用户购物车中商品的条目数
            # hlen(key) --> 返回属性的数目
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文数据
        context = {
            'type': type,
            'types': types,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'sort': sort,
            'page': pages,
        }

        # 使用模板
        return render(request, 'list.html', context)
