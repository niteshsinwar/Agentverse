from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.ToolViewSet, basename='tool')

urlpatterns = [path('', include(router.urls))]
