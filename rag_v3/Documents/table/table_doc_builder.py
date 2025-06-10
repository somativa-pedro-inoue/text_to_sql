# Mapeamento de colunas importantes
KEY_COLUMNS_CONTEXT = {
    "stg_omie_listarclientes": {
        "razao_social": "Nome oficial/jurídico do cliente",
        "nome_fantasia": "Nome comercial usado pelo cliente",
        "cnpj_cpf": "Documento de identificação (CNPJ ou CPF)",
        "codigo_cliente_omie": "ID único do cliente no sistema (usado para JOINs com contas a pagar)",
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
        "codigo_cliente_fornecedor": "ID do cliente/fornecedor (conecta com codigo_cliente_omie da tabela de clientes)",
        "numero_documento": "Número da fatura ou nota fiscal"
    }
}

def build_table_doc(schema, table_name, columns, table_comment):

    # DOCUMENTO DE SCHEMA TÉCNICO
    col_descriptions = []
    key_columns = KEY_COLUMNS_CONTEXT.get(table_name, {})

    for col in columns:
        col_desc = f"{col['name']} ({col['type']})"

        if col.get('comment') and col['comment'].strip():
            col_desc += f" -- {col['comment']}"
        elif col['name'] in key_columns:
            col_desc += f" -- {key_columns[col['name']]}"

        col_descriptions.append(col_desc)

    table = f"""
SCHEMA: {schema}
TABLE: {table_name}
COMMENT: {table_comment}

COLUMNS:
{chr(10).join([f"- {desc}" for desc in col_descriptions])}
            """.strip()
