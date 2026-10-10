# Sistema de Recuperação de Informação

Projeto desenvolvido para a disciplina de **Organização e Recuperação da Informação**, do curso de Engenharia de Computação da UEMG – Divinópolis.

O sistema realiza consultas em uma coleção de 20 artigos acadêmicos sobre Engenharia de Software, utilizando os modelos **Booleano** e **Espaço Vetorial**.

## Funcionalidades

- Indexação dos documentos e remoção de stopwords.
- Busca booleana com operadores `AND`, `OR` e `NOT`.
- Busca vetorial com TF-IDF e similaridade do cosseno.
- Exibição dos resultados com título, autor e relevância.
- Abertura dos artigos em PDF pela interface gráfica.

## Tecnologias

- Python
- Tkinter
- CSV

## Como executar

1. Clone o repositório:

   ```bash
   git clone https://github.com/IcaroGabriell/Sistema-de-Recuperacao-de-Informacao.git
   ```

2. Entre na pasta do projeto:

   ```bash
   cd Sistema-de-Recuperacao-de-Informacao/Projeto
   ```

3. Execute a interface:

   ```bash
   python interface.py
   ```

Certifique-se de que as pastas `artigos/` e `vocabularios/`, além dos arquivos necessários, estejam no mesmo diretório dos scripts.

## Relatório

O relatório acadêmico, com a descrição do desenvolvimento e os resultados do projeto, está disponível neste repositório em [📄 Relatório do projeto](./SRI_Relatorio.pdf)

## Autores

**Ícaro Gabriel dos Santos**  
**Raphael Muro Pimentel**

Engenharia de Computação — UEMG Divinópolis  
2026
