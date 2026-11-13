:- encoding(utf8).

% Perguntas sobre a base. Carregar depois de base.pl e regras.pl.

% 1. Quais países têm mais rodadas no top 1000?
%    ?- ranking_paises(Tabela).
rodadas_pais(C, N) :-
    pais(C),
    aggregate_all(count, pais_rodada(_, C), N).

ranking_paises(Tabela) :-
    setof(N-C, rodadas_pais(C, N), Crescente),
    reverse(Crescente, Tabela).

% 2. Qual a melhor média WCA de cada pessoa? (ranking crescente)
%    ?- ranking_media_wca(Tabela).
melhor_media_wca(P, Melhor) :-
    pessoa(P),
    findall(M, (competidor(R, P), media_wca(R, M), M \== dnf), Medias),
    min_list(Medias, Melhor).

ranking_media_wca(Tabela) :-
    setof(M-P, melhor_media_wca(P, M), Tabela).

% 3. Entre dois países, qual tem a menor média dos melhores tempos?
%    ?- compara_paises(usa, china, Vencedor, MediaA, MediaB).
media_melhor_pais(C, Media) :-
    pais(C),
    findall(M, (pais_rodada(R, C), melhor_tempo(R, M)), Tempos),
    media_lista(Tempos, Media).

compara_paises(A, B, Vencedor, MA, MB) :-
    media_melhor_pais(A, MA),
    media_melhor_pais(B, MB),
    (MA =< MB -> Vencedor = A ; Vencedor = B).

% 4. Quem é mais consistente? Menor amplitude média em rodadas sem dnf,
%    entre pessoas com pelo menos Min rodadas.
%    ?- ranking_consistencia(5, Tabela).
amplitude_media(P, Min, Media, N) :-
    pessoa(P),
    findall(A, (competidor(R, P), rodada_limpa(R), amplitude(R, A)), Amps),
    length(Amps, N),
    N >= Min,
    media_lista(Amps, Media).

ranking_consistencia(Min, Tabela) :-
    setof(Media-P, N^amplitude_media(P, Min, Media, N), Tabela).

% 5. Quem lidera cada país em número de rodadas?
%    ?- lider_pais(C, P, N).
rodadas_pessoa_pais(P, C, N) :-
    representa(P, C),
    aggregate_all(count, solve(_, P, _, _, _, _, _, _, C), N).

lider_pais(C, P, N) :-
    pais(C),
    aggregate_all(max(N0, P0), rodadas_pessoa_pais(P0, C, N0), max(N, P)).
