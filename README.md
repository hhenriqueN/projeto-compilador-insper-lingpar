# projeto-compilador-insper-lingpar

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/hhenriqueN/projeto-compilador-insper-lingpar)](https://compiler-tester.insper-comp.com.br/svg/hhenriqueN/projeto-compilador-insper-lingpar)

This repository is monitored by Compiler Tester for automatic compilation status.


```blockdiag blockdiag { span_width = 2; span_height = 12; default_fontsize = 14; node_height = 30;

A1 [label = '', shape = none, width = 1]; A2 [label = '', shape = none, width = 1]; A3 [label = '', shape = none, width = 1];

C1 [label = '', shape = none, width = 1]; C2 [label = '', shape = none, width = 1]; C3 [label = '', shape = none, width = 1];

P [label = 'EXPRESSION', color = none, style = none, shape = beginpoint, width=150 ]; D [label = '', color = none, style = none, shape = endpoint, width=150 ];

INT [shape = circle]; PLUS [label = '+', shape = circle]; MINUS [label = '-', shape = circle];

C [shape = none]; P -- A1 A1 -> INT INT -- C1 -> D; group { color = none; A1; A2; A3; }

group { color = none; INT; PLUS; MINUS; }

group { color = none; C1; C2; C3; }

A2 -- PLUS; A3 -- MINUS; A2 -> A1 [folded]; A3 -- A2 [folded];

INT -- C1 PLUS <- C2 MINUS <- C3 C1 -- C2 [folded]; C2 -- C3 [folded]; } ```