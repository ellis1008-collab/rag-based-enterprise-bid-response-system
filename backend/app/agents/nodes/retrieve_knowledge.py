from app.agents.state import BidAgentState, RetrievedContextState, truncate_text
from app.services.knowledge_retrieval import retrieve_knowledge


def retrieve_knowledge_node(state: BidAgentState) -> dict:
    db = state["db"]
    top_k = state.get("top_k", 3)
    retrieved_contexts: list[RetrievedContextState] = []

    for requirement in state.get("requirements", []):
        requirement_id = requirement.get("id")
        if requirement_id is None:
            raise ValueError("Requirement must be saved before knowledge retrieval.")

        chunks = retrieve_knowledge(db=db, query=requirement["content"], top_k=top_k)
        retrieved_contexts.append(
            {
                "requirement_id": requirement_id,
                "requirement_code": requirement["requirement_code"],
                "query": requirement["content"],
                "retrieved_chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "file_id": chunk.file_id,
                        "content": chunk.content,
                        "score": chunk.score,
                        "metadata": chunk.metadata,
                        "retriever_type": chunk.retriever_type,
                        "content_summary": truncate_text(chunk.content),
                    }
                    for chunk in chunks
                ],
            }
        )

    return {"retrieved_contexts": retrieved_contexts}
