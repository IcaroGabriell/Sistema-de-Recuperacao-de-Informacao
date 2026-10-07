import re #usado para procurar e separar as informações dos artigos


#carrega os artigos do arquivo de entrada
def carregar_artigos(caminho_arquivo):

    #abre o arquivo que contém os artigos
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        conteudo = f.read()

    #separa o conteúdo sempre que encontra "ARTIGO" seguido do número
    blocos = re.split(r"ARTIGO\s+(\d+)", conteudo)

    artigos = [] #lista que vai armazenar os artigos encontrados

    #percorre os blocos de dois em dois
    #um contém o número e o próximo contém os dados do artigo
    for i in range(1, len(blocos), 2):
        doc_id = int(blocos[i]) #converte o número do artigo para inteiro
        texto_bloco = blocos[i + 1] #pega o conteúdo do artigo

        #extrai cada informação do artigo
        titulo = extrair_campo(
            texto_bloco,
            "Título",
            "Autor"
        )

        autor = extrair_campo(
            texto_bloco,
            "Autor",
            "Resumo"
        )

        resumo = extrair_campo(
            texto_bloco,
            "Resumo",
            None
        )

        #cria um dicionário com os dados do artigo
        artigo = {
            "doc_id": doc_id,
            "titulo": titulo,
            "autor": autor,
            "resumo": resumo,
        }

        artigos.append(artigo) #adiciona o artigo à lista

    return artigos


#extrai um campo específico do texto
def extrair_campo(texto, campo_inicio, campo_fim):

    #quando existe um próximo campo, procura o conteúdo entre os dois
    if campo_fim:
        padrao = (
            campo_inicio
            + r":\s*(.*?)\s*"
            + campo_fim
            + ":"
        )

    #quando não existe próximo campo, pega tudo que vem depois
    else:
        padrao = campo_inicio + r":\s*(.*)"

    #procura o padrão dentro do texto
    #DOTALL permite que o . também considere quebras de linha
    resultado = re.search(
        padrao,
        texto,
        re.DOTALL
    )

    #caso o campo não seja encontrado, retorna vazio
    if not resultado:
        return ""

    valor = resultado.group(1)

    #separa o conteúdo por linhas
    linhas = valor.splitlines()

    #junta as linhas novamente, retirando espaços desnecessários
    valor = " ".join(
        linha.strip()
        for linha in linhas
    )

    #remove espaços repetidos
    valor = re.sub(
        r"\s+",
        " ",
        valor
    ).strip()

    return valor