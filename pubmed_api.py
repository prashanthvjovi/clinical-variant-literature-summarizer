import requests
import xml.etree.ElementTree as ET
from typing import List, Dict


ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def search_pubmed(query: str, max_results: int = 10) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    response = requests.get(ESEARCH_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])

def fetch_abstracts(pubmed_ids: List[str]) -> List[Dict[str, str]]:
    if not pubmed_ids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "xml",
    }
    response = requests.get(EFETCH_URL, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    articles = []

    for article in root.findall(".//PubmedArticle"):
        title_node = article.find(".//ArticleTitle")
        abstract_nodes = article.findall(".//Abstract/AbstractText")
        pmid_node = article.find(".//PMID")
        year_node = article.find(".//PubDate/Year")

        title = "".join(title_node.itertext()).strip() if title_node is not None else ""
        abstract = " ".join(
            "".join(node.itertext()).strip()
            for node in abstract_nodes
            if node is not None
        ).strip()
        pmid = pmid_node.text.strip() if pmid_node is not None and pmid_node.text else ""
        year = year_node.text.strip() if year_node is not None and year_node.text else "Unknown"
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""

        if title or abstract:
            articles.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "year": year,
                "url": url,
            })

    return articles


if __name__ == "__main__":
    query = "BRCA1 mutation breast cancer"
    ids = search_pubmed(query, max_results=5)
    papers = fetch_abstracts(ids)

    for paper in papers:
        print(f"PMID: {paper['pmid']}")
        print(f"Title: {paper['title']}")
        print(f"Abstract: {paper['abstract'][:300]}...")
        print("-" * 80)