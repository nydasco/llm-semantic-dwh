#!/bin/python

from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.llms import LlamaCpp
from langchain.vectorstores import FAISS
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.document_loaders import CubeSemanticLoader
from pathlib import Path
import pandas as pd
import os
import re
import pickle
import jwt

from utils import (
    log,
    call_sql_api,
    CUBE_SQL_API_PROMPT,
    _NO_ANSWER_TEXT,
)

# Constants
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL_PATH = "/Users/admin/llama.cpp/models/OpenHermes/openhermes-2.5-mistral-7b.Q5_K_M.gguf"
VECTOR_STORE_PATH = "./chroma_db"

def ingest_cube_meta():
    security_context = {}
    token = jwt.encode(security_context, os.environ["CUBE_API_SECRET"], algorithm="HS256")

    loader = CubeSemanticLoader(os.environ["CUBE_API_URL"], token)
    documents = loader.load()

    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Save vectorstore
    with open("vectorstore.pkl", "wb") as f:
        pickle.dump(vectorstore, f)
        
if not Path("vectorstore.pkl").exists():
    ingest_cube_meta()

callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

llm = LlamaCpp(
    model_path=LLM_MODEL_PATH,
    n_gpu_layers=32,
    n_batch=512,
    n_ctx=2048,
    f16_kv=True,
    callback_manager=callback_manager,
)
llm.client.verbose = False






question = "How many settlements were there in January 2018?"

with open("vectorstore.pkl", "rb") as f:
    vectorstore = pickle.load(f)

    # log("Quering vectorstore and building the prompt...")

    docs = vectorstore.similarity_search(question)
    # take the first document as the best guess
    table_name = docs[0].metadata["table_name"]

    # Columns
    columns_question = "All available columns"
    column_docs = vectorstore.similarity_search(
        columns_question, filter=dict(table_name=table_name), k=15
    )

    lines = []
    for column_doc in column_docs:
        column_title = column_doc.metadata["column_title"]
        column_name = column_doc.metadata["column_name"]
        column_data_type = column_doc.metadata["column_data_type"]
        print(column_name)
        lines.append(
            f"title: {column_title}, column name: {column_name}, datatype: {column_data_type}, member type: {column_doc.metadata['column_member_type']}"
        )
    columns = "\n\n".join(lines)

    # Construct the prompt
    prompt = CUBE_SQL_API_PROMPT.format(
        input_question=question,
        table_info=table_name,
        columns_info=columns,
        top_k=1000,
        no_answer_text=_NO_ANSWER_TEXT,
    )

    # Call LLM API to get the SQL query
    log("Calling LLM API to generate SQL query...")
    llm_answer = llm(prompt)
    bare_llm_answer = re.sub(r"(?i)Answer:\s*", "", llm_answer)

    if llm_answer.strip() == _NO_ANSWER_TEXT:
        exit()
        
    sql_query = llm_answer

    log("Query generated by LLM:")
    print(sql_query)

    # Call Cube SQL API
    log("Sending the above query to Cube...")
    columns, rows = call_sql_api(sql_query)

    # Display the result
    df = pd.DataFrame(rows, columns=columns)
    print(df)