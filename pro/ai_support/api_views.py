from rest_framework import views, response, status, permissions
from django.shortcuts import get_object_or_404
from pro.servers.models import Server
from .models import DiagnosticRequest
from .serializers import DiagnosticRequestSerializer, DiagnosticInputSerializer
from .services import RouterService

class AIDiagnosticAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DiagnosticInputSerializer(data=request.data)
        if serializer.is_valid():
            server = get_object_or_404(Server, id=serializer.validated_data["server_id"])
            query = serializer.validated_data["query"]

            diag = RouterService.process_diagnostic(
                user=request.user,
                server=server,
                query=query
            )

            return response.Response(
                DiagnosticRequestSerializer(diag).data,
                status=status.HTTP_201_CREATED
            )
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
