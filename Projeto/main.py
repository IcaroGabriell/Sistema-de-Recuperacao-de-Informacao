import csv #permite criar a tabela tabela_documentos.csv
import os #usado para trabalhar com caminhos e diretórios

from parser import carregar_artigos
from indexador import carregar_stopwords, gerar_vocabulario


#Essas constantes centralizam os caminhos dos arquivos utilizados pelo programa,
#facilitando a manutenção e evitando repetir esses valores pelo código
CAMINHO_RESUMOS = "Titulos_autores_e_resumos.txt"
CAMINHO_STOPWORDS = "stopwords.txt"
PASTA_VOCABULARIOS = "vocabularios"
CAMINHO_TABELA_DOCUMENTOS = "tabela_documentos.csv"
CAMINHO_REGISTRO_CONTROLE = "registro_controle.txt"


# para cada artido é criado um arquivo como "doc1_vocabulario.txt"
def salvar_vocabulario(doc_id, vocabulario, pasta_destino):
    caminho = os.path.join(pasta_destino, "doc" + str(doc_id) + "_vocabulario.txt") #Construção do caminho
    #os.path.join monta o caminho do arquivo a partir da pasta de destino e do nome do documento

    termos_ordenados = sorted(vocabulario.items(), key=lambda item: (-item[1], item[0])) #ordenar pela frequência em ordem decrescente
                                                   #em caso de empate, ordenar o termo alfabeticamente

    # criação do arquivo
    #with faz com que o arquivo seja fechado sozinho depois que o bloco termina
    with open(caminho, "w", encoding="utf-8") as f:
        #Escrita do vocabulário
        for termo, freq in termos_ordenados:
            f.write("<" + termo + ", " + str(freq) + ">\n")
            #converte o número para texto porque o write() trabalha com strings

def main():
    os.makedirs(PASTA_VOCABULARIOS, exist_ok=True) #criação da pasta vocabularios
    #exist_ok=True permite executar novamente sem gerar erro caso a pasta já tenha sido criada
    
    #carregamento dos dados
    artigos = carregar_artigos(CAMINHO_RESUMOS) # parser.py lê o arquivo e extrai DocId; Título; Autor; Resumo
    stopwords = carregar_stopwords(CAMINHO_STOPWORDS)

    linhas_tabela = [] #guarda as informações que serão escritas depois no excel
    total_palavras_geral = 0
    ultimo_doc_id = 0 #maior identificador de documento encontrado

    #processa um documento por vez
    for artigo in artigos:
        doc_id = artigo["doc_id"]
        titulo = artigo["titulo"]
        autor = artigo["autor"]
        resumo = artigo["resumo"]
        #o dicionario de cada artigo possui essas informações

        #geração do vocabulario
        vocabulario = gerar_vocabulario(resumo, stopwords) #envia resumo para o indexador
        total_termos = sum(vocabulario.values()) #pega somente as frequencias dos termos e soma

        salvar_vocabulario(doc_id, vocabulario, PASTA_VOCABULARIOS)

        #construção da linha da tabela
        linha = {
            "DocId": doc_id,
            "Titulo": titulo,
            "Autor": autor,
            "TotalTermosSignificativos": total_termos,
        }
        linhas_tabela.append(linha) #add linha a lista

        #atualização da quantidade geral de termos de todos os documentos
        total_palavras_geral = total_palavras_geral + total_termos
        #verifica se o ID atual é maior que o maior ID já encontrado até agora
        if doc_id > ultimo_doc_id:
            ultimo_doc_id = doc_id

    #criação da tabela de documentos
    with open(CAMINHO_TABELA_DOCUMENTOS, "w", newline="", encoding="utf-8") as f: #abre/cria tabela_documentos.csv
        campos = ["DocId", "Titulo", "Autor", "TotalTermosSignificativos"] #define os nomes das colunas
        writer = csv.DictWriter(f, fieldnames=campos, delimiter=";") #permite escrever os dicionários da lista diretamente no CSV
        writer.writeheader() #cabeçalho
        writer.writerows(linhas_tabela) #escreve todas as linhas acumuladas

    #registro de controle "<20, 3500>"
    with open(CAMINHO_REGISTRO_CONTROLE, "w", encoding="utf-8") as f:
        f.write("<" + str(ultimo_doc_id) + ", " + str(total_palavras_geral) + ">\n")

    print("Processamento concluido")
    print("Total de artigos:", len(artigos))
    print("Registro de controle:", ultimo_doc_id, total_palavras_geral)


#chama a função main() e inicia o processamento
if __name__ == "__main__":
    main()
