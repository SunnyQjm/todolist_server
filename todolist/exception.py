# -*- coding: utf-8 -*-

from rest_framework.views import exception_handler
from todolist import views


def custom_exception_handler(exc, context):
    """
    统一错误处理，返回统一的数据格式
    :param exc:
    :param context:
    :return:
    """
    response = exception_handler(exc, context)
    print response
    if response:
        return views.JsonResponse(msg=response.data['detail'], code=response.status_code)
    else:
        return views.JsonResponse(msg='error')
