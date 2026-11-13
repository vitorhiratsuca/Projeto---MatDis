# Projeto---MatDis: Knowledge Engine de Rubik's Cube

Base de conhecimento em Prolog com os 1000 tempos (single) mais rápidos de cubo mágico 3x3 em competições oficiais, construída a partir de um dataset do Kaggle, com perguntas respondidas por inferência lógica.

## Dataset

- Fonte: [Top 1000 Fastest Rubik's Cube Solves](https://www.kaggle.com/datasets/darshanvss/top-1000-fastest-rubiks-cube-solves) (Kaggle)
- Arquivo usado: `data/solves.csv` (tabela única, 1000 linhas)
- Cada linha é uma rodada oficial de 5 tentativas cujo melhor tempo está no top 1000.

| Campo CSV | Tipo | No Prolog |
|---|---|---|
| `#` | quantitativo | `Rank` |
| `Person` | qualitativo | `Pessoa` |
| `Solve 1` .. `Solve 5` | quantitativo | `S1` .. `S5` |
| `Fastest Solve` | quantitativo | `Melhor` |
| `Country` | qualitativo | `Pais` |

Tempos em centésimos de segundo (`347` = 3,47 s). Tentativa não concluída (DNF) vira o átomo `dnf`.

## Estrutura

```
data/solves.csv   dataset original
etl.py            ETL: CSV -> base.pl
base.pl           base de conhecimento (fatos solve/9)
regras.pl         regras auxiliares
perguntas.pl      perguntas
```

## Construção

### 1. ETL (`etl.py`)

Lê o CSV e gera um fato por linha:

```prolog
solve(Rank, Pessoa, S1, S2, S3, S4, S5, Melhor, Pais).
solve(1, yusheng_du, 1113, 347, 880, dnf, 707, 347, china).
```

- Nomes e países viram átomos: minúsculos, sem acento, com `_` e sem o nome nativo entre parênteses (`Łukasz Burliga` -> `lukasz_burliga`).
- `DNF` vira `dnf`.
- Validações: rank único, `Melhor` igual ao mínimo das tentativas, nenhum par de nomes distintos gerando o mesmo átomo.

Resultado: 1000 fatos, 185 pessoas, 43 países, 36 rodadas com `dnf`.

### 2. Regras auxiliares (`regras.pl`)

| Regra | Significado |
|---|---|
| `rodada/1`, `pessoa/1`, `pais/1` | domínio, sem repetição |
| `competidor/2`, `pais_rodada/2`, `melhor_tempo/2` | projeções de `solve/9` |
| `representa(P, C)` | países pelos quais `P` competiu |
| `tentativas/2`, `tentativas_validas/2` | tentativas da rodada (todas / sem `dnf`) |
| `qtd_dnf/2`, `tem_dnf/1`, `rodada_limpa/1` | contagem e presença de `dnf` |
| `pior_tempo/2` | maior tempo concluído |
| `media_wca/2` | média oficial: descarta melhor e pior (`dnf` = pior), média dos 3 restantes; 2+ `dnf` -> `dnf` |
| `media_simples/2`, `media_lista/2` | médias aritméticas |
| `amplitude/2` | pior - melhor (consistência) |
| `segundos/2`, `abaixo_de/2` | conversão e filtro por tempo |

### 3. Perguntas (`perguntas.pl`)

Todas usam agregação, ordenação ou composição de regras.

**1. Quais países têm mais rodadas no top 1000?**

```prolog
?- ranking_paises(Tabela).
Tabela = [469-usa, 112-poland, 93-australia, 44-germany, 40-china, ...]
```

**2. Qual a melhor média WCA de cada pessoa?**

```prolog
?- ranking_media_wca(Tabela).
Tabela = [486-max_park, 486-tymon_kolasinski, 503-luke_garrett, 524-leo_borromeo, 525-matty_hiroto_inaba, ...]
```

**3. Entre dois países, qual tem a menor média dos melhores tempos?**

```prolog
?- compara_paises(usa, china, Vencedor, MediaA, MediaB).
Vencedor = china, MediaA = 511.49..., MediaB = 509.125
```

**4. Quem é mais consistente (menor amplitude média em rodadas sem `dnf`, com pelo menos 5 rodadas)?**

```prolog
?- ranking_consistencia(5, Tabela).
Tabela = [195.11...-max_park, 222.26...-tymon_kolasinski, 236.21...-matty_hiroto_inaba, ...]
```

**5. Quem lidera cada país em número de rodadas?**

```prolog
?- lider_pais(C, P, N).
C = australia, P = feliks_zemdegs, N = 75 ;
C = brazil, P = caio_hideaki_sato, N = 5 ;
C = china, P = ruihang_xu, N = 16 ;
...
```

## Como rodar

### Gerar a base

```bash
python etl.py
```

Requer Python 3.9+ (somente biblioteca padrão). Opcional: `python etl.py entrada.csv saida.pl`.

### SWISH

1. Acesse https://swish.swi-prolog.org/ e crie um Program.
2. Cole, nesta ordem, o conteúdo de `base.pl`, `regras.pl` e `perguntas.pl` na área Program.
3. Rode as queries acima na área Query.

### SWI-Prolog local

```bash
swipl base.pl regras.pl perguntas.pl
?- ranking_paises(T).
```
