import re


def carregar_artigos(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    blocos = re.split(r"ARTIGO\s+(\d+)", conteudo)

    artigos = []
    for i in range(1, len(blocos), 2):
        doc_id = int(blocos[i])
        texto_bloco = blocos[i + 1]

        titulo = extrair_campo(texto_bloco, "Título", "Autor")
        autor = extrair_campo(texto_bloco, "Autor", "Resumo")
        resumo = extrair_campo(texto_bloco, "Resumo", None)

        artigo = {
            "doc_id": doc_id,
            "titulo": titulo,
            "autor": autor,
            "resumo": resumo,
        }
        artigos.append(artigo)

    return artigos


def extrair_campo(texto, campo_inicio, campo_fim):
    if campo_fim:
        padrao = campo_inicio + r":\s*(.*?)\s*" + campo_fim + ":"
    else:
        padrao = campo_inicio + r":\s*(.*)"

    resultado = re.search(padrao, texto, re.DOTALL)
    if not resultado:
        return ""

    valor = resultado.group(1)
    linhas = valor.splitlines()
    valor = " ".join(linha.strip() for linha in linhas)
    valor = re.sub(r"\s+", " ", valor).strip()
    return valor
