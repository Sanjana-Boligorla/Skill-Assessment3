import os
from openai import OpenAI
from utils.vector_store import get_vector_store


def run(state: dict) -> dict:
    parsed_files = state.get("parsed_files", [])
    if not parsed_files:
        return {**state, "ingestion_status": "No files uploaded.", "ingestion_complete": False}

    vs = get_vector_store()
    vs.reset()

    documents = []
    for f in parsed_files:
        dtype = f.get("type", "text")
        fname = f.get("filename", "file")
        if dtype == "csv":
            # Embed review texts
            for rev in f.get("reviews", []):
                text = f"Product: {rev.get('product','')} | Review: {rev.get('review','')} | Rating: {rev.get('rating','')}"
                documents.append({"text": text, "metadata": {"source": fname, "type": "review", "product": rev.get("product", "")}})
            # Embed product performance summaries
            for p in f.get("product_performance", []):
                text = (
                    f"Product: {p.get('Product_Name','')} | "
                    f"Revenue: ${p.get('Revenue_USD', 0):,.0f} | "
                    f"Profit: ${p.get('Profit_USD', 0):,.0f} | "
                    f"Units: {p.get('Units_Sold', 0)} | "
                    f"Rating: {p.get('Customer_Rating', 0):.2f}"
                )
                documents.append({"text": text, "metadata": {"source": fname, "type": "product_performance", "product": p.get("Product_Name", "")}})
        else:
            full_text = f.get("full_text", f.get("preview", ""))
            if full_text:
                documents.append({"text": full_text, "metadata": {"source": fname, "type": dtype}})

    try:
        vs.upsert_documents(documents)
        status = f"Successfully ingested {len(documents)} document chunks from {len(parsed_files)} file(s) into vector store."
        complete = True
    except Exception as e:
        status = f"Vector store ingestion partial (will use direct context): {str(e)}"
        complete = True  # continue pipeline regardless

    return {
        **state,
        "ingestion_status": status,
        "ingestion_complete": complete,
        "num_chunks": len(documents),
    }
