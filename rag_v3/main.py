from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import vector_store, get_retriever  # importa funções do vector.py
from langchain_core.documents import Document


def extract_sql(text):
    start_index = text.upper().find('SELECT')
    end_index = text.find(';')
    if start_index != -1 and end_index != -1:
        return text[start_index:end_index + 1]
    return text


def smart_retrieval(question):
    """
    Busca inteligente em duas etapas:
    1. Primeiro identifica as tabelas relevantes pelo contexto de negócio
    2. Depois busca o schema técnico apenas das tabelas identificadas
    """

    # Etapa 1: Busca contexto de negócio para identificar tabelas
    business_retriever = get_retriever("business", k=2)
    business_docs = business_retriever.invoke(question)

    if business_docs:
        # Pega os nomes das tabelas identificadas
        relevant_tables = [doc.metadata["table"] for doc in business_docs]
        print(f"📋 Tabelas identificadas: {relevant_tables}")

        # Etapa 2: Busca schema apenas das tabelas relevantes
        # Chroma precisa de operadores AND explícitos
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

        # Combina contexto + schema
        return business_docs + schema_docs
    else:
        # Fallback: busca mista se não encontrou contexto
        mixed_retriever = get_retriever("mixed", k=4)
        return mixed_retriever.invoke(question)


# Modelo
model = OllamaLLM(model="codellama:7b")

# Prompt otimizado para incluir JOINs
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

INFORMAÇÕES DE JOIN:
- stg_omie_listarclientes.codigo_cliente_omie = stg_omie_listarcontaspagar.codigo_cliente_fornecedor
- Use esta ligação para relacionar dados de clientes com suas contas a pagar

Contexto do banco de dados:
{context}

Pergunta: {question}

SQL Query:"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Loop principal
while True:
    question = input("\n🤖 Faça sua pergunta (ou 'q' para sair): ")
    if question.lower() == 'q':
        break

    print("\n🔍 Buscando informações relevantes...")

    # Usa busca inteligente
    docs = smart_retrieval(question)

    # Separa contexto de negócio e schema para exibição
    business_context = [doc for doc in docs if doc.metadata.get("doc_type") == "business_context"]
    schema_context = [doc for doc in docs if doc.metadata.get("doc_type") == "schema"]

    print(f"\n📊 Contexto de Negócio ({len(business_context)} docs):")
    for doc in business_context:
        print(f"  - {doc.metadata['table']}")

    print(f"\n🏗️  Schema Técnico ({len(schema_context)} docs):")
    for doc in schema_context:
        print(f"  - {doc.metadata['table']}")

    # Monta contexto final priorizando schema (mais importante para SQL)
    context_parts = []

    # Primeiro o schema (mais importante para gerar SQL)
    for doc in schema_context:
        context_parts.append(f"=== SCHEMA DA TABELA {doc.metadata['table'].upper()} ===")
        context_parts.append(doc.page_content)

    # Depois contexto de negócio (para entendimento)
    for doc in business_context:
        context_parts.append(f"=== CONTEXTO: {doc.metadata['table'].upper()} ===")
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