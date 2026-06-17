import argparse
import json
import sys
from pathlib import Path

from local_ai_lab.cli.doctor import run_doctor
from local_ai_lab.embeddings.base import EmbeddingProviderError
from local_ai_lab.llms.base import ChatProviderError
from local_ai_lab.rag.factory import build_rag_service


def main() -> int:
    parser = argparse.ArgumentParser(prog="local-ai-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Run local health checks for the v0 stack.")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest markdown/text docs into Qdrant.")
    ingest_parser.add_argument("--path", type=Path, required=True)

    ask_parser = subparsers.add_parser("ask", help="Ask a question against the local RAG index.")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--top-k", type=int, default=None)
    ask_parser.add_argument("--json", action="store_true", help="Print the full response as JSON.")

    args = parser.parse_args()

    if args.command == "doctor":
        return run_doctor()

    if args.command == "ingest":
        service = build_rag_service()
        try:
            result = service.ingest_path(args.path)
        except EmbeddingProviderError as exc:
            print(f"Embedding provider error: {exc}", file=sys.stderr)
            return 1
        print(f"Ingested {result['documents']} document(s) into {result['chunks']} chunk(s).")
        return 0

    if args.command == "ask":
        service = build_rag_service()
        try:
            result = service.ask(args.question, top_k=args.top_k)
        except EmbeddingProviderError as exc:
            print(f"Embedding provider error: {exc}", file=sys.stderr)
            return 1
        except ChatProviderError as exc:
            print(f"Provider error: {exc}", file=sys.stderr)
            return 1
        if args.json:
            print(
                json.dumps(
                    {
                        "answer": result.answer,
                        "citations": [citation.__dict__ for citation in result.citations],
                    },
                    indent=2,
                )
            )
            return 0

        print(result.answer)
        if result.citations:
            print("\nCitations:")
            for citation in result.citations:
                print(
                    f"- {citation.source_name}#chunk_{citation.chunk_index} "
                    f"score={citation.score:.4f} id={citation.chunk_id}"
                )
        return 0

    return 1
