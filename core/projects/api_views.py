from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Project, Deployment
from .serializers import ProjectSerializer, DeploymentSerializer
from .services import get_deployment_logs
from ai.logsage import LogSagePreprocessor
from ai.rag import RCAPromptBuilder
from ai.client import OllamaClient
import logging

logger = logging.getLogger(__name__)

class ProjectListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create projects.
    """
    queryset = Project.objects.select_related('owner').only(
        'name', 'owner__username', 'created_at', 'updated_at', 'domain'
    )
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the owner to the current user
        serializer.save(owner=self.request.user)

class DeploymentListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to list and create deployments.
    """
    queryset = Deployment.objects.select_related('project').only(
        'project__name', 'status', 'container_id', 'container_port', 'hot_reload', 'created_at', 'updated_at'
    )
    serializer_class = DeploymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(project__owner=self.request.user).select_related('project')

class LogSageAnalysisAPIView(APIView):
    """
    API view to perform Root Cause Analysis (RCA) using LogSage and Ollama.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, deployment_id):
        deployment = get_object_or_404(Deployment, id=deployment_id, project__owner=request.user)

        # 1. Get raw logs
        raw_logs = get_deployment_logs(deployment)
        if not raw_logs:
            return Response(
                {"error": "Aucun log disponible pour ce déploiement."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2. Preprocess logs
            preprocessor = LogSagePreprocessor(max_output_lines=50)
            processed_logs = preprocessor.process(raw_logs)

            # 3. Build RCA prompt
            prompt_builder = RCAPromptBuilder(
                enable_tools=False # We don't support auto-fix via UI yet, just analysis
            )
            project_context = {
                "project_name": deployment.project.name,
                "environment": "Khamal Managed Container"
            }
            rca_prompt = prompt_builder.build_prompt(processed_logs, project_context)

            # 4. Call Ollama
            client = OllamaClient()
            analysis = client.chat(messages=rca_prompt.to_ollama_messages())

            return Response({
                "analysis": analysis,
                "logs_used": len(processed_logs)
            })

        except Exception as e:
            logger.exception(f"LogSage analysis failed for deployment {deployment_id}")
            return Response(
                {"error": f"Erreur lors de l'analyse : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
