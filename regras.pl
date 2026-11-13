:- encoding(utf8).

% Regras auxiliares sobre solve/9. Carregar depois de base.pl.
% R = Rank (identifica a rodada). Tempos em centésimos; dnf = não concluída.

% Domínio (sem repetição)

rodada(R) :-
    solve(R, _, _, _, _, _, _, _, _).

pessoa(P) :-
    setof(X, R^S1^S2^S3^S4^S5^M^C^solve(R, X, S1, S2, S3, S4, S5, M, C), Pessoas),
    member(P, Pessoas).

pais(C) :-
    setof(X, R^P^S1^S2^S3^S4^S5^M^solve(R, P, S1, S2, S3, S4, S5, M, X), Paises),
    member(C, Paises).

competidor(R, P) :- solve(R, P, _, _, _, _, _, _, _).
pais_rodada(R, C) :- solve(R, _, _, _, _, _, _, _, C).
melhor_tempo(R, M) :- solve(R, _, _, _, _, _, _, M, _).

% Países pelos quais P competiu.
representa(P, C) :-
    pessoa(P),
    setof(X, R^S1^S2^S3^S4^S5^M^solve(R, P, S1, S2, S3, S4, S5, M, X), Paises),
    member(C, Paises).

% Tentativas

tentativas(R, [S1, S2, S3, S4, S5]) :-
    solve(R, _, S1, S2, S3, S4, S5, _, _).

tentativa_valida(T) :-
    integer(T).

tentativas_validas(R, Validas) :-
    tentativas(R, Todas),
    include(tentativa_valida, Todas, Validas).

qtd_dnf(R, N) :-
    tentativas(R, Todas),
    include(==(dnf), Todas, Dnfs),
    length(Dnfs, N).

tem_dnf(R) :-
    qtd_dnf(R, N),
    N > 0.

rodada_limpa(R) :-
    rodada(R),
    \+ tem_dnf(R).

pior_tempo(R, Pior) :-
    tentativas_validas(R, Validas),
    max_list(Validas, Pior).

% Médias e consistência

media_lista(Lista, Media) :-
    Lista \= [],
    sum_list(Lista, Soma),
    length(Lista, N),
    Media is Soma / N.

% Média WCA: descarta o melhor e o pior (dnf conta como pior) e
% faz a média dos 3 restantes. Com 2 ou mais dnf, a média é dnf.
media_wca(R, dnf) :-
    qtd_dnf(R, N),
    N >= 2.
media_wca(R, Media) :-
    qtd_dnf(R, N),
    N < 2,
    tentativas_validas(R, Validas),
    msort(Validas, [_Melhor | Resto]),
    length(Meio, 3),
    append(Meio, _, Resto),
    media_lista(Meio, MediaReal),
    Media is round(MediaReal).

media_simples(R, Media) :-
    tentativas_validas(R, Validas),
    media_lista(Validas, Media).

% Pior menos melhor tempo; menor = mais consistente.
amplitude(R, A) :-
    melhor_tempo(R, Melhor),
    pior_tempo(R, Pior),
    A is Pior - Melhor.

% Utilidades

segundos(dnf, dnf) :- !.
segundos(C, S) :-
    S is C / 100.0.

abaixo_de(R, Limite) :-
    melhor_tempo(R, Melhor),
    Melhor < Limite.
