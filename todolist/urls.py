# -*- coding: utf-8 -*-
from django.conf.urls import url
from todolist import views

urlpatterns = [
    # 获取待办事项列表
    url(r'^tasklist/', views.getTaskList.as_view()),
    url(r'^addTask', views.addTask.as_view()),
    url(r'^register', views.Register.as_view()),
    url(r'^login', views.Login.as_view()),
    url(r'^updateToken', views.UpdateToken.as_view()),
    url(r'^taskDetail/(?P<pk>[0-9]+)/$', views.TaskDetail.as_view()),
]