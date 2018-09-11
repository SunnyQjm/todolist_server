from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from todolist import views

urlpatterns = [
    url(r'^tasklist/', views.getTaskList.as_view()),
    url(r'^addTask', views.addTask.as_view()),
    url(r'^register', views.Register.as_view()),
    url(r'^taskDetail/(?P<pk>[0-9]+)/$', views.TaskDetail.as_view()),
    url(r'^updateTask/(?P<id>[0-9]+)/$', views.UpdateTask.as_view()),
]