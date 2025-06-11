from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

db_location = "../chrome_langchain_db"
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

vector_store = Chroma(
    collection_name="database",
    persist_directory=db_location,
    embedding_function=embeddings,
)

def format(docs):
    context_part = []
    for doc in docs:
        context_part.append(f"=== SCHEMA DA TABELA {doc.metadata['table'].upper()} ===")
        context_part.append(doc.page_content)
    context = "\n\n".join(context_part)
    return context

def test_business_context():
    query = 'Liste os clientes'

    v = vector_store.similarity_search(query, k=1, filter={"doc_type": {"$eq": "business_context"}})

    v2 = [doc for doc in v]

    part=[]
    for doc in v2:
        part.append(f"CONTEXTO TABELA: {doc.metadata['table'].upper()}")
        part.append(doc.page_content)

    context = "\n\n".join(part)

    print("CONTEXTO USANDO K")
    print(context)
    print("###########################################################")


    v_sim = vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "score_threshold": 0.4,
                    "filter": {"doc_type": {"$eq": "business_context"}}
                }
            )

    x = v_sim.invoke(query)

    if x:
        v2 = [doc for doc in x]

        part = []
        for doc in v2:
            part.append(f"CONTEXTO TABELA: {doc.metadata['table'].upper()}")
            part.append(doc.page_content)
        context_sim = "\n\n".join(part)
        print(context_sim)
    else:
        print("Nenhum resultado")

def test_join_context(relevant_tables=["stg_omie_listarclientes", "stg_omie_listarcontaspagar"]):
    question = "Liste os clientes e quantas contas cada um tem"

    relations_docs = vector_store.similarity_search(
        question,
        k=2,
        filter={
            "$and": [
                {"doc_type": {"$eq": "join"}},
                {"table": {"$in": relevant_tables}}
            ]
        }
    )
    context = format(relations_docs)
    print(context)

test_join_context()