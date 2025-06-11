# RELACIONAMENTOS ENTRE TABELAS
TABLE_RELATIONSHIPS = {
    "stg_omie_listarclientes":"""
        CLIENTES ↔ CONTAS A PAGAR:
        - Join entre as tabelas stg_omie_listarclientes com stg_omie_listarcontaspagar
        - Como conectar: stg_omie_listarclientes.codigo_cliente_omie = stg_omie_listarcontaspagar.codigo_cliente_fornecedor and stg_omie_listarclientes.org_id = stg_omie_listarcontaspagar.org_id
        - Relacionamento: 1 cliente pode ter N contas a pagar
        - Usado para: Ver débitos, contas pendentes, histórico financeiro por cliente
        """
    ,
}


def build_relations_doc(table_name):

    relation = TABLE_RELATIONSHIPS.get(table_name, "")
    return relation
