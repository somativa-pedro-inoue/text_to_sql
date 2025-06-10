# RELACIONAMENTOS ENTRE TABELAS
TABLE_RELATIONSHIPS = {
    "stg_omie_listarclientes": {
        "joins_with": {
            "stg_omie_listarcontaspagar": {
                "condition": "stg_omie_listarclientes.codigo_cliente_omie = stg_omie_listarcontaspagar.codigo_cliente_fornecedor AND stg_omie_listarclientes.org_id = stg_omie_listarcontaspagar.org_id",
                "type": "1:N",
                "description": "Um cliente pode ter múltiplas contas a pagar",
                "use_case": "Ver débitos, contas pendentes ou histórico financeiro do cliente"
            }
        }
    },

    "stg_omie_listarcontaspagar": {
        "joins_with": {
            "stg_omie_listarclientes": {
                "condition": "stg_omie_listarcontaspagar.codigo_cliente_fornecedor = stg_omie_listarclientes.codigo_cliente_omie AND stg_omie_listarcontaspagar.org_id = stg_omie_listarclientes.org_id",
                "type": "N:1",
                "description": "Cada conta pertence a um cliente específico",
                "use_case": "Identificar qual cliente deve cada conta ou obter dados do cliente"
            }
        }
    }
}

def build_relations_doc(table_name):

    relation = TABLE_RELATIONSHIPS.get(table_name, {})
    print(relation)

build_relations_doc("stg_omie_listarclientes")