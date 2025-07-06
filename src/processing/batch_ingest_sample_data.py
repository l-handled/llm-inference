import os
import logging
from src.processing.validation import validate_document
from src.processing.ingest_rag import ingest_document_rag

SUPPORTED_EXTENSIONS = {"txt", "json", "pdf"}
SAMPLE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample_data"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("batch_ingest")

def main():
    logger.info(f"Batch ingesting files from {SAMPLE_DATA_DIR}")
    for fname in os.listdir(SAMPLE_DATA_DIR):
        fpath = os.path.join(SAMPLE_DATA_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        ext = fname.split(".")[-1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            logger.info(f"Skipping unsupported file: {fname}")
            continue
        try:
            with open(fpath, "rb") as f:
                doc_bytes = f.read()
            doc_content = validate_document(doc_bytes, ext)
            mongo_id = ingest_document_rag(fname, doc_content, doc_metadata=None, strategy="langchain")
            logger.info(f"Ingested {fname} (mongo_id={mongo_id})")
        except Exception as e:
            logger.error(f"Failed to ingest {fname}: {e}")

if __name__ == "__main__":
    main() 