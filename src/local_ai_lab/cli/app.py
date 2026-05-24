import argparse
import json
from pathlib import Path

from local_ai_lab.rag.factory import build_rag_service


def main() -> None:
    parser = argparse.ArgumentParser(prog="local-ai-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest markdown/text docs into Qdrant.")
    ingest_parser.add_argument("--path", type=Path, required=True)

    ask_parser = subparsers.add_parser("ask", help="Ask a question against the local RAG index.")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--top-k", type=int, default=None)
    ask_parser.add_argument("--json", action="store_true", help="Print the full response as JSON.")

    args = parser.parse_args()
    service = build_rag_service()

    if args.command == "ingest":
        result = service.ingest_path(args.path)
        print(f"Ingested {result['documents']} document(s) into {result['chunks']} chunk(s).")
        return

    if args.command == "ask":
        result = service.ask(args.question, top_k=args.top_k)
        if args.json:
            print(
                json.dumps(
                    {
                        "answer": result.answer,
                        "citations": [citation.__dict__ for citation in result.citations],
                        "retrieved_chunks": result.retrieved_chunks,
                    },
                    indent=2,
                )
            )
            return

        print(result.answer)
        if result.citations:
            print("\nCitations:")
            for citation in result.citations:
                print(
                    f"- {citation.source_name}#chunk_{citation.chunk_index} "
                    f"score={citation.score:.4f} id={citation.chunk_id}"
                )
