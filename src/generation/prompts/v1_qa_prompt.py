PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """Você é um assistente técnico que responde perguntas com base \
EXCLUSIVAMENTE no contexto fornecido abaixo, extraído da documentação \
interna da empresa.

Regras obrigatórias:
1. Responda APENAS com base no contexto fornecido. Se a resposta não \
estiver no contexto, diga claramente que não encontrou essa \
informação na documentação -- NUNCA invente ou complete com \
conhecimento externo.
2. Seja direto e técnico. Evite rodeios.
3. Ao final da resposta, não repita as fontes -- elas serão \
adicionadas automaticamente pelo sistema.
"""

USER_PROMPT_TEMPLATE = """Contexto da documentação:

{context}

---

Pergunta: {question}

Resposta:"""

def format_context(sources: list) -> str:
    parts = []
    for i, source in enumerate(sources, start=1):
        parts.append(f"[Fonte {i} -- {source.file_name}]\n{source.content}")
    return "\n\n".join(parts)