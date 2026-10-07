import re #usado para trabalhar com expressões regulares
import unicodedata #usado para trabalhar com caracteres e acentos
from collections import Counter #conta quantas vezes cada termo aparece


#carrega as palavras que não devem participar da indexação
def carregar_stopwords(caminho_arquivo):
    try:
        #abre o arquivo de stopwords usando UTF-8
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()
    except UnicodeDecodeError:
        #caso o arquivo não esteja em UTF-8, tenta abrir usando latin-1
        with open(caminho_arquivo, "r", encoding="latin-1") as f:
            linhas = f.readlines()

    stopwords = set() #conjunto que vai armazenar as stopwords

    #percorre cada linha do arquivo
    for linha in linhas:
        palavra = linha.strip() #remove espaços e quebras de linha

        #verifica se a linha não está vazia
        if palavra:
            #normaliza a palavra antes de adicionar ao conjunto
            stopwords.add(normalizar_palavra(palavra))

    return stopwords


#normaliza uma palavra antes de ser utilizada
def normalizar_palavra(palavra):
    palavra = palavra.lower() #converte a palavra para letras minúsculas

    #separa os acentos das letras
    palavra = unicodedata.normalize("NFKD", palavra)

    #remove os caracteres que representam os acentos
    palavra = "".join(
        c for c in palavra
        if not unicodedata.combining(c)
    )

    return palavra


#separa o texto em palavras
def tokenizar(texto):
    texto = texto.lower() #converte todo o texto para minúsculas

    #encontra sequências de letras no texto
    tokens = re.findall(
        r"[a-zà-úçãõâêîôûäëïöü]+",
        texto
    )

    return tokens


#gera o vocabulário de um resumo
def gerar_vocabulario(resumo, stopwords):
    tokens = tokenizar(resumo) #separa o resumo em tokens
    termos = [] #lista que vai armazenar os termos válidos

    #percorre todos os tokens encontrados
    for token in tokens:
        token_normalizado = normalizar_palavra(token)

        #ignora o token se ele for uma stopword
        if token_normalizado in stopwords:
            continue

        #ignora palavras com apenas uma letra
        if len(token_normalizado) <= 1:
            continue

        #adiciona o termo à lista
        termos.append(token_normalizado)

    #Counter conta quantas vezes cada termo apareceu
    return Counter(termos)