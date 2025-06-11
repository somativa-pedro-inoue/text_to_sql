from dotenv import load_dotenv
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import vector_store, get_retriever
from langchain_core.documents import Document
import os

def extract_sql(text):
    start_index = text.upper().find('SELECT')
    end_index = text.find(';')
    if start_index != -1 and end_index != -1:
        return text[start_index:end_index + 1]
    return text


def smart_retrieval(question):
    business_retriever = get_retriever("business", k=2)
    business_docs = business_retriever.invoke(question)

    if business_docs:
        relevant_tables = [doc.metadata["table"] for doc in business_docs]
        print(f"📋 Tabelas identificadas: {relevant_tables}")

        schema_docs = vector_store.similarity_search(
            question,
            k=len(relevant_tables),
            filter={
                "$and": [
                    {"doc_type": {"$eq": "schema"}},
                    {"table": {"$in": relevant_tables}}
                ]
            }
        )

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
        return business_docs + schema_docs + relations_docs
    else:
        mixed_retriever = get_retriever("mixed", k=4)
        return mixed_retriever.invoke(question)

load_dotenv()
model = OllamaLLM(model=os.getenv("OLLAMA_MODEL"))

template = """
Você é um especialista em PostgreSQL. Gere APENAS a consulta SQL usando o contexto fornecido.

REGRAS IMPORTANTES:
- Retorne APENAS a query SQL, sem explicações
- Use os nomes exatos de colunas e tabelas do schema (sempre com schema.tabela)
- Preste atenção nos comentários das colunas para entender seu significado
- Use apenas as tabelas e colunas que existem no schema fornecido
- Se a pergunta envolver informações de múltiplas tabelas, use JOINs apropriados
- Para conectar clientes com contas a pagar, use: codigo_cliente_omie = codigo_cliente_fornecedor
- Sempre use o schema "visao360" antes do nome da tabela (ex: visao360.stg_omie_listarclientes)

Contexto do banco de dados:
{context}

Pergunta: {question}

SQL Query:"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    question = input("\n🤖 Faça sua pergunta (ou 'q' para sair): ")
    if question.lower() == 'q':
        break

    print("\n🔍 Buscando informações relevantes...")

    docs = smart_retrieval(question)

    business_context = [doc for doc in docs if doc.metadata.get("doc_type") == "business_context"]
    schema_context = [doc for doc in docs if doc.metadata.get("doc_type") == "schema"]
    join_context = [doc for doc in docs if doc.metadata.get("doc_type") == "join"]

    print(f"\n📊 Contexto de Negócio ({len(business_context)} docs):")
    for doc in business_context:
        print(f"  - {doc.metadata['table']}")

    print(f"\n🏗️  Schema Técnico ({len(schema_context)} docs):")
    for doc in schema_context:
        print(f"  - {doc.metadata['table']}")

    context_parts = []

    for doc in schema_context:
        context_parts.append(f"=== SCHEMA DA TABELA {doc.metadata['table'].upper()} ===")
        context_parts.append(doc.page_content)

    for doc in business_context:
        context_parts.append(f"=== CONTEXTO: {doc.metadata['table'].upper()} ===")
        context_parts.append(doc.page_content)

    for doc in join_context:
        context_parts.append(f"=== JOIN: {doc.metadata['table'].upper()} ===")
        context_parts.append(doc.page_content)

    context = "\n\n".join(context_parts)

    print("\n" + "=" * 50)
    print("CONTEXTO USADO:")
    print("=" * 50)
    print(context)
    print("=" * 50)

    # Gera SQL
    print("\n⚡ Gerando SQL...")
    result = chain.invoke({"context": context, "question": question})
    sql_result = extract_sql(result)

    print(f"\n✅ SQL Query:")
    print(f"```sql\n{sql_result}\n```\n")