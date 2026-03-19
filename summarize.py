import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DISEASE_KEYWORDS = [
    "cancer", "tumor", "syndrome", "disease", "epilepsy", "glioma",
    "carcinoma", "disorder", "deficiency", "infection", "leukemia",
    "lymphoma", "neurodevelopmental", "autism", "cardiomyopathy"
]


def rank_articles(query: str, articles: List[Dict[str, str]], top_k: int = 5) -> List[Dict[str, str]]:
    if not articles:
        return []

    documents = [f"{a['title']} {a['abstract']}" for a in articles]
    corpus = [query] + documents

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    query_vector = tfidf_matrix[0:1]
    doc_vectors = tfidf_matrix[1:]
    scores = cosine_similarity(query_vector, doc_vectors).flatten()

    ranked = []
    for article, score in zip(articles, scores):
        item = article.copy()
        item["score"] = float(score)
        ranked.append(item)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]


def extract_key_sentences(text: str, max_sentences: int = 2) -> str:
    if not text:
        return ""

    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    selected = sentences[:max_sentences]
    if not selected:
        return ""

    joined = ". ".join(selected)
    if not joined.endswith("."):
        joined += "."
    return joined


def extract_disease_terms(text: str) -> List[str]:
    text_lower = text.lower()
    found = []

    for keyword in DISEASE_KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)

    return sorted(list(set(found)))


def extract_gene_like_terms(text: str) -> List[str]:
    # Looks for terms like BRCA1, TP53, SCN2A, EGFR, CFTR
    candidates = re.findall(r"\b[A-Z0-9\-]{3,10}\b", text)
    cleaned = []

    for term in candidates:
        if any(char.isdigit() for char in term) or term.isalpha():
            if term not in {"DNA", "RNA", "PCR", "USA"}:
                cleaned.append(term)

    return sorted(list(set(cleaned)))[:10]


def build_structured_highlights(ranked_articles: List[Dict[str, str]]) -> Dict[str, List[str]]:
    combined_text = " ".join(
        f"{article.get('title', '')} {article.get('abstract', '')}"
        for article in ranked_articles[:3]
    )

    diseases = extract_disease_terms(combined_text)
    genes = extract_gene_like_terms(combined_text)

    return {
        "disease_terms": diseases[:8],
        "gene_terms": genes[:8],
    }


def simple_summary(query: str, ranked_articles: List[Dict[str, str]]) -> str:
    if not ranked_articles:
        return "No relevant literature found."

    highlights = build_structured_highlights(ranked_articles)

    lines = []
    lines.append(f"Literature summary for: {query}")
    lines.append("")
    lines.append("Most relevant publications:")

    for i, article in enumerate(ranked_articles[:3], start=1):
        lines.append(
            f"{i}. {article['title']} "
            f"(PMID: {article['pmid']}, score: {article['score']:.3f})"
        )

    if highlights["disease_terms"]:
        lines.append("")
        lines.append("Likely disease-related terms:")
        lines.append(", ".join(highlights["disease_terms"]))

    if highlights["gene_terms"]:
        lines.append("")
        lines.append("Likely gene/variant-related terms:")
        lines.append(", ".join(highlights["gene_terms"]))

    lines.append("")
    lines.append("Key findings:")
    for article in ranked_articles[:3]:
        snippet = extract_key_sentences(article.get("abstract", ""), max_sentences=2)
        if snippet:
            lines.append(f"- {snippet}")

    return "\n".join(lines)