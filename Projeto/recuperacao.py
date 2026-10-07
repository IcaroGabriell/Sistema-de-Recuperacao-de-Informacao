import csv #usado para ler a tabela de documentos
import math #usado nos cálculos de IDF e similaridade
import os #usado para trabalhar com caminhos e arquivos
import re #usado para expressões regulares

from indexador import (
    carregar_stopwords,
    normalizar_palavra,
    tokenizar,
)


#pega o diretório onde o programa está sendo executado
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

#caminho da pasta que contém os vocabulários
PASTA_VOCABULARIOS = os.path.join(
    BASE_DIR,
    "vocabularios"
)

#caminho da tabela com os dados dos documentos
CAMINHO_TABELA_DOCUMENTOS = os.path.join(
    BASE_DIR,
    "tabela_documentos.csv"
)

#caminho do arquivo de stopwords
CAMINHO_STOPWORDS = os.path.join(
    BASE_DIR,
    "stopwords.txt"
)


#carrega as informações dos documentos
def carregar_documentos(
    caminho_tabela=CAMINHO_TABELA_DOCUMENTOS
):
    documentos = {} #dicionário que vai armazenar os documentos

    #abre a tabela de documentos
    with open(
        caminho_tabela,
        "r",
        encoding="utf-8"
    ) as f:

        #lê o CSV usando ; como separador
        reader = csv.DictReader(
            f,
            delimiter=";"
        )

        #percorre cada linha da tabela
        for linha in reader:
            doc_id = int(linha["DocId"])

            #cria os dados do documento
            documentos[doc_id] = {
                "doc_id": doc_id,
                "titulo": linha["Titulo"],
                "autor": linha["Autor"],
                "total_termos": int(
                    linha["TotalTermosSignificativos"]
                ),
            }

    return documentos


#carrega o vocabulário de um documento
def carregar_vocabulario(
    doc_id,
    pasta=PASTA_VOCABULARIOS
):
    #monta o nome do arquivo do vocabulário
    caminho = os.path.join(
        pasta,
        f"doc{doc_id}_vocabulario.txt"
    )

    vocabulario = {} #dicionário que guarda termo e frequência

    #se o arquivo não existir, retorna um vocabulário vazio
    if not os.path.exists(caminho):
        return vocabulario

    #abre o arquivo do vocabulário
    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        #percorre cada linha do arquivo
        for linha in f:

            #procura o formato <termo, frequência>
            match = re.match(
                r"<(.*?),\s*(\d+)>",
                linha.strip()
            )

            #se encontrou o formato esperado
            if match:
                termo = match.group(1)
                frequencia = int(match.group(2))

                #guarda o termo e sua frequência
                vocabulario[termo] = frequencia

    return vocabulario


#cria o índice invertido
def carregar_indice(
    pasta=PASTA_VOCABULARIOS
):
    indice = {} #termo -> conjunto de documentos

    #pega somente os arquivos de vocabulário
    arquivos = [
        nome
        for nome in os.listdir(pasta)
        if re.fullmatch(
            r"doc\d+_vocabulario\.txt",
            nome
        )
    ]

    #percorre todos os arquivos encontrados
    for nome in arquivos:

        #extrai o número do documento pelo nome do arquivo
        doc_id = int(
            re.search(
                r"\d+",
                nome
            ).group()
        )

        #carrega o vocabulário daquele documento
        vocabulario = carregar_vocabulario(
            doc_id,
            pasta
        )

        #percorre os termos do documento
        for termo in vocabulario:

            #cria o conjunto caso o termo ainda não exista
            indice.setdefault(
                termo,
                set()
            ).add(doc_id)

    return indice


#prepara a consulta antes de realizar a busca
def preparar_consulta(
    consulta,
    stopwords
):
    #separa operadores, parênteses e palavras
    tokens = re.findall(
        r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|[a-zà-úçãõâêîôûäëïöü]+",
        consulta,
        flags=re.IGNORECASE
    )

    resultado = [] #guarda os tokens já preparados

    #percorre os tokens encontrados
    for token in tokens:
        operador = token.upper()

        #mantém os operadores booleanos
        if operador in {"AND", "OR", "NOT"}:
            resultado.append(operador)

        #mantém os parênteses
        elif token in {"(", ")"}:
            resultado.append(token)

        else:
            #normaliza o termo
            termo = normalizar_palavra(token)

            #ignora stopwords e palavras com apenas uma letra
            if termo not in stopwords and len(termo) > 1:
                resultado.append(termo)

    return resultado



# MODELO BOOLEANO

#faz o processamento das consultas booleanas
class ParserBooleano:

    #define a estrutura da consulta:
    #NOT possui maior prioridade que AND
    #AND possui maior prioridade que OR

    def __init__(
        self,
        tokens,
        conjuntos_documentos
    ):
        self.tokens = tokens #tokens da consulta
        self.posicao = 0 #posição atual na consulta
        self.conjuntos = conjuntos_documentos

        #conjunto com todos os documentos da coleção
        self.universo = set(
            conjuntos_documentos["__UNIVERSO__"]
        )

    #retorna o token atual
    def atual(self):
        if self.posicao >= len(self.tokens):
            return None

        return self.tokens[self.posicao]

    #consome o token atual e avança para o próximo
    def consumir(self, esperado=None):
        token = self.atual()

        #verifica se a consulta terminou antes do esperado
        if token is None:
            raise ValueError(
                "Fim inesperado da consulta."
            )

        #verifica se o token encontrado é o esperado
        if esperado and token != esperado:
            raise ValueError(
                f"Esperado '{esperado}', encontrado '{token}'."
            )

        self.posicao += 1

        return token

    #inicia a análise da consulta
    def analisar(self):

        #não permite uma consulta vazia
        if not self.tokens:
            raise ValueError(
                "Consulta vazia."
            )

        #começa pelo operador OR, que possui menor prioridade
        resultado = self.parse_or()

        #verifica se sobrou algum token sem ser processado
        if self.atual() is not None:
            raise ValueError(
                f"Token inesperado na posição {self.posicao}: "
                f"{self.atual()}"
            )

        return resultado

    #processa operações OR
    def parse_or(self):

        #primeiro processa operações AND
        resultado = self.parse_and()

        #continua enquanto encontrar OR
        while self.atual() == "OR":
            self.consumir("OR")

            direita = self.parse_and()

            #união dos conjuntos = OR
            resultado = resultado | direita

        return resultado

    #processa operações AND
    def parse_and(self):

        #primeiro processa NOT
        resultado = self.parse_not()

        #continua enquanto encontrar AND
        while self.atual() == "AND":
            self.consumir("AND")

            direita = self.parse_not()

            #interseção dos conjuntos = AND
            resultado = resultado & direita

        return resultado

    #processa o operador NOT
    def parse_not(self):

        if self.atual() == "NOT":
            self.consumir("NOT")

            #retorna os documentos que não possuem o termo
            return self.universo - self.parse_not()

        return self.parse_primario()

    #processa termos e expressões entre parênteses
    def parse_primario(self):

        token = self.atual()

        #quando encontra (, processa a expressão dentro dele
        if token == "(":
            self.consumir("(")

            resultado = self.parse_or()

            self.consumir(")")

            return resultado

        #esses tokens não podem aparecer onde deveria existir um termo
        if token in {
            "AND",
            "OR",
            "NOT",
            ")",
            None
        }:
            raise ValueError(
                f"Termo esperado, encontrado '{token}'."
            )

        self.consumir()

        #retorna os documentos que possuem o termo
        #se não existir, retorna conjunto vazio
        return self.conjuntos.get(
            token,
            set()
        )


#realiza uma busca usando o modelo booleano
def buscar_booleano(
    consulta,
    documentos,
    indice,
    stopwords
):
    #prepara a consulta
    tokens = preparar_consulta(
        consulta,
        stopwords
    )

    #transforma o índice em conjuntos de documentos
    conjuntos = {
        termo: set(docs)
        for termo, docs in indice.items()
    }

    #cria o conjunto de todos os documentos
    #usado principalmente pelo operador NOT
    conjuntos["__UNIVERSO__"] = set(
        documentos.keys()
    )

    #cria o analisador da consulta
    parser = ParserBooleano(
        tokens,
        conjuntos
    )

    #processa a consulta
    ids = parser.analisar()

    #o modelo booleano não possui ranking
    return sorted(ids)



# MODELO ESPAÇO VETORIAL

#calcula o IDF de cada termo
def calcular_idf(
    indice,
    total_documentos
):
    """
    IDF usado no TF-IDF:
        IDF(t) = log(N / df(t))

    N = número total de documentos
    df(t) = quantidade de documentos que possuem o termo
    """

    idf = {} #guarda o IDF de cada termo

    #percorre todos os termos do índice
    for termo, documentos in indice.items():

        #quantidade de documentos que possuem o termo
        df = len(documentos)

        if df > 0:
            #calcula o IDF usando log(N / df)
            idf[termo] = math.log(
                total_documentos / df
            )

    return idf


#calcula o peso TF-IDF
def peso_tfidf(tf, idf):
    #multiplica a frequência do termo pelo seu IDF
    return tf * idf


#calcula a similaridade entre dois vetores
def similaridade_cosseno(
    vetor_documento,
    vetor_consulta
):
    #pega todos os termos presentes nos dois vetores
    termos = (
        set(vetor_documento)
        | set(vetor_consulta)
    )

    produto = 0.0 #produto escalar
    norma_documento = 0.0 #tamanho do vetor do documento
    norma_consulta = 0.0 #tamanho do vetor da consulta

    #percorre todos os termos
    for termo in termos:

        #pega o peso do termo no documento
        peso_documento = vetor_documento.get(
            termo,
            0.0
        )

        #pega o peso do termo na consulta
        peso_consulta = vetor_consulta.get(
            termo,
            0.0
        )

        #calcula o produto escalar
        produto += (
            peso_documento
            * peso_consulta
        )

        #soma o quadrado dos pesos do documento
        norma_documento += (
            peso_documento ** 2
        )

        #soma o quadrado dos pesos da consulta
        norma_consulta += (
            peso_consulta ** 2
        )

    #evita divisão por zero
    if (
        norma_documento == 0
        or norma_consulta == 0
    ):
        return 0.0

    #fórmula da similaridade do cosseno
    return produto / (
        math.sqrt(norma_documento)
        * math.sqrt(norma_consulta)
    )


#realiza a busca usando o modelo espaço vetorial
def buscar_vetorial(
    consulta,
    documentos,
    indice,
    stopwords,
    pasta=PASTA_VOCABULARIOS
):
    #prepara a consulta
    tokens = preparar_consulta(
        consulta,
        stopwords
    )

    #guarda a frequência dos termos da consulta
    frequencia_consulta = {}

    #percorre os tokens da consulta
    for token in tokens:

        #ignora operadores e parênteses
        if token in {
            "AND",
            "OR",
            "NOT",
            "(",
            ")"
        }:
            continue

        #conta quantas vezes o termo aparece
        frequencia_consulta[token] = (
            frequencia_consulta.get(token, 0)
            + 1
        )

    #se não houver nenhum termo válido, não há resultado
    if not frequencia_consulta:
        return []

    #calcula o IDF dos termos
    idf = calcular_idf(
        indice,
        len(documentos)
    )

    vetor_consulta = {} #vetor TF-IDF da consulta

    #monta o vetor da consulta
    for termo, tf in frequencia_consulta.items():

        #só considera termos que existem no índice
        if termo in idf:
            vetor_consulta[termo] = peso_tfidf(
                tf,
                idf[termo]
            )

    resultados = [] #lista com documento e sua similaridade

    #percorre todos os documentos
    for doc_id in documentos:

        #carrega o vocabulário do documento
        vocabulario = carregar_vocabulario(
            doc_id,
            pasta
        )

        vetor_documento = {} #vetor TF-IDF do documento

        #monta o vetor do documento
        for termo, tf in vocabulario.items():

            if termo in idf:
                vetor_documento[termo] = peso_tfidf(
                    tf,
                    idf[termo]
                )

        #calcula a similaridade entre documento e consulta
        score = similaridade_cosseno(
            vetor_documento,
            vetor_consulta
        )

        #só guarda documentos que possuem alguma similaridade
        if score > 0:
            resultados.append(
                (doc_id, score)
            )

    #ordena primeiro pela relevância
    #em caso de empate, usa o ID do documento
    resultados.sort(
        key=lambda item: (
            -item[1],
            item[0]
        )
    )

    return resultados


#calcula precisão e revocação dos resultados
def calcular_precisao_revocacao(
    relevantes_julgados,
    recuperados
):
    #transforma as listas em conjuntos
    relevantes_julgados = set(
        relevantes_julgados
    )

    recuperados = set(
        recuperados
    )

    #documentos que são relevantes e foram recuperados
    relevantes_recuperados = (
        relevantes_julgados
        & recuperados
    )

    #calcula a precisão
    if len(recuperados) == 0:
        precisao = 0.0
    else:
        precisao = (
            len(relevantes_recuperados)
            / len(recuperados)
        )

    #calcula a revocação
    if len(relevantes_julgados) == 0:
        revocacao = 0.0
    else:
        revocacao = (
            len(relevantes_recuperados)
            / len(relevantes_julgados)
        )

    return precisao, revocacao