from fastapi import FastAPI, HTTPException

from local_ai_lab.api.schemas import AskRequest, AskResponse
from local_ai_lab.config.settings import get_settings
from local_ai_lab.llms.base import ChatProviderError
from local_ai_lab.rag.factory import build_rag_service


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    @app.post("/ask", response_model=AskResponse, response_model_exclude_none=True)
    def ask(request: AskRequest) -> AskResponse:
        service = build_rag_service(settings)
        try:
            result = service.ask(
                request.question,
                top_k=request.top_k,
                inspect_retrieval=request.inspect_retrieval,
            )
        except ChatProviderError as exc:
            raise HTTPException(
                status_code=502,
                detail="Local chat provider failed. Run `uv run local-ai-lab doctor`.",
            ) from exc
        return AskResponse(
            answer=result.answer,
            citations=[citation.__dict__ for citation in result.citations],
            retrieval_inspection=[
                inspection.__dict__ for inspection in result.retrieval_inspection
            ]
            if result.retrieval_inspection is not None
            else None,
        )

    return app
