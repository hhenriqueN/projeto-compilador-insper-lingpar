# projeto-compilador-insper-lingpar

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/hhenriqueN/projeto-compilador-insper-lingpar)](https://compiler-tester.insper-comp.com.br/svg/hhenriqueN/projeto-compilador-insper-lingpar)

This repository is monitored by Compiler Tester for automatic compilation status.


```blockdiag blockdiag { span_width = 2; span_height = 12; default_fontsize = 14; node_height = 30;

EXPRESSION = TERM, { ("+" | "-"), TERM } ;
TERM = FACTOR, { ("*" | "/"), FACTOR } ;
FACTOR = ("+" | "-"), FACTOR | "(", EXPRESSION, ")" | NUMBER ;
NUMBER = DIGIT, {DIGIT} ;
DIGIT = 0 | 1 | ... | 9 ;
