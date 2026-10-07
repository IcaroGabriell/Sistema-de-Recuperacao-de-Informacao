import os #usado para trabalhar com caminhos e arquivos
import subprocess #usado para abrir os PDFs em alguns sistemas
import sys #usado para identificar o sistema operacional
import tkinter as tk #biblioteca usada para criar a interface
from tkinter import messagebox, ttk #componentes da interface

from indexador import carregar_stopwords
from recuperacao import (
    carregar_documentos,
    carregar_indice,
    buscar_booleano,
    buscar_vetorial,
)


#pega o diretório onde o programa está sendo executado
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

#caminho do arquivo de stopwords
CAMINHO_STOPWORDS = os.path.join(
    BASE_DIR,
    "stopwords.txt"
)

#pasta onde estão os artigos originais
PASTA_ARTIGOS = os.path.join(
    BASE_DIR,
    "artigos"
)


#classe responsável pela interface gráfica
class InterfaceSRI:

    #configura a janela e carrega os dados necessários
    def __init__(self, root):
        self.root = root

        #define o título da janela
        self.root.title(
            "Sistema de Recuperação de Informação"
        )

        #define o tamanho da janela
        self.root.geometry(
            "1000x650"
        )

        #carrega os documentos já indexados
        self.documentos = carregar_documentos()

        #carrega o índice invertido
        self.indice = carregar_indice()

        #carrega as stopwords
        self.stopwords = carregar_stopwords(
            CAMINHO_STOPWORDS
        )

        #guarda os resultados que estão sendo exibidos
        self.resultados_atuais = {}

        #monta os componentes da interface
        self.criar_interface()


    #cria os elementos da janela
    def criar_interface(self):

        #cria o espaço superior da interface
        frame_superior = ttk.Frame(
            self.root,
            padding=15
        )

        frame_superior.pack(
            fill="x"
        )

        #texto indicando o campo da consulta
        ttk.Label(
            frame_superior,
            text="Consulta:"
        ).pack(
            anchor="w"
        )

        #campo onde o usuário digita a consulta
        self.entrada_consulta = ttk.Entry(
            frame_superior,
            font=("Arial", 12)
        )

        self.entrada_consulta.pack(
            fill="x",
            pady=(5, 10)
        )

        #cria uma área para selecionar o modelo
        frame_modelo = ttk.Frame(
            frame_superior
        )

        frame_modelo.pack(
            fill="x"
        )

        #texto indicando a seleção do modelo
        ttk.Label(
            frame_modelo,
            text="Modelo:"
        ).pack(
            side="left"
        )

        #define o modelo padrão como vetorial
        self.modelo = tk.StringVar(
            value="Vetorial"
        )

        #botão para selecionar o modelo booleano
        ttk.Radiobutton(
            frame_modelo,
            text="Booleano",
            variable=self.modelo,
            value="Booleano"
        ).pack(
            side="left",
            padx=10
        )

        #botão para selecionar o modelo vetorial
        ttk.Radiobutton(
            frame_modelo,
            text="Espaço Vetorial",
            variable=self.modelo,
            value="Vetorial"
        ).pack(
            side="left"
        )

        #botão que executa a busca
        ttk.Button(
            frame_modelo,
            text="Buscar",
            command=self.buscar
        ).pack(
            side="right"
        )

        #área onde os resultados serão mostrados
        frame_resultados = ttk.Frame(
            self.root,
            padding=(15, 0, 15, 15)
        )

        frame_resultados.pack(
            fill="both",
            expand=True
        )

        #define as colunas da tabela
        colunas = (
            "doc_id",
            "titulo",
            "autor",
            "score"
        )

        #cria a tabela de resultados
        self.tabela = ttk.Treeview(
            frame_resultados,
            columns=colunas,
            show="headings"
        )

        #define o nome de cada coluna
        self.tabela.heading(
            "doc_id",
            text="DocId"
        )

        self.tabela.heading(
            "titulo",
            text="Título"
        )

        self.tabela.heading(
            "autor",
            text="Autor"
        )

        self.tabela.heading(
            "score",
            text="Relevância"
        )

        #define a largura das colunas
        self.tabela.column(
            "doc_id",
            width=60
        )

        self.tabela.column(
            "titulo",
            width=480
        )

        self.tabela.column(
            "autor",
            width=320
        )

        self.tabela.column(
            "score",
            width=100
        )

        #cria a barra de rolagem
        scrollbar = ttk.Scrollbar(
            frame_resultados,
            orient="vertical",
            command=self.tabela.yview
        )

        #liga a barra de rolagem à tabela
        self.tabela.configure(
            yscrollcommand=scrollbar.set
        )

        #posiciona a tabela
        self.tabela.pack(
            side="left",
            fill="both",
            expand=True
        )

        #posiciona a barra de rolagem
        scrollbar.pack(
            side="right",
            fill="y"
        )

        #duplo clique em um resultado abre o artigo
        self.tabela.bind(
            "<Double-1>",
            self.abrir_documento
        )

        #instrução para o usuário
        ttk.Label(
            self.root,
            text="Dê duplo clique em um resultado para abrir o artigo."
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 10)
        )


    #executa a busca digitada pelo usuário
    def buscar(self):

        #pega o texto da caixa de consulta
        consulta = (
            self.entrada_consulta
            .get()
            .strip()
        )

        #verifica se o usuário digitou alguma coisa
        if not consulta:
            messagebox.showwarning(
                "Consulta",
                "Digite uma consulta."
            )
            return

        #limpa os resultados anteriores
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        #limpa o dicionário de resultados
        self.resultados_atuais = {}

        try:

            #verifica qual modelo foi selecionado
            if self.modelo.get() == "Booleano":

                #realiza a busca usando o modelo booleano
                resultados = buscar_booleano(
                    consulta,
                    self.documentos,
                    self.indice,
                    self.stopwords
                )

                #mostra cada documento encontrado
                for doc_id in resultados:
                    self.inserir_resultado(
                        doc_id,
                        "-"
                    )

            else:

                #realiza a busca usando o modelo vetorial
                resultados = buscar_vetorial(
                    consulta,
                    self.documentos,
                    self.indice,
                    self.stopwords
                )

                #mostra os documentos e suas similaridades
                for doc_id, score in resultados:
                    self.inserir_resultado(
                        doc_id,
                        f"{score:.4f}"
                    )

            #avisa caso nenhum documento tenha sido encontrado
            if not resultados:
                messagebox.showinfo(
                    "Busca",
                    "Nenhum documento foi recuperado."
                )

        #mostra uma mensagem caso a consulta tenha algum erro
        except ValueError as erro:
            messagebox.showerror(
                "Consulta inválida",
                str(erro)
            )


    #adiciona um resultado à tabela
    def inserir_resultado(
        self,
        doc_id,
        score
    ):
        #pega os dados do documento
        documento = self.documentos[doc_id]

        #adiciona o documento na tabela
        item = self.tabela.insert(
            "",
            "end",
            values=(
                doc_id,
                documento["titulo"],
                documento["autor"],
                score
            )
        )

        #guarda a relação entre o item da tabela e o documento
        self.resultados_atuais[item] = doc_id


    #abre o PDF do artigo selecionado
    def abrir_documento(self, event):

        #pega o item selecionado na tabela
        item = self.tabela.focus()

        #se não houver item selecionado, encerra
        if not item:
            return

        #descobre qual documento está relacionado ao item
        doc_id = self.resultados_atuais.get(item)

        if doc_id is None:
            return

        #monta o caminho do PDF
        caminho = os.path.join(
            PASTA_ARTIGOS,
            f"artigo{doc_id}.pdf"
        )

        #verifica se o PDF realmente existe
        if not os.path.exists(caminho):
            messagebox.showwarning(
                "Arquivo não encontrado",
                f"Não foi encontrado:\n{caminho}\n\n"
                "Ajuste a pasta ou o nome dos PDFs no código."
            )
            return

        try:

            #abre o arquivo de acordo com o sistema operacional
            if sys.platform.startswith("win"):
                os.startfile(
                    os.path.abspath(caminho)
                )

            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["open", caminho]
                )

            else:
                subprocess.Popen(
                    ["xdg-open", caminho]
                )

        #caso ocorra algum erro ao abrir o PDF
        except Exception as erro:
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir o artigo:\n{erro}"
            )


#inicia a interface quando o arquivo é executado diretamente
if __name__ == "__main__":

    #cria a janela principal
    root = tk.Tk()

    #cria a aplicação
    app = InterfaceSRI(root)

    #mantém a janela aberta esperando as ações do usuário
    root.mainloop()