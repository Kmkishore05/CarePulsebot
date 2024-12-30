from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain import HuggingFacePipeline

# Use a local model instead of OpenAI
local_model_name = "distilgpt2"  # Or any other compatible model

def qa_pipeline():
    # Initialize HuggingFace embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Load the FAISS vectorstore
    db = FAISS.load_local(FAISS_INDEX, embeddings)

    # Use a local model instead of OpenAI
    llm = HuggingFacePipeline.from_pretrained(local_model_name)

    # Initialize the chain with the local model
    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=db.as_retriever())
    
    return chain
