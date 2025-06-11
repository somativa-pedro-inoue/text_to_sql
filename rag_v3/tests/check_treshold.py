from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

db_location = "../chrome_langchain_db"
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

vector_store = Chroma(
    collection_name="database",
    persist_directory=db_location,
    embedding_function=embeddings,
)

question = "Liste os clientes"

print(f"=== ANALISANDO SCORES PARA: '{question}' ===\n")

# 1. Ver TODOS os documentos business_context com scores
print("1. TODOS os documentos business_context com scores:")
business_docs_with_scores = vector_store.similarity_search_with_score(
    question,
    k=10,
    filter={"doc_type": {"$eq": "business_context"}}
)

for i, (doc, score) in enumerate(business_docs_with_scores):
    print(f"Doc {i+1}:")
    print(f"  Score: {score:.4f}")
    print(f"  Tabela: {doc.metadata.get('table', 'N/A')}")
    print(f"  Conteúdo (primeiras 100 chars): {doc.page_content[:100]}...")
    print("-" * 50)

print("\n2. TODOS os documentos (qualquer tipo) com scores:")
all_docs_with_scores = vector_store.similarity_search_with_score(question, k=10)

for i, (doc, score) in enumerate(all_docs_with_scores):
    print(f"Doc {i+1}:")
    print(f"  Score: {score:.4f}")
    print(f"  Tipo: {doc.metadata.get('doc_type', 'N/A')}")
    print(f"  Tabela: {doc.metadata.get('table', 'N/A')}")
    print(f"  Conteúdo: {doc.page_content[:80]}...")
    print("-" * 30)

# 3. Testar diferentes queries relacionadas
print("\n3. TESTANDO DIFERENTES QUERIES:")
test_queries = [
    "clientes",
    "customer",
    "cadastro de clientes",
    "listar clientes",
    "dados do cliente"
]

for test_q in test_queries:
    docs_test = vector_store.similarity_search_with_score(
        test_q,
        k=3,
        filter={"doc_type": {"$eq": "business_context"}}
    )
    print(f"\nQuery: '{test_q}'")
    if docs_test:
        best_score = docs_test[0][1]
        print(f"  Melhor score: {best_score:.4f}")
        print(f"  Tabela: {docs_test[0][0].metadata.get('table')}")
    else:
        print("  Nenhum resultado")

# 4. Ver o conteúdo completo dos documentos business_context
print("\n4. CONTEÚDO COMPLETO DOS DOCUMENTOS BUSINESS_CONTEXT:")
business_only = vector_store.similarity_search(
    "",
    k=10,
    filter={"doc_type": {"$eq": "business_context"}}
)

for i, doc in enumerate(business_only):
    print(f"\n=== DOCUMENTO {i+1}: {doc.metadata.get('table')} ===")
    print(doc.page_content)
    print("=" * 60)

# 5. Teste sem filtro para ver se o problema é o filtro
print("\n5. TESTE SEM FILTRO (todos os tipos de documento):")
no_filter_docs = vector_store.similarity_search_with_score(question, k=5)
for doc, score in no_filter_docs:
    if score <= 0.5:  # Só mostra os que passariam no threshold
        print(f"Score: {score:.4f} | Tipo: {doc.metadata.get('doc_type')} | Tabela: {doc.metadata.get('table')}")