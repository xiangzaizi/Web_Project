from django.views.generic import View
from django.contrib.auth.decorators import login_required


class LoginRequiredView(View):
    @classmethod
    def as_view(cls, **initkwargs):
        # 继承View中的as_view
        view = super().as_view(**initkwargs)

        # 调用login_required的装饰器
        return login_required(view)


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        # 继承
        view = super().as_view(**initkwargs)

        return login_required(view)