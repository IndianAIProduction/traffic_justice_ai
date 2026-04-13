"""
Ingest legal corpus into ChromaDB.
Run inside container: python run_ingestion.py
"""
from app.rag.ingestion import ingest_legal_corpus
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    logger.info("Starting legal corpus ingestion...")
    count = ingest_legal_corpus()
    if count > 0:
        logger.info(f"Successfully ingested {count} chunks into ChromaDB")
    else:
        logger.warning(
            "No documents ingested. Place legal documents (PDF/TXT) in "
            "data/legal_corpus/ and re-run."
        )


if __name__ == "__main__":
    main()
