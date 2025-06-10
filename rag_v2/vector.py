from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

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

# Contexto de negócio separado por tabela
TABLE_BUSINESS_CONTEXT = {
    "stg_omie_listarclientes": {
        "purpose": "Cadastro completo de clientes da empresa",
        "business_use": "Usado para vendas, faturamento, cobrança e relacionamento comercial",
        "keywords": [
            "clientes", "customers", "cadastro de clientes", "dados do cliente",
            "contatos", "empresas", "pessoas", "razão social", "nome fantasia",
            "endereços", "telefones", "emails", "documentos", "cnpj", "cpf"
        ],
        "common_questions": [
            "dados do cliente", "contato do cliente", "endereço do cliente",
            "clientes ativos", "buscar cliente", "informações de cobrança"
        ]
    },

    "stg_omie_listarprodutos": {
        "purpose": "Catálogo de produtos e controle de estoque",
        "business_use": "Gestão de vendas, precificação, controle de estoque e informações fiscais",
        "keywords": [
            "produtos", "items", "estoque", "inventory", "catálogo",
            "preços", "valores", "código do produto", "descrição do produto",
            "marca", "família de produtos", "unidades", "quantidade em estoque"
        ],
        "common_questions": [
            "produtos disponíveis", "preço do produto", "estoque do produto",
            "buscar produto", "produtos por marca", "produtos por categoria"
        ]
    },

    "stg_omie_listarcontaspagar": {
        "purpose": "Controle financeiro de pagamentos e compromissos",
        "business_use": "Gestão de fluxo de caixa, pagamentos a fornecedores e controle de vencimentos",
        "keywords": [
            "contas a pagar", "pagamentos", "fornecedores", "vencimentos",
            "títulos", "faturas", "boletos", "financeiro", "despesas",
            "contas em atraso", "valor a pagar", "status de pagamento"
        ],
        "common_questions": [
            "contas vencidas", "pagamentos pendentes", "total a pagar",
            "contas por fornecedor", "vencimentos do mês", "status das contas"
        ]
    }
}

# Mapeamento de colunas importantes
KEY_COLUMNS_CONTEXT = {
    "stg_omie_listarclientes": {
        "razao_social": "Nome oficial/jurídico do cliente",
        "nome_fantasia": "Nome comercial usado pelo cliente",
        "cnpj_cpf": "Documento de identificação (CNPJ ou CPF)",
        "codigo_cliente_omie": "ID único do cliente no sistema",
        "email": "Email principal para contato",
        "cidade": "Cidade onde o cliente está localizado",
        "estado": "Estado/UF do cliente"
    },

    "stg_omie_listarprodutos": {
        "codigo_produto": "Identificador único do produto",
        "descricao": "Nome/descrição completa do produto",
        "valor_unitario": "Preço de venda por unidade",
        "quantidade_estoque": "Quantidade disponível em estoque",
        "marca": "Marca/fabricante do produto",
        "unidade": "Unidade de medida (kg, un, cx, etc.)"
    },

    "stg_omie_listarcontaspagar": {
        "status_titulo": "Situação do pagamento (PAGO, A PAGAR, ATRASADO)",
        "valor_documento": "Valor total da conta",
        "data_vencimento": "Data limite para pagamento",
        "codigo_cliente_fornecedor": "ID do fornecedor/credor",
        "numero_documento": "Número da fatura ou nota fiscal"
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

        # 1. DOCUMENTO DE CONTEXTO DE NEGÓCIO (para entendimento semântico)
        if table_name in TABLE_BUSINESS_CONTEXT:
            context = TABLE_BUSINESS_CONTEXT[table_name]

            business_doc = f"""
{context['purpose']}

Finalidade: {context['business_use']}

Esta tabela é usada quando você precisa de informações sobre: {', '.join(context['keywords'][:8])}

Perguntas típicas que esta tabela responde:
{chr(10).join([f"- {q}" for q in context['common_questions']])}

Palavras-chave relacionadas: {', '.join(context['keywords'])}
            """.strip()

            documents.append(Document(
                page_content=business_doc,
                metadata={
                    "table": table_name,
                    "schema": schema,
                    "doc_type": "business_context",
                    "full_name": f"{schema}.{table_name}"
                }
            ))

        # 2. DOCUMENTO DE SCHEMA TÉCNICO (para SQL generation)
        col_descriptions = []
        key_columns = KEY_COLUMNS_CONTEXT.get(table_name, {})

        for col in columns:
            col_desc = f"{col['name']} ({col['type']})"

            # Prioriza comentários do banco, depois contexto customizado
            if col.get('comment') and col['comment'].strip():
                col_desc += f" -- {col['comment']}"
            elif col['name'] in key_columns:
                col_desc += f" -- {key_columns[col['name']]}"

            col_descriptions.append(col_desc)

        schema_doc = f"""
SCHEMA: {schema}
TABLE: {table_name}
COMMENT: {table_comment}

COLUMNS:
{chr(10).join([f"- {desc}" for desc in col_descriptions])}
        """.strip()

        documents.append(Document(
            page_content=schema_doc,
            metadata={
                "table": table_name,
                "schema": schema,
                "doc_type": "schema",
                "full_name": f"{schema}.{table_name}"
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


# Retriever customizado que pode buscar ambos os tipos
def get_retriever(search_type="mixed", k=4):
    """
    search_type:
    - 'business': apenas contexto de negócio
    - 'schema': apenas schema técnico
    - 'mixed': ambos (padrão)
    """

    if search_type == "business":
        # Filtro para apenas documentos de contexto
        return vector_store.as_retriever(
            search_kwargs={
                "k": k,
                "filter": {"doc_type": "business_context"}
            }
        )
    elif search_type == "schema":
        # Filtro para apenas schema
        return vector_store.as_retriever(
            search_kwargs={
                "k": k,
                "filter": {"doc_type": "schema"}
            }
        )
    else:
        return vector_store.as_retriever(search_kwargs={"k": k})


# Retriever padrão (busca ambos tipos)
retriever = get_retriever("mixed", k=4)