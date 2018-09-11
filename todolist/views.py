# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from rest_framework.decorators import api_view

from todolist.models import Task
from todolist import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from todolist.serializers import TaskSerializer, UserSerializer
from rest_framework import generics, status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.utils import six
from rest_framework.serializers import Serializer
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


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


def permissionDenyResponse():
    return JsonResponse(code=status.HTTP_400_BAD_REQUEST, msg="permission deny!")

# Create your views here.


# class getTaskList(generics.ListAPIView):
#     queryset = Task.objects.all()
#     serializer_class = TaskSerializer

class Register(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = ()


################################################
#  Task 相关接口
################################################

# class getTaskList(generics.ListAPIView):
#     serializer_class = TaskSerializer
#     permission_classes = (IsAuthenticated,)
#
#     def get_queryset(self):
#         """
#         增加一个过滤，只获取自己的任务列表
#         :return:
#         """
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
    获取一个任务的详情
    """
    permission_classes = (IsAuthenticated, permissions.IsOwnerReadOnly)

    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return JsonResponse(code=status.HTTP_404_NOT_FOUND, msg='task not found')
        self.check_object_permissions(request, task)
        result = TaskSerializer(task)
        return JsonResponse(data=result.data, code=status.HTTP_200_OK, msg='Get task detail success')

    def put(self, request, pk):
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
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return JsonResponse(code=status.HTTP_404_NOT_FOUND, msg='task not found')
        self.check_object_permissions(request, task)
        return JsonResponse(code=status.HTTP_200_OK, msg='delete success')


class addTask(APIView):
    """
    添加一个任务
    """
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """
        在保存任务的时候，同时关联创建者的信息
        :param serializer:
        :return:
        """
        serializer.save(owner=self.request.user)
