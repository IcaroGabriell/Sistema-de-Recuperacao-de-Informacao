import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from indexador import carregar_stopwords
from recuperacao import (
    carregar_documentos,
    carregar_indice,
    buscar_booleano,
    buscar_vetorial,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CAMINHO_STOPWORDS = os.path.join(
    BASE_DIR, "stopwords.txt"
)

PASTA_ARTIGOS = os.path.join(
    BASE_DIR, "artigos"
)


class InterfaceSRI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Recuperação de Informação")
        self.root.geometry("1000x650")

        self.documentos = carregar_documentos()
        self.indice = carregar_indice()
        self.stopwords = carregar_stopwords(CAMINHO_STOPWORDS)

        self.resultados_atuais = {}

        self.criar_interface()

    def criar_interface(self):
        frame_superior = ttk.Frame(self.root, padding=15)
        frame_superior.pack(fill="x")

        ttk.Label(
            frame_superior,
            text="Consulta:"
        ).pack(anchor="w")

        self.entrada_consulta = ttk.Entry(
            frame_superior,
            font=("Arial", 12)
        )
        self.entrada_consulta.pack(
            fill="x",
            pady=(5, 10)
        )

        frame_modelo = ttk.Frame(frame_superior)
        frame_modelo.pack(fill="x")

        ttk.Label(
            frame_modelo,
            text="Modelo:"
        ).pack(side="left")

        self.modelo = tk.StringVar(value="Vetorial")

        ttk.Radiobutton(
            frame_modelo,
            text="Booleano",
            variable=self.modelo,
            value="Booleano"
        ).pack(side="left", padx=10)

        ttk.Radiobutton(
            frame_modelo,
            text="Espaço Vetorial",
            variable=self.modelo,
            value="Vetorial"
        ).pack(side="left")

        ttk.Button(
            frame_modelo,
            text="Buscar",
            command=self.buscar
        ).pack(side="right")

        frame_resultados = ttk.Frame(
            self.root,
            padding=(15, 0, 15, 15)
        )
        frame_resultados.pack(
            fill="both",
            expand=True
        )

        colunas = ("doc_id", "titulo", "autor", "score")

        self.tabela = ttk.Treeview(
            frame_resultados,
            columns=colunas,
            show="headings"
        )

        self.tabela.heading("doc_id", text="DocId")
        self.tabela.heading("titulo", text="Título")
        self.tabela.heading("autor", text="Autor")
        self.tabela.heading("score", text="Relevância")

        self.tabela.column("doc_id", width=60)
        self.tabela.column("titulo", width=480)
        self.tabela.column("autor", width=320)
        self.tabela.column("score", width=100)

        scrollbar = ttk.Scrollbar(
            frame_resultados,
            orient="vertical",
            command=self.tabela.yview
        )

        self.tabela.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabela.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tabela.bind(
            "<Double-1>",
            self.abrir_documento
        )

        ttk.Label(
            self.root,
            text="Dê duplo clique em um resultado para abrir o artigo."
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 10)
        )

    def buscar(self):
        consulta = self.entrada_consulta.get().strip()

        if not consulta:
            messagebox.showwarning(
                "Consulta",
                "Digite uma consulta."
            )
            return

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        self.resultados_atuais = {}

        try:
            if self.modelo.get() == "Booleano":
                resultados = buscar_booleano(
                    consulta,
                    self.documentos,
                    self.indice,
                    self.stopwords
                )

                for doc_id in resultados:
                    self.inserir_resultado(
                        doc_id,
                        "-"
                    )

            else:
                resultados = buscar_vetorial(
                    consulta,
                    self.documentos,
                    self.indice,
                    self.stopwords
                )

                for doc_id, score in resultados:
                    self.inserir_resultado(
                        doc_id,
                        f"{score:.4f}"
                    )

            if not resultados:
                messagebox.showinfo(
                    "Busca",
                    "Nenhum documento foi recuperado."
                )

        except ValueError as erro:
            messagebox.showerror(
                "Consulta inválida",
                str(erro)
            )

    def inserir_resultado(self, doc_id, score):
        documento = self.documentos[doc_id]

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

        self.resultados_atuais[item] = doc_id

    def abrir_documento(self, event):
        item = self.tabela.focus()

        if not item:
            return

        doc_id = self.resultados_atuais.get(item)

        if doc_id is None:
            return

        caminho = os.path.join(
            PASTA_ARTIGOS,
            f"artigo{doc_id}.pdf"
        )

        if not os.path.exists(caminho):
            messagebox.showwarning(
                "Arquivo não encontrado",
                f"Não foi encontrado:\n{caminho}\n\n"
                "Ajuste a pasta ou o nome dos PDFs no código."
            )
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(os.path.abspath(caminho))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", caminho])
            else:
                subprocess.Popen(["xdg-open", caminho])

        except Exception as erro:
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir o artigo:\n{erro}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = InterfaceSRI(root)
    root.mainloop()
