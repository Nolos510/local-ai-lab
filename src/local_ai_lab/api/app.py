from fastapi import FastAPI

from local_ai_lab.api.schemas import AskRequest, AskResponse
from local_ai_lab.config.settings import get_settings
from local_ai_lab.rag.factory import build_rag_service


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        service = build_rag_service(settings)
        result = service.ask(request.question, top_k=request.top_k)
        return AskResponse(
            answer=result.answer,
            citations=[citation.__dict__ for citation in result.citations],
            retrieved_chunks=result.retrieved_chunks,
        )

    return app
