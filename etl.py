"""ETL: converte data/solves.csv (Kaggle) na base de conhecimento Prolog base.pl.

Dataset: "Top 1000 Fastest Rubik's Cube Solves"
https://www.kaggle.com/datasets/darshanvss/top-1000-fastest-rubiks-cube-solves

Cada linha do CSV vira um fato

    solve(Rank, Pessoa, S1, S2, S3, S4, S5, Melhor, Pais).

Uso:
    python etl.py                      # lê data/solves.csv e escreve base.pl
    python etl.py entrada.csv saida.pl
"""

import csv
import re
import sys
import unicodedata
from pathlib import Path

ENTRADA_PADRAO = Path("data/solves.csv")
SAIDA_PADRAO = Path("base.pl")

# Letras que a decomposição Unicode (NFKD) não reduz a ASCII sozinha.
LETRAS_ESPECIAIS = {
    "ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE",
    "ı": "i", "ß": "ss", "đ": "d", "Đ": "D",
}

CABECALHO = """\
:- encoding(utf8).

% =====================================================================
% Base de conhecimento: Top 1000 Fastest Rubik's Cube Solves (3x3)
% Fonte: https://www.kaggle.com/datasets/darshanvss/top-1000-fastest-rubiks-cube-solves
% Arquivo gerado automaticamente por etl.py. Não edite à mão.
% =====================================================================
%
% Domínio (universo de discurso):
%   - Rodadas oficiais de 5 tentativas de cubo 3x3 cujo melhor tempo
%     está entre os 1000 mais rápidos do mundo.
%   - Pessoas (competidores), países e tempos.
%
% Predicado (axiomas não lógicos da teoria):
%   solve(Rank, Pessoa, S1, S2, S3, S4, S5, Melhor, Pais)
%     "A rodada de posição Rank no ranking foi feita por Pessoa,
%      representante de Pais, com as tentativas S1..S5 e o melhor
%      tempo Melhor."
%
%   Rank       : inteiro, 1..{n} (posição no ranking de melhor tempo)
%   Pessoa     : átomo, nome sem acentos (ex.: max_park)
%   S1..S5     : inteiro em centésimos de segundo (347 = 3,47 s)
%                ou o átomo dnf (Did Not Finish, tentativa não concluída)
%   Melhor     : inteiro em centésimos de segundo, min(S1..S5) sem dnf
%   Pais       : átomo (ex.: usa, united_kingdom)
%
% Propriedades garantidas pelo ETL (verificadas em etl.py):
%   ∀r (Rank(r) é único)
%   ∀r (Melhor(r) = min{{Si(r) | Si(r) ≠ dnf}})
%   ∀r (pelo menos uma tentativa de r é diferente de dnf)
%
% Exemplo de consulta no SWISH (área Query):
%   ?- solve(_, max_park, _, _, _, _, _, Melhor, _).
% =====================================================================

"""


def para_atomo(texto: str) -> str:
    """Normaliza um texto para um átomo Prolog: minúsculo, ASCII, com underscores.

    Remove o nome nativo entre parênteses, por exemplo
    "Yusheng Du (杜宇生)" vira yusheng_du.
    """
    texto = re.sub(r"\s*\(.*?\)", "", texto)
    texto = "".join(LETRAS_ESPECIAIS.get(c, c) for c in texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto.lower()).strip("_")
    if not texto or not texto[0].isalpha():
        raise ValueError(f"não foi possível gerar um átomo válido a partir de {texto!r}")
    return texto


def para_tempo(valor: str):
    """Converte uma tentativa: inteiro em centésimos ou o átomo dnf."""
    valor = valor.strip()
    if valor.upper() in {"DNF", "DNS"}:
        return "dnf"
    return int(valor)


def ler_solves(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    solves = []
    for linha in linhas:
        tentativas = [para_tempo(linha[f"Solve {i}"]) for i in range(1, 6)]
        validas = [t for t in tentativas if t != "dnf"]
        melhor = int(linha["Fastest Solve"])

        if not validas:
            raise ValueError(f"rodada {linha['#']} sem nenhuma tentativa válida")
        if melhor != min(validas):
            raise ValueError(
                f"rodada {linha['#']}: Fastest Solve={melhor}, mas o mínimo é {min(validas)}"
            )

        solves.append({
            "rank": int(linha["#"]),
            "pessoa": para_atomo(linha["Person"]),
            "nome_original": linha["Person"],
            "tentativas": tentativas,
            "melhor": melhor,
            "pais": para_atomo(linha["Country"]),
        })
    return solves


def validar(solves: list[dict]) -> None:
    ranks = [s["rank"] for s in solves]
    if len(ranks) != len(set(ranks)):
        raise ValueError("há ranks repetidos no CSV")

    # Dois nomes diferentes não podem virar o mesmo átomo. Diferença só de
    # maiúsculas conta como a mesma pessoa (ex.: "Danny SungIn Park" e
    # "Danny Sungin Park" aparecem grafados das duas formas no CSV).
    origem: dict[str, str] = {}
    for s in solves:
        anterior = origem.setdefault(s["pessoa"], s["nome_original"])
        if anterior.casefold() != s["nome_original"].casefold():
            raise ValueError(
                f"colisão de átomo {s['pessoa']!r}: {anterior!r} e {s['nome_original']!r}"
            )


def formatar_fato(s: dict) -> str:
    args = [s["rank"], s["pessoa"], *s["tentativas"], s["melhor"], s["pais"]]
    return f"solve({', '.join(str(a) for a in args)})."


def main() -> None:
    entrada = Path(sys.argv[1]) if len(sys.argv) > 1 else ENTRADA_PADRAO
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else SAIDA_PADRAO

    solves = ler_solves(entrada)
    validar(solves)
    solves.sort(key=lambda s: s["rank"])

    conteudo = CABECALHO.format(n=len(solves))
    conteudo += "\n".join(formatar_fato(s) for s in solves) + "\n"
    saida.write_text(conteudo, encoding="utf-8")

    pessoas = {s["pessoa"] for s in solves}
    paises = {s["pais"] for s in solves}
    dnfs = sum(1 for s in solves if "dnf" in s["tentativas"])
    print(f"{len(solves)} fatos solve/9 escritos em {saida}")
    print(f"{len(pessoas)} pessoas, {len(paises)} países, {dnfs} rodadas com dnf")


if __name__ == "__main__":
    main()
