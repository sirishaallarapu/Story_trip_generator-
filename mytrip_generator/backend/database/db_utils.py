
import chromadb
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ensure chroma_data directory exists
os.makedirs("./chroma_data", exist_ok=True)

try:
    client = chromadb.PersistentClient(path="./chroma_data")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
    raise RuntimeError(f"Failed to initialize ChromaDB client: {str(e)}")

def get_collection(collection_name: str):
    try:
        return client.get_or_create_collection(name=collection_name)
    except Exception as e:
        logger.error(f"Failed to get collection {collection_name}: {str(e)}")
        raise ValueError(f"Failed to get collection: {str(e)}")

def store_itinerary(itinerary_key: str, itinerary_data: dict):
    try:
        if not itinerary_key:
            raise ValueError("Itinerary key must be non-empty")
        collection = get_collection("itineraries")
        collection.add(
            ids=[itinerary_key],
            documents=[json.dumps(itinerary_data)],
            metadatas=[{"key": itinerary_key}]
        )
        logger.info(f"Stored itinerary with key: {itinerary_key}")
    except Exception as e:
        logger.error(f"Failed to store itinerary: {str(e)}")
        raise ValueError(f"Failed to store itinerary: {str(e)}")

def retrieve_itinerary(itinerary_key: str) -> dict:
    try:
        if not itinerary_key:
            raise ValueError("Itinerary key must be non-empty")
        collection = get_collection("itineraries")
        results = collection.query(
            query_texts=[itinerary_key],
            n_results=1
        )
        if results.get("ids", [[]])[0] and results.get("documents", [[]])[0]:
            return json.loads(results["documents"][0][0])
        logger.info(f"No itinerary found for key: {itinerary_key}")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve itinerary: {str(e)}")
        raise ValueError(f"Failed to retrieve itinerary: {str(e)}")
