from django.urls import path
from . import views

urlpatterns = [
    path('get_reports', views.getReports),
    path('get_report/<str:pk>', views.getReport),
    path('delete_report', views.deleteReport),
    path('create_report', views.createReport),
    path('update_report', views.updateReport)
]