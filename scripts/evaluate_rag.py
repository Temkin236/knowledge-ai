"""Repeatable RAG evaluation script measuring retrieval hit rate, faithfulness, citation validity, and latency."""

import asyncio
import json
import os
import sys
import time
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.base import Base
from app.rag.graph import build_rag_workflow
from app.rag.prompts import FALLBACK_INSUFFICIENT_EVIDENCE
from app.rag.state import RAGState
from app.repositories.collection_repository import CollectionRepository
from app.services.ingestion.pipeline import IngestionPipeline
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

EVALUATION_DATASET = [
    {
        "id": "eval-1",
        "question": "What is the logical qubit count and error threshold of the Aurora-7 processor?",
        "expected_facts": ["256", "99.98%"],
        "is_answerable": True,
    },
    {
        "id": "eval-2",
        "question": "At what temperature does the cooling apparatus operate and what refrigerant is used?",
        "expected_facts": ["15 millikelvin", "helium-3"],
        "is_answerable": True,
    },
    {
        "id": "eval-3",
        "question": "How much was invested in the project and what are the projected Q4 operating margins?",
        "expected_facts": ["420 million", "34%"],
        "is_answerable": True,
    },
    {
        "id": "eval-4",
        "question": "What was the founder's favorite programming language in college?",
        "expected_facts": [],
        "is_answerable": False,  # Must trigger abstention
    },
    {
        "id": "eval-5",
        "question": "Which stock exchange did Helios Labs file its IPO on in 2024?",
        "expected_facts": [],
        "is_answerable": False,  # Must trigger abstention
    },
]


async def run_evaluation():
    print("=" * 70)
    print("KNOWLEDGE AI — LIGHTWEIGHT RAG BENCHMARK & EVALUATION")
    print("=" * 70)

    # 1. Setup isolated in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async with session_factory() as session:
        # 2. Ingest benchmark fixture
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        col_repo = CollectionRepository(session)
        col = await col_repo.create(user_id, "Benchmark Collection")
        await session.commit()

        fixture_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../backend/tests/fixtures/quantum_computing_report.md")
        )
        with open(fixture_file, "rb") as f:
            file_bytes = f.read()

        pipeline = IngestionPipeline(session)
        doc, _ = await pipeline.register_document(
            owner_id=user_id,
            collection_id=col.id,
            filename="quantum_computing_report.md",
            content_type="text/markdown",
            file_bytes=file_bytes,
        )
        await session.commit()
        await pipeline.process_document(doc.id, file_bytes, "quantum_computing_report.md")

        print(f"[*] Ingested benchmark document with {doc.chunk_count} chunks into collection {col.id}\n")

        # 3. Evaluate Questions
        results = []
        retrieval_hits = 0
        total_answerable = 0
        abstention_successes = 0
        total_unanswerable = 0
        valid_citation_count = 0
        total_citations = 0
        latencies = []

        workflow = build_rag_workflow(session)

        for item in EVALUATION_DATASET:
            q_id = item["id"]
            question = item["question"]
            is_answerable = item["is_answerable"]
            expected = item["expected_facts"]

            conv_id = uuid.uuid4()
            start_t = time.time()

            state: RAGState = {
                "collection_id": str(col.id),
                "owner_id": str(user_id),
                "conversation_id": str(conv_id),
                "query": question,
                "history": [],
                "retry_count": 0,
                "retrieved_chunks": [],
                "evidence_sufficient": True,
                "raw_answer": "",
                "final_answer": "",
                "citations": [],
                "retrieval_metadata": {},
            }

            final_state = await workflow.ainvoke(state)
            duration = time.time() - start_t
            latencies.append(duration)

            answer = final_state.get("final_answer", "")
            citations = final_state.get("citations", [])
            retrieved = final_state.get("retrieved_chunks", [])

            # Check retrieval hit
            has_hit = len(retrieved) > 0

            # Check citation validity
            valid_cits = all(c.get("filename") == "quantum_computing_report.md" for c in citations)
            if citations and valid_cits:
                valid_citation_count += len(citations)
            total_citations += len(citations)

            # Check faithfulness / abstention
            passed = False
            if is_answerable:
                total_answerable += 1
                if has_hit:
                    retrieval_hits += 1
                # Check expected keywords in answer or evidence
                facts_found = all(f.lower() in answer.lower() for f in expected)
                passed = facts_found and len(citations) > 0 and answer != FALLBACK_INSUFFICIENT_EVIDENCE
            else:
                total_unanswerable += 1
                # Must abstain
                passed = answer == FALLBACK_INSUFFICIENT_EVIDENCE and len(citations) == 0
                if passed:
                    abstention_successes += 1

            results.append({
                "id": q_id,
                "question": question,
                "is_answerable": is_answerable,
                "answer": answer,
                "citations_count": len(citations),
                "passed": passed,
                "duration_ms": int(duration * 1000),
            })

            status_str = "PASS" if passed else "FAIL"
            print(f"[{status_str}] {q_id}: {question[:50]}... ({int(duration*1000)}ms)")

        # 4. Summary Metrics
        hit_rate = (retrieval_hits / total_answerable) * 100 if total_answerable else 0
        abstention_rate = (abstention_successes / total_unanswerable) * 100 if total_unanswerable else 0
        citation_validity = (valid_citation_count / total_citations) * 100 if total_citations else 100
        avg_latency = (sum(latencies) / len(latencies)) * 1000 if latencies else 0

        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_queries": len(EVALUATION_DATASET),
            "retrieval_hit_rate_pct": round(hit_rate, 2),
            "abstention_accuracy_pct": round(abstention_rate, 2),
            "citation_validity_pct": round(citation_validity, 2),
            "average_latency_ms": round(avg_latency, 2),
            "results": results,
        }

        report_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../evaluation_report.json"))
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 70)
        print("EVALUATION SUMMARY REPORT:")
        print(f"Retrieval Hit Rate (Answerable): {hit_rate:.1f}%")
        print(f"Abstention Accuracy (Unanswerable): {abstention_rate:.1f}%")
        print(f"Citation Validity Rate: {citation_validity:.1f}%")
        print(f"Average Latency: {avg_latency:.1f}ms")
        print(f"Saved report to: {report_file}")
        print("=" * 70)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_evaluation())
