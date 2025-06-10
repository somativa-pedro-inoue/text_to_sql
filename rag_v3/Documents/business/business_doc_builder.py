from rag_v3.Documents.business.business_context import get_business_context

def build_business_doc(table_name):

    context = get_business_context(table_name)

    document = f"""
    {context['purpose']}
    
    Finalidade: {context['business_use']}
    
    Esta tabela é usada quando você precisa de informações sobre: {', '.join(context['keywords'][:8])}
    
    Perguntas típicas que esta tabela responde:
    {chr(10).join([f"- {q}" for q in context['common_questions']])}
    
    Palavras-chave relacionadas: {', '.join(context['keywords'])}
    
                """.strip()

    return document