from rest_framework import viewsets
from apps.core.permissions import IsAdminOrReadOnly
from .models import Tool
from .serializers import ToolSerializer

class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    permission_classes = [IsAdminOrReadOnly]
