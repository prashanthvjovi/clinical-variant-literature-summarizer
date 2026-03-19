import streamlit as st
import pandas as pd
from pubmed_api import search_pubmed, fetch_abstracts
from summarize import rank_articles, simple_summary


st.set_page_config(page_title="Clinical Variant Literature Summarizer", layout="wide")

st.title("Clinical Variant Literature Summarizer")
st.write("Search PubMed for gene, variant, or disease literature and generate a quick summary.")

query = st.text_input("Enter a gene, variant, or disease", "BRCA1 mutation breast cancer")
max_results = st.slider("Number of PubMed papers to retrieve", min_value=3, max_value=20, value=10)

if st.button("Search"):
    with st.spinner("Fetching and ranking PubMed results..."):
        ids = search_pubmed(query, max_results=max_results)
        articles = fetch_abstracts(ids)
        ranked = rank_articles(query, articles, top_k=5)
        summary = simple_summary(query, ranked)

    st.subheader("Summary")
    st.text(summary)

    if ranked:
        st.subheader("Download Results")

        df = pd.DataFrame(ranked)[["pmid", "year", "title", "score", "url", "abstract"]]
        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download ranked results as CSV",
            data=csv_data,
            file_name="ranked_pubmed_results.csv",
            mime="text/csv",
        )

    st.subheader("Top Ranked Articles")
    for article in ranked:
        with st.expander(f"{article['title']} (score: {article['score']:.3f})"):
            st.write(f"**PMID:** {article['pmid']}")
            st.write(f"**Year:** {article.get('year', 'Unknown')}")
            if article.get("url"):
                st.markdown(f"**PubMed Link:** [Open article]({article['url']})")
            if article["abstract"]:
                st.write(article["abstract"])
            else:
                st.write("_No abstract available._")