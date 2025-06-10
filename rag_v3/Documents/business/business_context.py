TABLE_BUSINESS_CONTEXT = {
    "stg_omie_listarclientes": {
        "purpose": "Cadastro completo de clientes da empresa",
        "business_use": "Usado para vendas, faturamento, cobrança e relacionamento comercial",
        "keywords": [
            "clientes", "customers", "cadastro de clientes", "dados do cliente",
            "contatos", "empresas", "pessoas", "razão social", "nome fantasia",
            "endereços", "telefones", "emails", "documentos", "cnpj", "cpf",
            "clientes com débitos", "clientes devedores", "histórico do cliente"
        ],
        "common_questions": [
            "dados do cliente", "contato do cliente", "endereço do cliente",
            "clientes ativos", "buscar cliente", "informações de cobrança",
            "clientes com contas em atraso", "clientes que mais devem"
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
            "contas em atraso", "valor a pagar", "status de pagamento",
            "clientes devedores", "débitos por cliente", "ranking de devedores"
        ],
        "common_questions": [
            "contas vencidas", "pagamentos pendentes", "total a pagar",
            "contas por fornecedor", "vencimentos do mês", "status das contas",
            "quais clientes devem", "total devido por cliente", "clientes em atraso"
        ]
    }
}

def get_business_context(table_name):
    if table_name in TABLE_BUSINESS_CONTEXT:
        context = TABLE_BUSINESS_CONTEXT[table_name]

    return context