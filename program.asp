# Copyright (C) 2026 Cristian Liporace
# Licensed under the GNU General Public License v3.0
# See LICENSE file for details.

stesso_nucleo(Pair, P0, P1) :- proposizione(Pair, 0, P0, S, A, O), proposizione(Pair, 1, P1, S, A, O).
contraddizione(Pair, negazione, P0, P1) :- stesso_nucleo(Pair, P0, P1), forma(Pair, 0, P0, Pol0), forma(Pair, 1, P1, Pol1), Pol0!=Pol1

modalita_incompatibile(obbligatorio, vietato).
modalita_incompatibile(vietato, obbligatorio).
modalita_incompatibile(facoltativo, vietato).
modalita_incompatibile(vietato, facoltativo).
modalita_incompatibile(neutrale, vietato).
modalita_incompatibile(vietato, neutrale).

contraddizione(Pair, modale, P0, P1) :-
    stesso_nucleo(Pair, P0, P1),
    modalita(Pair, 0, P0, M0),
    modalita(Pair, 1, P1, M1),
    modalita_incompatibile(M0, M1).

coppia_quantita(Pair,P0,P1,Concetto,Unita,Op0,V0,Op1,V1) :-
    stesso_nucleo(Pair, P0, P1),
    quantita(Pair, 0, P0, Concetto, Op0, V0, Unita),
    quantita(Pair, 1, P1, Concetto, Op1, V1, Unita).

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, eq, V0, eq, V1),
    V0 != V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, eq, V0, gt, V1),
    V0 <= V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, gt, V0, eq, V1),
    V1 <= V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, eq, V0, ge, V1),
    V0 < V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, ge, V0, eq, V1),
    V1 < V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, eq, V0, lt, V1),
    V0 >= V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, lt, V0, eq, V1),
    V1 >= V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, eq, V0, le, V1),
    V0 > V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, le, V0, eq, V1),
    V1 > V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, gt, V0, lt, V1),
    V0 >= V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, lt, V0, gt, V1),
    V1 >= V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, gt, V0, le, V1),
    V0 >= V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, le, V0, gt, V1),
    V1 >= V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, ge, V0, lt, V1),
    V0 >= V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, lt, V0, ge, V1),
    V1 >= V0.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, ge, V0, le, V1),
    V0 > V1.

incompatibilita_numerica(Pair, P0, P1) :-
    coppia_quantita(Pair, P0, P1, C, U, le, V0, ge, V1),
    V1 > V0.

contraddizione(Pair, numerica, P0, P1) :-
    incompatibilita_numerica(Pair, P0, P1).

azione_direzionale(nominare).
azione_direzionale(eleggere).
azione_direzionale(designare).
azione_direzionale(approvare).
azione_direzionale(proporre).
azione_direzionale(revocare).
azione_direzionale(sostituire).
azione_direzionale(convocare).

contraddizione(Pair, strutturale, P0, P1) :-
    proposizione(Pair, 0, P0, S, A, O),
    proposizione(Pair, 1, P1, O, A, S),
    azione_direzionale(A),
    S != O.

contraddizione(Pair, attributiva, P0, P1) :-
    proposizione(Pair, 0, P0, S0, A, O),
    proposizione(Pair, 1, P1, S1, A, O),
    S0 != S1,
    esclusivita(Pair, 0, P0).

contraddizione(Pair, attributiva, P0, P1) :-
    proposizione(Pair, 0, P0, S0, A, O),
    proposizione(Pair, 1, P1, S1, A, O),
    S0 != S1,
    esclusivita(Pair, 1, P1).