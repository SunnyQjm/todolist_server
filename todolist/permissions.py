# -*- coding: utf-8 -*-

from rest_framework import permissions


class IsOwnerReadOnly(permissions.BasePermission):
    """
    自定义权限只允许对象的所有者访问或编辑
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

