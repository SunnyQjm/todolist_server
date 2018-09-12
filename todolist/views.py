# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from todolist.models import Task
from todolist import permissions
from rest_framework.views import APIView
from rest_framework_jwt.views import ObtainJSONWebToken, RefreshJSONWebToken
from rest_framework.response import Response
from todolist.serializers import TaskSerializer, UserSerializer
from rest_framework import generics, status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.utils import six
from rest_framework.serializers import Serializer
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework_jwt.settings import api_settings
from datetime import datetime


#################################################
# 一些辅助类
#################################################

class JsonResponse(Response):
    """
    自定义Response，返回固定格式的数据
    {
        "code": 状态玛,
        "data": 数据,
        "msg": 返回数据描述
    }
    """

    def __init__(self, data=None, code=None, msg=None, status=None,
                 exception=False, headers=None, content_type="application/json",
                 template_name=None):
        super(Response, self).__init__(None, status=status)
        if isinstance(data, Serializer):
            msg = (
                'You passed a Serializer instance as data, but '
                'probably meant to pass serialized `.data` or '
                '`.error`. representation.'
            )
            raise AssertionError(msg)
        self.data = {
            "code": code,
            "msg": msg,
            "data": data
        }
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type,

        if headers:
            for name, value in six.iteritems(headers):
                self[name] = value


def pageJsonResponse(objs, request, Serializer):
    """
    objs : 实体对象
    request : 请求对象
    Serializer : 对应实体对象的序列化
    """
    try:
        page_size = int(request.GET.get('page_size', default=10))
        page = int(request.GET.get('page', default=1))
    except (TypeError, ValueError):
        return JsonResponse(code=status.HTTP_400_BAD_REQUEST, msg='page_size and page must be integer')

    paginator = Paginator(objs, page_size)
    total = paginator.num_pages  # 总页数
    try:
        objs = paginator.page(page)
    except PageNotAnInteger:
        objs = paginator.page(1)
    except EmptyPage:       # 如果页数比总页数大，就返回空列表
        objs = []

    serializer = Serializer(objs, many=True)

    return JsonResponse(data={
        'page': page,
        'totalPage': total,
        'pageSize': page_size,
        'detail': serializer.data,
    }, code=status.HTTP_200_OK, msg='page success')


# Create your views here.


################################################
# 用户管理相关接口
################################################

# 下面两个函数用于生成token
jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


class Register(APIView):
    """
    用户注册接口，注册成功之后会返回一个token，可以直接使用
    """
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            payload = jwt_payload_handler(serializer.instance)
            token = jwt_encode_handler(payload)
            result = {'token': token, 'user': serializer.data}
            return JsonResponse(code=status.HTTP_200_OK, msg='create user success', data=result)
        else:
            return JsonResponse(code=status.HTTP_400_BAD_REQUEST, msg=serializer.errors)


def dealTokenPost(view, request, msg=''):
    serializer = view.get_serializer(data=request.data)

    if serializer.is_valid():
        user = serializer.object.get('user') or request.user
        token = serializer.object.get('token')
        response_data = jwt_response_payload_handler(token, user, request)
        response_data['user'] = UserSerializer(user).data
        response = JsonResponse(code=status.HTTP_200_OK, data=response_data, msg='login success')
        if api_settings.JWT_AUTH_COOKIE:
            expiration = (datetime.utcnow() +
                          api_settings.JWT_EXPIRATION_DELTA)
            response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                token,
                                expires=expiration,
                                httponly=True)
        return response

    return JsonResponse(msg=serializer.errors, code=status.HTTP_400_BAD_REQUEST)


class Login(ObtainJSONWebToken):
    """
    用户登陆接口，登陆成功之后返回一个token以及用户的信息
    """
    def post(self, request, *args, **kwargs):
        return dealTokenPost(self, request, 'login success')


class UpdateToken(RefreshJSONWebToken):
    """
    对于没有过期的token，可以凭借旧的token获取一个新的有效的token
    """
    def post(self, request, *args, **kwargs):
        return dealTokenPost(self, request, 'update token success')


################################################
#  Task 相关接口
######################################
##########

# class getTaskList(generics.ListAPIView):
#     serializer_class = TaskSerializer
#     permission_classes = (IsAuthenticated,)
#
#     def get_queryset(self):

#         user = self.request.user
#         queryset = Task.objects.filter(owner=user)
#         return queryset


class getTaskList(APIView):
    """
    获取一个用户的任务列表
    """

    def get(self, request, format=None):
        user = request.user
        tasks = Task.objects.filter(owner=user)
        return pageJsonResponse(tasks, request, TaskSerializer)


class TaskDetail(APIView):
    """
    对一个任务详情的一系列操作
    """
    permission_classes = (IsAuthenticated, permissions.IsOwnerReadOnly)

    def get(self, request, pk):
        """
        获取一个任务的详情
        :param request:
        :param pk:
        :return:
        """
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return JsonResponse(code=status.HTTP_404_NOT_FOUND, msg='task not found')
        self.check_object_permissions(request, task)
        result = TaskSerializer(task)
        return JsonResponse(data=result.data, code=status.HTTP_200_OK, msg='Get task detail success')

    def put(self, request, pk):
        """
        更新一个任务
        :param request:
        :param pk:
        :return:
        """
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return JsonResponse(code=status.HTTP_404_NOT_FOUND, msg='task not found')
        self.check_object_permissions(request, task)
        # 验证用户欲修改的对象是否属于这个用户
        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(code=status.HTTP_200_OK, msg='update success', data=serializer.data)
        else:
            return JsonResponse(code=status.HTTP_400_BAD_REQUEST, msg=serializer.error_messages)

    def delete(self, request, pk):
        """
        删除一个任务
        :param request:
        :param pk:
        :return:
        """
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return JsonResponse(code=status.HTTP_404_NOT_FOUND, msg='task not found')
        # 验证用户欲删除的对象是否属于这个用户
        self.check_object_permissions(request, task)
        return JsonResponse(code=status.HTTP_200_OK, msg='delete success')


class addTask(APIView):
    """
    添加一个任务
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        self.check_permissions(request)
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return JsonResponse(code=status.HTTP_200_OK, msg='add success', data=serializer.data)
        else:
            return JsonResponse(code=status.HTTP_400_BAD_REQUEST, msg=serializer.error_messages)
