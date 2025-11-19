from rest_framework import viewsets
from apps.core.permissions import IsAdminOrReadOnly
from .models import Agent
from .serializers import AgentSerializer

class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [IsAdminOrReadOnly]
