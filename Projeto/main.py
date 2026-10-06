import csv
import os

from parser import carregar_artigos
from indexador import carregar_stopwords, gerar_vocabulario

CAMINHO_RESUMOS = "Titulos__autores_e_resumos.txt"
CAMINHO_STOPWORDS = "stopwords.txt"
PASTA_VOCABULARIOS = "vocabularios"
CAMINHO_TABELA_DOCUMENTOS = "tabela_documentos.csv"
CAMINHO_REGISTRO_CONTROLE = "registro_controle.txt"


def salvar_vocabulario(doc_id, vocabulario, pasta_destino):
    caminho = os.path.join(pasta_destino, "doc" + str(doc_id) + "_vocabulario.txt")

    termos_ordenados = sorted(vocabulario.items(), key=lambda item: (-item[1], item[0]))

    with open(caminho, "w", encoding="utf-8") as f:
        for termo, freq in termos_ordenados:
            f.write("<" + termo + ", " + str(freq) + ">\n")


def main():
    os.makedirs(PASTA_VOCABULARIOS, exist_ok=True)

    artigos = carregar_artigos(CAMINHO_RESUMOS)
    stopwords = carregar_stopwords(CAMINHO_STOPWORDS)

    linhas_tabela = []
    total_palavras_geral = 0
    ultimo_doc_id = 0

    for artigo in artigos:
        doc_id = artigo["doc_id"]
        titulo = artigo["titulo"]
        autor = artigo["autor"]
        resumo = artigo["resumo"]

        vocabulario = gerar_vocabulario(resumo, stopwords)
        total_termos = sum(vocabulario.values())

        salvar_vocabulario(doc_id, vocabulario, PASTA_VOCABULARIOS)

        linha = {
            "DocId": doc_id,
            "Titulo": titulo,
            "Autor": autor,
            "TotalTermosSignificativos": total_termos,
        }
        linhas_tabela.append(linha)

        total_palavras_geral = total_palavras_geral + total_termos
        if doc_id > ultimo_doc_id:
            ultimo_doc_id = doc_id

    with open(CAMINHO_TABELA_DOCUMENTOS, "w", newline="", encoding="utf-8") as f:
        campos = ["DocId", "Titulo", "Autor", "TotalTermosSignificativos"]
        writer = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        writer.writeheader()
        writer.writerows(linhas_tabela)

    with open(CAMINHO_REGISTRO_CONTROLE, "w", encoding="utf-8") as f:
        f.write("<" + str(ultimo_doc_id) + ", " + str(total_palavras_geral) + ">\n")

    print("Processamento concluido")
    print("Total de artigos:", len(artigos))
    print("Registro de controle:", ultimo_doc_id, total_palavras_geral)


if __name__ == "__main__":
    main()
