from .models import DiagnosticRequest

class LLMService:
    @staticmethod
    def get_local_diagnostic(server, query):
        """
        Simulates a local LLM diagnostic.
        """
        return f"[LOCAL LLM] Diagnosis for server {server.name}: Resources are sufficient. Recommendation: check application logs."

    @staticmethod
    def get_cloud_diagnostic(server, query):
        """
        Simulates a premium cloud LLM diagnostic.
        """
        return f"[CLOUD PREMIUM LLM] Advanced analysis for server {server.name}: Potential memory leak detected in background worker. Recommendation: upgrade to higher tier or optimize codebase."

class RouterService:
    # Thresholds for routing
    MIN_CPU_CORES = 4
    MIN_MEMORY_BYTES = 8 * 1024 * 1024 * 1024  # 8GB

    @classmethod
    def route_request(cls, server):
        """
        Routes the request to LOCAL if resources are sufficient, otherwise CLOUD.
        """
        if server.cpu_cores and server.cpu_cores >= cls.MIN_CPU_CORES and            server.memory_total and server.memory_total >= cls.MIN_MEMORY_BYTES:
            return DiagnosticRequest.Routing.LOCAL
        return DiagnosticRequest.Routing.CLOUD

    @classmethod
    def process_diagnostic(cls, user, server, query):
        """
        Processes the diagnostic request based on routing logic.
        """
        routing = cls.route_request(server)

        if routing == DiagnosticRequest.Routing.LOCAL:
            response = LLMService.get_local_diagnostic(server, query)
        else:
            response = LLMService.get_cloud_diagnostic(server, query)

        return DiagnosticRequest.objects.create(
            user=user,
            server=server,
            query=query,
            routing=routing,
            response=response
        )
