from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from Documents.business.business_doc_builder import build_business_doc
from Documents.table.table_doc_builder import build_table_doc
from Documents.relations.relations_doc_builder import build_relations_doc

from sqlalchemy import create_engine, MetaData, inspect
import os

# Carrega .env
load_dotenv()

# Conexão com banco
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SCHEMA = os.getenv("DB_SCHEMA")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Inspeção do banco
inspector = inspect(engine)
schema = DB_SCHEMA

# EXEMPLOS DE CONSULTAS COM JOIN
QUERY_EXAMPLES = {
    "clientes_devedores": {
        "description": "Clientes com contas não pagas e valores devidos",
        "keywords": ["clientes devedores", "clientes que devem", "débitos por cliente", "ranking de devedores"],
        "tables_involved": ["stg_omie_listarclientes", "stg_omie_listarcontaspagar"],
        "join_example": "INNER JOIN usando codigo_cliente_omie = codigo_cliente_fornecedor"
    },

    "contas_em_atraso_com_cliente": {
        "description": "Contas atrasadas com informações completas do cliente",
        "keywords": ["contas em atraso", "clientes inadimplentes", "vencimentos atrasados"],
        "tables_involved": ["stg_omie_listarclientes", "stg_omie_listarcontaspagar"],
        "join_example": "INNER JOIN para obter dados do cliente das contas atrasadas"
    }
}

# Tabelas para processar
tabelas_para_testar = [
    "stg_omie_listarclientes",
    "stg_omie_listarprodutos",
    "stg_omie_listarcontaspagar"
]

# Embeddings com Ollama
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# Diretório de persistência
db_location = "./chrome_langchain_db"
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []

    for table_name in tabelas_para_testar:
        columns = inspector.get_columns(table_name, schema=schema)
        table_comment = inspector.get_table_comment(table_name, schema=schema)

        business_doc = build_business_doc(table_name)

        documents.append(Document(
            page_content=business_doc,
            metadata={
                "table": table_name,
                "schema": schema,
                "doc_type": "business_context",
                "full_name": f"{schema}.{table_name}"
            }
        ))

        table_doc = build_table_doc(schema,table_name,columns,table_comment)

        documents.append(Document(
            page_content=table_doc,
            metadata={
                "table": table_name,
                "schema": schema,
                "doc_type": "schema",
                "full_name": f"{schema}.{table_name}"
            }
        ))

        relations_doc = build_relations_doc(table_name)
        if relations_doc:
            documents.append(Document(
                page_content=relations_doc,
                metadata={
                    "table": table_name,
                    "doc_type": "join",
                }
            ))

    # 3. DOCUMENTOS DE EXEMPLOS DE QUERIES
    for example_name, example_info in QUERY_EXAMPLES.items():
        example_doc = f"""
TIPO DE CONSULTA: {example_info['description']}

PALAVRAS-CHAVE: {', '.join(example_info['keywords'])}

TABELAS ENVOLVIDAS: {', '.join(example_info['tables_involved'])}

COMO FAZER O JOIN: {example_info['join_example']}

QUANDO USAR: Quando o usuário perguntar sobre {', '.join(example_info['keywords'])}
        """

        documents.append(Document(
            page_content=example_doc,
            metadata={
                "doc_type": "query_example",
                "example_type": example_name,
                "keywords": ",".join(example_info['keywords']),
                "tables": ",".join(example_info['tables_involved'])
            }
        ))

# Cria vector store
vector_store = Chroma(
    collection_name="database",
    persist_directory=db_location,
    embedding_function=embeddings,
)

if add_documents:
    vector_store.add_documents(documents=documents)

def get_retriever(search_type="mixed", k=4):
    if search_type == "business":
        return vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "score_threshold": 0.4,
                "filter": {"doc_type": {"$eq": "business_context"}}
            }
        )
    elif search_type == "schema":
        return vector_store.as_retriever(
            search_kwargs={
                "k": k,
                "filter": {"doc_type": {"$eq": "schema"}}
            }
        )
    elif search_type == "relationships":
        return vector_store.as_retriever(
            search_kwargs={
                "k": k,
                "filter": {"doc_type": {"$in": ["relationships", "query_example"]}}
            }
        )
    else:
        return vector_store.as_retriever(search_kwargs={"k": k})


# Retriever padrão
retriever = get_retriever("mixed", k=5)