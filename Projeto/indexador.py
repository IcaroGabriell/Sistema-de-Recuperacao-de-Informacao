import re
import unicodedata
from collections import Counter


def carregar_stopwords(caminho_arquivo):
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        with open(caminho_arquivo, "r", encoding="latin-1") as f:
            linhas = f.readlines()

    stopwords = set()
    for linha in linhas:
        palavra = linha.strip()
        if palavra:
            stopwords.add(normalizar_palavra(palavra))

    return stopwords


def normalizar_palavra(palavra):
    palavra = palavra.lower()
    palavra = unicodedata.normalize("NFKD", palavra)
    palavra = "".join(c for c in palavra if not unicodedata.combining(c))
    return palavra


def tokenizar(texto):
    texto = texto.lower()
    tokens = re.findall(r"[a-zà-úçãõâêîôûäëïöü]+", texto)
    return tokens


def gerar_vocabulario(resumo, stopwords):
    tokens = tokenizar(resumo)
    termos = []

    for token in tokens:
        token_normalizado = normalizar_palavra(token)
        if token_normalizado in stopwords:
            continue
        if len(token_normalizado) <= 1:
            continue
        termos.append(token_normalizado)

    return Counter(termos)
