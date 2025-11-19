from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'uploaded_by', 'file_type']

    @action(detail=False, methods=['post'])
    def upload(self, request):
        # TODO: Implement MinIO/S3 upload
        return Response({'message': 'Upload endpoint - implement MinIO integration'}, status=status.HTTP_501_NOT_IMPLEMENTED)
