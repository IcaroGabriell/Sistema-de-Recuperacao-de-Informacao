import csv
import math
import os
import re

from indexador import carregar_stopwords, normalizar_palavra, tokenizar


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASTA_VOCABULARIOS = os.path.join(BASE_DIR, "vocabularios")
CAMINHO_TABELA_DOCUMENTOS = os.path.join(
    BASE_DIR, "tabela_documentos.csv"
)
CAMINHO_STOPWORDS = os.path.join(
    BASE_DIR, "stopwords.txt"
)


def carregar_documentos(caminho_tabela=CAMINHO_TABELA_DOCUMENTOS):
    documentos = {}

    with open(caminho_tabela, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for linha in reader:
            doc_id = int(linha["DocId"])

            documentos[doc_id] = {
                "doc_id": doc_id,
                "titulo": linha["Titulo"],
                "autor": linha["Autor"],
                "total_termos": int(linha["TotalTermosSignificativos"]),
            }

    return documentos


def carregar_vocabulario(doc_id, pasta=PASTA_VOCABULARIOS):
    caminho = os.path.join(pasta, f"doc{doc_id}_vocabulario.txt")
    vocabulario = {}

    if not os.path.exists(caminho):
        return vocabulario

    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            match = re.match(r"<(.*?),\s*(\d+)>", linha.strip())

            if match:
                termo = match.group(1)
                frequencia = int(match.group(2))
                vocabulario[termo] = frequencia

    return vocabulario


def carregar_indice(pasta=PASTA_VOCABULARIOS):
    indice = {}

    arquivos = [
        nome for nome in os.listdir(pasta)
        if re.fullmatch(r"doc\d+_vocabulario\.txt", nome)
    ]

    for nome in arquivos:
        doc_id = int(re.search(r"\d+", nome).group())
        vocabulario = carregar_vocabulario(doc_id, pasta)

        for termo in vocabulario:
            indice.setdefault(termo, set()).add(doc_id)

    return indice


def preparar_consulta(consulta, stopwords):
    """
    Aplica à consulta a mesma lógica usada na indexação:
    tokenização, normalização e remoção de stopwords.

    Os operadores booleanos são preservados.
    """
    tokens = re.findall(
        r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|[a-zà-úçãõâêîôûäëïöü]+",
        consulta,
        flags=re.IGNORECASE
    )

    resultado = []

    for token in tokens:
        operador = token.upper()

        if operador in {"AND", "OR", "NOT"}:
            resultado.append(operador)

        elif token in {"(", ")"}:
            resultado.append(token)

        else:
            termo = normalizar_palavra(token)

            if termo not in stopwords and len(termo) > 1:
                resultado.append(termo)

    return resultado


# -------------------------
# MODELO BOOLEANO
# -------------------------

class ParserBooleano:
    """
    Gramática utilizada:

        expressao := termo
                   | NOT expressao
                   | ( expressao )
                   | expressao AND expressao
                   | expressao OR expressao

    Precedência:
        NOT > AND > OR
    """

    def __init__(self, tokens, conjuntos_documentos):
        self.tokens = tokens
        self.posicao = 0
        self.conjuntos = conjuntos_documentos
        self.universo = set(conjuntos_documentos["__UNIVERSO__"])

    def atual(self):
        if self.posicao >= len(self.tokens):
            return None
        return self.tokens[self.posicao]

    def consumir(self, esperado=None):
        token = self.atual()

        if token is None:
            raise ValueError("Fim inesperado da consulta.")

        if esperado and token != esperado:
            raise ValueError(
                f"Esperado '{esperado}', encontrado '{token}'."
            )

        self.posicao += 1
        return token

    def analisar(self):
        if not self.tokens:
            raise ValueError("Consulta vazia.")

        resultado = self.parse_or()

        if self.atual() is not None:
            raise ValueError(
                f"Token inesperado na posição {self.posicao}: "
                f"{self.atual()}"
            )

        return resultado

    def parse_or(self):
        resultado = self.parse_and()

        while self.atual() == "OR":
            self.consumir("OR")
            direita = self.parse_and()
            resultado = resultado | direita

        return resultado

    def parse_and(self):
        resultado = self.parse_not()

        while self.atual() == "AND":
            self.consumir("AND")
            direita = self.parse_not()
            resultado = resultado & direita

        return resultado

    def parse_not(self):
        if self.atual() == "NOT":
            self.consumir("NOT")
            return self.universo - self.parse_not()

        return self.parse_primario()

    def parse_primario(self):
        token = self.atual()

        if token == "(":
            self.consumir("(")
            resultado = self.parse_or()
            self.consumir(")")
            return resultado

        if token in {"AND", "OR", "NOT", ")", None}:
            raise ValueError(
                f"Termo esperado, encontrado '{token}'."
            )

        self.consumir()
        return self.conjuntos.get(token, set())


def buscar_booleano(consulta, documentos, indice, stopwords):
    tokens = preparar_consulta(consulta, stopwords)

    conjuntos = {
        termo: set(docs)
        for termo, docs in indice.items()
    }
    conjuntos["__UNIVERSO__"] = set(documentos.keys())

    parser = ParserBooleano(tokens, conjuntos)
    ids = parser.analisar()

    # O modelo booleano não produz ranking de relevância.
    return sorted(ids)


# -------------------------
# MODELO ESPAÇO VETORIAL
# -------------------------

def calcular_idf(indice, total_documentos):
    """
    IDF usado no TF-IDF:
        IDF(t) = log(N / df(t))

    N = número total de documentos
    df(t) = quantidade de documentos que contêm t
    """
    idf = {}

    for termo, documentos in indice.items():
        df = len(documentos)

        if df > 0:
            idf[termo] = math.log(total_documentos / df)

    return idf


def peso_tfidf(tf, idf):
    return tf * idf


def similaridade_cosseno(vetor_documento, vetor_consulta):
    termos = set(vetor_documento) | set(vetor_consulta)

    produto = 0.0
    norma_documento = 0.0
    norma_consulta = 0.0

    for termo in termos:
        peso_documento = vetor_documento.get(termo, 0.0)
        peso_consulta = vetor_consulta.get(termo, 0.0)

        produto += peso_documento * peso_consulta
        norma_documento += peso_documento ** 2
        norma_consulta += peso_consulta ** 2

    if norma_documento == 0 or norma_consulta == 0:
        return 0.0

    return produto / (
        math.sqrt(norma_documento) *
        math.sqrt(norma_consulta)
    )


def buscar_vetorial(
    consulta,
    documentos,
    indice,
    stopwords,
    pasta=PASTA_VOCABULARIOS
):
    tokens = preparar_consulta(consulta, stopwords)

    # Apenas termos que aparecem na consulta e na coleção.
    frequencia_consulta = {}

    for token in tokens:
        if token in {"AND", "OR", "NOT", "(", ")"}:
            continue

        frequencia_consulta[token] = (
            frequencia_consulta.get(token, 0) + 1
        )

    if not frequencia_consulta:
        return []

    idf = calcular_idf(indice, len(documentos))

    vetor_consulta = {}

    for termo, tf in frequencia_consulta.items():
        if termo in idf:
            vetor_consulta[termo] = peso_tfidf(tf, idf[termo])

    resultados = []

    for doc_id in documentos:
        vocabulario = carregar_vocabulario(doc_id, pasta)

        vetor_documento = {}

        for termo, tf in vocabulario.items():
            if termo in idf:
                vetor_documento[termo] = peso_tfidf(tf, idf[termo])

        score = similaridade_cosseno(
            vetor_documento,
            vetor_consulta
        )

        # Documentos com score 0 não são relevantes para a consulta
        # no modelo vetorial implementado aqui.
        if score > 0:
            resultados.append((doc_id, score))

    resultados.sort(key=lambda item: (-item[1], item[0]))

    return resultados


def calcular_precisao_revocacao(relevantes_julgados, recuperados):
    relevantes_julgados = set(relevantes_julgados)
    recuperados = set(recuperados)

    relevantes_recuperados = relevantes_julgados & recuperados

    if len(recuperados) == 0:
        precisao = 0.0
    else:
        precisao = len(relevantes_recuperados) / len(recuperados)

    if len(relevantes_julgados) == 0:
        revocacao = 0.0
    else:
        revocacao = (
            len(relevantes_recuperados) /
            len(relevantes_julgados)
        )

    return precisao, revocacao
