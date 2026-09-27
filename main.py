import os
import streamlit as st
import time

from secret_key import GOOGLE_API_KEY

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings
)

from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader
from langchain.vectorstores import FAISS


st.title("RockyBot: News Research Tool 📈")
st.sidebar.title("News Article URLs")

urls = []

for i in range(3):
    url = st.sidebar.text_input(f"URL {i+1}")
    urls.append(url)

process_url_clicked = st.sidebar.button("Process URLs")

main_placeholder = st.empty()


# Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)


# Gemini Embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    google_api_key=GOOGLE_API_KEY
)


if process_url_clicked:

    # Remove empty URLs
    urls = [url for url in urls if url.strip()]

    if not urls:
        st.error("Please enter at least one URL.")
        st.stop()

    # Load data
    main_placeholder.text("Data Loading...Started...✅")

    loader = UnstructuredURLLoader(urls=urls)
    data = loader.load()

    if not data:
        st.error("No data could be loaded from the URL.")
        st.stop()

    # Split data
    main_placeholder.text("Text Splitter...Started...✅")

    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", ","],
        chunk_size=1000,
        chunk_overlap=200
    )

    docs = text_splitter.split_documents(data)

    if not docs:
        st.error("No text chunks were created from the URL.")
        st.stop()

    # Create FAISS index
    main_placeholder.text("Building Embedding Vector...✅")

    vectorindex_gemini = FAISS.from_documents(
        docs,
        embeddings
    )

    time.sleep(2)

    # Save FAISS index
    vectorindex_gemini.save_local("vector_index")

    st.success("URLs processed successfully! ✅")


# Question
query = st.text_input("Question:")

if query:

    if not os.path.exists("vector_index"):
        st.error("Please process the URLs first.")
        st.stop()

    # Load FAISS index
    vectorindex_gemini = FAISS.load_local(
        "vector_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    # Create RAG chain
    chain = RetrievalQAWithSourcesChain.from_llm(
        llm=llm,
        retriever=vectorindex_gemini.as_retriever()
    )

    # Get answer
    result = chain.invoke({
        "question": query
    })

    # Display answer
    st.header("Answer")
    st.write(result["answer"])

    # Display sources
    sources = result.get("sources", "")

    if sources:
        st.subheader("Sources:")

        for source in sources.split("\n"):
            st.write(source)