from rest_framework import viewsets
from apps.core.permissions import IsAdminOrReadOnly
from .models import MCPServer
from .serializers import MCPServerSerializer

class MCPServerViewSet(viewsets.ModelViewSet):
    queryset = MCPServer.objects.all()
    serializer_class = MCPServerSerializer
    permission_classes = [IsAdminOrReadOnly]
