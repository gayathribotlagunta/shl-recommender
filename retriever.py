import json
import chromadb
from chromadb.utils import embedding_functions

class SHLRetriever:
    def __init__(self, catalog_path="catalog.json"):
        self.catalog = self._load_catalog(catalog_path)
        self.client = chromadb.Client()
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="shl_assessments",
            embedding_function=self.ef
        )
        self._index_catalog()

    def _load_catalog(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def _index_catalog(self):
        # Only add if collection is empty
        if self.collection.count() > 0:
            return
        
        docs = []
        ids = []
        metadatas = []
        
        for i, item in enumerate(self.catalog):
            # Rich text for embedding
            doc = f"{item['name']}. {item.get('description', '')} Test types: {', '.join(item.get('test_types', []))}. Remote testing: {item.get('remote_testing', False)}. Adaptive: {item.get('adaptive', False)}."
            docs.append(doc)
            ids.append(str(i))
            metadatas.append({
                "name": item["name"],
                "url": item["url"],
                "test_types": ",".join(item.get("test_types", [])),
                "remote_testing": str(item.get("remote_testing", False)),
                "adaptive": str(item.get("adaptive", False)),
            })
        
        # Add in batches
        batch_size = 50
        for i in range(0, len(docs), batch_size):
            self.collection.add(
                documents=docs[i:i+batch_size],
                ids=ids[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
        
        print(f"Indexed {len(docs)} assessments into ChromaDB")

    def retrieve(self, query: str, top_k: int = 10):
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count())
        )
        
        assessments = []
        if results and results["metadatas"]:
            for meta in results["metadatas"][0]:
                assessments.append({
                    "name": meta["name"],
                    "url": meta["url"],
                    "test_type": meta["test_types"],
                    "remote_testing": meta["remote_testing"] == "True",
                    "adaptive": meta["adaptive"] == "True",
                })
        
        return assessments

    def get_by_names(self, names: list):
        """Get assessments by name for comparison."""
        results = []
        for item in self.catalog:
            for name in names:
                if name.lower() in item["name"].lower():
                    results.append(item)
                    break
        return results


# Singleton
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = SHLRetriever()
    return _retriever