"""
Legal corpus ingestion pipeline.

Loads legal documents (Motor Vehicles Act, CMVR, state rules, penalty schedules,
insurance/accident rules, driving licence rules, etc.) from the data/legal_corpus
directory, splits them into section-aware chunks with rich metadata, and stores
embeddings in ChromaDB for RAG retrieval.
"""
import json
import os
import re
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader

from app.rag.embeddings import get_embedding_function
from app.rag.retriever import get_chroma_client, LEGAL_COLLECTION
from app.core.logging import get_logger

logger = get_logger(__name__)

LEGAL_CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "legal_corpus")
FINE_SCHEDULES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fine_schedules")

SECTION_PATTERN = re.compile(
    r"(?:Section|Sec\.?|S\.?)\s*(\d+[A-Z]?)", re.IGNORECASE
)

RULE_PATTERN = re.compile(
    r"(?:Rule)\s*(\d+[A-Z]?)", re.IGNORECASE
)

STATE_KEYWORDS = {
    "delhi": "delhi",
    "uttar pradesh": "uttar_pradesh",
    "uttarakhand": "uttarakhand",
    "himachal pradesh": "himachal_pradesh",
    "punjab": "punjab",
    "haryana": "haryana",
    "chandigarh": "chandigarh",
    "jammu & kashmir": "jammu_kashmir",
    "jammu and kashmir": "jammu_kashmir",
    "ladakh": "ladakh",
    "rajasthan": "rajasthan",
    "gujarat": "gujarat",
    "maharashtra": "maharashtra",
    "goa": "goa",
    "madhya pradesh": "madhya_pradesh",
    "chhattisgarh": "chhattisgarh",
    "tamil nadu": "tamil_nadu",
    "kerala": "kerala",
    "karnataka": "karnataka",
    "andhra pradesh": "andhra_pradesh",
    "telangana": "telangana",
    "puducherry": "puducherry",
    "lakshadweep": "lakshadweep",
    "west bengal": "west_bengal",
    "bihar": "bihar",
    "jharkhand": "jharkhand",
    "odisha": "odisha",
    "andaman": "andaman_nicobar",
    "assam": "assam",
    "meghalaya": "meghalaya",
    "tripura": "tripura",
    "mizoram": "mizoram",
    "manipur": "manipur",
    "nagaland": "nagaland",
    "arunachal pradesh": "arunachal_pradesh",
    "sikkim": "sikkim",
}

FILENAME_TO_TOPIC = {
    "motor_vehicles_act": "mv_act",
    "central_motor_vehicles_rules": "cmvr",
    "mv_act_penalties": "penalties",
    "driving_license": "driving_licence",
    "vehicle_registration": "registration",
    "traffic_violations": "legal_remedies",
    "insurance_accident": "insurance_claims",
    "road_safety": "road_safety",
    "commercial_vehicle": "commercial_vehicles",
    "echallan": "echallan_digital",
    "state_rules_north": "state_rules",
    "state_rules_south": "state_rules",
    "state_rules_west": "state_rules",
    "state_rules_east": "state_rules",
}


def detect_section(text: str) -> str:
    match = SECTION_PATTERN.search(text)
    return match.group(1) if match else "unknown"


def detect_rule(text: str) -> Optional[str]:
    match = RULE_PATTERN.search(text)
    return match.group(1) if match else None


def detect_topic_from_filename(filename: str) -> str:
    filename_lower = filename.lower()
    for key, topic in FILENAME_TO_TOPIC.items():
        if key in filename_lower:
            return topic
    return "general"


def detect_state_from_content(text: str) -> str:
    text_lower = text.lower()
    for keyword, state_key in STATE_KEYWORDS.items():
        if keyword in text_lower:
            return state_key
    return "central"


def detect_state_from_filename(filename: str) -> str:
    filename_lower = filename.lower()
    if "state_rules_north" in filename_lower:
        return "multi_state_north"
    if "state_rules_south" in filename_lower:
        return "multi_state_south"
    if "state_rules_west" in filename_lower:
        return "multi_state_west"
    if "state_rules_east" in filename_lower or "northeast" in filename_lower:
        return "multi_state_east_northeast"
    return "central"


def load_documents(directory: str) -> List[Document]:
    documents = []
    if not os.path.exists(directory):
        logger.warning(f"Directory not found: {directory}")
        return documents

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            for doc in docs:
                doc.metadata["filename"] = filename
            documents.extend(docs)
        elif filename.endswith((".txt", ".md")):
            loader = TextLoader(filepath, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["filename"] = filename
            documents.extend(docs)

    logger.info(f"Loaded {len(documents)} documents from {directory}")
    return documents


def load_fine_schedules_as_documents() -> List[Document]:
    """Load JSON fine schedules as text documents for RAG ingestion."""
    documents = []
    if not os.path.exists(FINE_SCHEDULES_DIR):
        logger.warning(f"Fine schedules directory not found: {FINE_SCHEDULES_DIR}")
        return documents

    for filename in os.listdir(FINE_SCHEDULES_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(FINE_SCHEDULES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            state_name = data.get("state", filename.replace(".json", ""))
            lines = [
                f"TRAFFIC FINE SCHEDULE — {state_name.upper()}",
                f"Description: {data.get('description', '')}",
                f"Effective date: {data.get('effective_date', 'N/A')}",
                f"Notes: {data.get('notes', '')}",
                "",
            ]
            for sec_num, sec_data in data.get("sections", {}).items():
                lines.append(f"Section {sec_num}: {sec_data.get('offense', '')}")
                if sec_data.get("first_offense"):
                    lines.append(f"  First offence fine: Rs {sec_data['first_offense']}")
                if sec_data.get("repeat"):
                    lines.append(f"  Repeat offence fine: Rs {sec_data['repeat']}")
                if sec_data.get("imprisonment"):
                    lines.append(f"  Imprisonment: {sec_data['imprisonment']}")
                if sec_data.get("license_action"):
                    lines.append(f"  Licence action: {sec_data['license_action']}")
                if sec_data.get("notes"):
                    lines.append(f"  Note: {sec_data['notes']}")
                lines.append("")

            text = "\n".join(lines)
            state_key = state_name.lower().replace(" ", "_")
            doc = Document(
                page_content=text,
                metadata={
                    "source": filepath,
                    "filename": filename,
                    "state": state_key,
                    "topic": "fine_schedule",
                    "act": "Motor Vehicles Act 1988",
                },
            )
            documents.append(doc)
        except Exception as e:
            logger.warning(f"Failed to load fine schedule {filename}: {e}")

    logger.info(f"Loaded {len(documents)} fine schedule documents")
    return documents


def create_section_aware_chunks(documents: List[Document]) -> List[Document]:
    """Split documents while preserving section/rule metadata and enriching with topic/state."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=[
            "\nSection ",
            "\nSec. ",
            "\nRule ",
            "\n## ",
            "\n### ",
            "\n\n",
            "\n",
            ". ",
        ],
    )

    chunks = []
    for doc in documents:
        filename = doc.metadata.get("filename", "")
        file_topic = detect_topic_from_filename(filename)
        file_state = detect_state_from_filename(filename)

        splits = splitter.split_documents([doc])
        for split in splits:
            section = detect_section(split.page_content)
            rule = detect_rule(split.page_content)
            chunk_state = detect_state_from_content(split.page_content)
            if chunk_state == "central" and file_state != "central":
                chunk_state = file_state

            existing_state = split.metadata.get("state")
            if existing_state and existing_state != "central":
                chunk_state = existing_state

            split.metadata.update({
                "section": section,
                "rule": rule or "unknown",
                "topic": split.metadata.get("topic", file_topic),
                "act": split.metadata.get("act", "Motor Vehicles Act 1988"),
                "state": chunk_state,
                "year": split.metadata.get("year", "2019"),
            })
            chunks.append(split)

    logger.info(f"Created {len(chunks)} section-aware chunks from {len(documents)} documents")
    return chunks


def is_corpus_ingested() -> bool:
    """Check whether the legal corpus has already been ingested into ChromaDB."""
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name=LEGAL_COLLECTION)
        count = collection.count()
        logger.info(f"ChromaDB '{LEGAL_COLLECTION}' collection has {count} documents")
        return count > 0
    except Exception as e:
        logger.warning(f"Could not check ChromaDB collection: {e}")
        return False


def ingest_legal_corpus() -> int:
    """Main ingestion entrypoint. Returns number of chunks ingested."""
    documents = load_documents(LEGAL_CORPUS_DIR)

    fine_schedule_docs = load_fine_schedules_as_documents()
    documents.extend(fine_schedule_docs)

    if not documents:
        logger.warning("No legal documents found to ingest")
        return 0

    logger.info(
        f"Total documents loaded: {len(documents)} "
        f"(legal corpus: {len(documents) - len(fine_schedule_docs)}, "
        f"fine schedules: {len(fine_schedule_docs)})"
    )

    chunks = create_section_aware_chunks(documents)

    client = get_chroma_client()
    try:
        client.delete_collection(name=LEGAL_COLLECTION)
        logger.info(f"Deleted existing '{LEGAL_COLLECTION}' collection for fresh ingestion")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=LEGAL_COLLECTION,
        metadata={"description": "Indian traffic law legal corpus — all states and UTs"},
    )

    embedding_fn = get_embedding_function()
    batch_size = 100

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c.page_content for c in batch]
        metadatas = []
        for c in batch:
            meta = {k: str(v) if v is not None else "unknown" for k, v in c.metadata.items()}
            metadatas.append(meta)
        ids = [f"legal_{i + j}" for j in range(len(batch))]

        embeddings = embedding_fn.embed_documents(texts)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total += len(batch)
        logger.info(f"Ingested batch {i // batch_size + 1}: {len(batch)} chunks (total: {total})")

    logger.info(f"Ingestion complete. Total chunks: {total}")
    return total
