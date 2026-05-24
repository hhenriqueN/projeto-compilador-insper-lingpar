# GoLite Compiler

[![Compilation Status](https://compiler-tester.insper-comp.com.br/svg/hhenriqueN/projeto-compilador-insper-lingpar)](https://compiler-tester.insper-comp.com.br/svg/hhenriqueN/projeto-compilador-insper-lingpar)

A compiler for **GoLite** — a statically-typed subset of the Go programming language — that targets **x86-32 assembly** (NASM). Built in Python as an academic project for the Languages and Paradigms course at Insper.

---

## Table of Contents

- [Overview](#overview)
- [Source Language](#source-language)
- [Compiler Pipeline](#compiler-pipeline)
- [Grammar (EBNF)](#grammar-ebnf)
- [AST Node Types](#ast-node-types)
- [Installation & Usage](#installation--usage)
- [Example](#example)

---

## Overview

GoLite compiles a Go-like language with integers, strings, booleans, functions, control flow, and I/O into x86-32 assembly. The generated `.asm` file can be assembled with NASM and linked to produce a native Linux executable.

```
source.go  →  [ GoLite Compiler ]  →  output.asm  →  [ NASM + ld ]  →  executable
```

---

## Source Language

GoLite supports the following constructs from Go:

| Feature | Syntax |
|---|---|
| Variable declaration | `var x int = 5` |
| Types | `int`, `string`, `bool` |
| Arithmetic | `+`, `-`, `*`, `/` |
| Comparison | `==`, `<`, `>` |
| Logical | `&&`, `\|\|`, `!` |
| Conditional | `if / else` |
| Loop | `for <condition> { }` |
| Functions | `func name(p type) returnType { }` |
| Output | `Println(x)` |
| Input | `Scanln(&x)` |
| Comments | `// single-line` |

---

## Compiler Pipeline

The compiler is structured as a classic multi-stage pipeline:

```
┌─────────────┐
│  Source File │  (*.go)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   Preprocessor  │  Remove comments (//)
│   (PrepPro)     │
└────────┬────────┘
         │  cleaned source string
         ▼
┌─────────────────┐
│     Lexer       │  Tokenize: keywords, identifiers,
│                 │  literals, operators, delimiters
└────────┬────────┘
         │  Token stream
         ▼
┌─────────────────────────────────┐
│   Parser (Recursive Descent)    │  Build Abstract Syntax Tree
│                                 │  Enforce syntactic grammar
└────────────────┬────────────────┘
                 │  AST
                 ▼
┌─────────────────────────────────┐
│     Semantic Analysis           │  Type checking, scope resolution,
│     (Node.evaluate)             │  symbol table management
└────────────────┬────────────────┘
                 │  Validated AST
                 ▼
┌─────────────────────────────────┐
│     Code Generation             │  Walk AST, emit NASM x86-32
│     (Node.generate)             │  assembly instructions
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────┐
│   output.asm    │  x86-32 NASM assembly
└─────────────────┘
```

### Stages in detail

| Stage | Class | Responsibility |
|---|---|---|
| Preprocessing | `PrepPro` | Strip `//` comments via regex |
| Lexical Analysis | `Lexer` | Produce `Token(kind, value)` stream |
| Parsing | `Parser` | Recursive descent; builds AST from grammar rules |
| Semantic Analysis | `Node.evaluate()` | Type checking, scoped `SymbolTable` lookups |
| Code Generation | `Node.generate()` | Emit NASM instructions; manage stack offsets |

---

## Grammar (EBNF)

```ebnf
Program       = { FuncDec }, FuncCall("main") ;

FuncDec       = "func", IDEN, "(", [ Params ], ")", [ Type ], Block ;
Params        = IDEN, Type, { ",", IDEN, Type } ;

Block         = "{", { Statement }, "}" ;

Statement     = ( Print
               | VarDec
               | Assignment
               | FuncCall
               | If
               | For
               | Return
               ), "\n" ;

Print         = "Println", "(", BoolExpr, ")" ;
VarDec        = "var", IDEN, Type, [ "=", BoolExpr ] ;
Assignment    = IDEN, "=", BoolExpr ;
FuncCall      = IDEN, "(", [ Args ], ")" ;
If            = "if", BoolExpr, Block, [ "else", Block ] ;
For           = "for", BoolExpr, Block ;
Return        = "return", BoolExpr ;

BoolExpr      = BoolTerm, { "||", BoolTerm } ;
BoolTerm      = RelExpr,  { "&&", RelExpr  } ;
RelExpr       = Expr, [ ( "==" | "<" | ">" ), Expr ] ;
Expr          = Term, { ( "+" | "-" ), Term } ;
Term          = Factor, { ( "*" | "/" ), Factor } ;
Factor        = ( "+" | "-" | "!" ), Factor
               | "(", BoolExpr, ")"
               | INT
               | STRING
               | BOOL
               | IDEN
               | FuncCall
               | Scanln ;

Scanln        = ( "Scanln" | "Scan" ), "(", "&", IDEN, ")" ;

Type          = "int" | "string" | "bool" ;
INT           = digit, { digit } ;
STRING        = '"', { char }, '"' ;
BOOL          = "true" | "false" ;
IDEN          = letter, { letter | digit | "_" } ;
```

---

## AST Node Types

```
Node (abstract)
├── Literals
│   ├── IntVal        — integer constant
│   ├── BoolVal       — boolean constant
│   └── StringVal     — string constant
│
├── Operators
│   ├── BinOp         — binary: +  -  *  /  ==  <  >  &&  ||
│   └── UnOp          — unary:  +  -  !
│
├── Variables
│   ├── VarDec        — declaration: var x int = expr
│   ├── Identifier    — variable reference
│   └── Assingment    — assignment: x = expr
│
├── Control Flow
│   ├── If            — if / else
│   └── For           — condition loop
│
├── I/O
│   ├── Print         — Println(expr)
│   └── Read          — Scanln(&x) / Scan(&x)
│
├── Functions
│   ├── FuncDec       — function declaration
│   ├── FuncCall      — function invocation
│   └── Return        — return statement
│
└── Block             — sequence of statements (owns a SymbolTable scope)
```

### Symbol Table

Each `Block` and `FuncDec` creates a new `SymbolTable` scope chained to its parent. Variable lookup walks the chain upward, enabling lexical scoping. Each entry stores:

```
Variable { value, type, shift (stack offset), func (bool) }
```

---

## Installation & Usage

**Requirements:** Python 3.10+

```bash
# Clone the repository
git clone https://github.com/hhenriqueN/projeto-compilador-insper-lingpar.git
cd projeto-compilador-insper-lingpar

# Compile a source file
python main.py <source_file.go>
```

To assemble and run the generated output (Linux, NASM required):

```bash
nasm -f elf32 output.asm -o output.o
ld -m elf_i386 output.o -o program -lc -dynamic-linker /lib/ld-linux.so.2
./program
```

---

## Example

**source.go**
```go
func add(a int, b int) int {
    return a + b
}

func main() {
    var x int = 10
    var y int = 32
    var result int
    result = add(x, y)
    Println(result)
}
```

**Generated x86-32 assembly (excerpt)**
```asm
section .data
    format_out db "%d", 10, 0
    format_in  db "%d", 0

section .text
    global _start
    extern printf, scanf

_start:
    push ebp
    mov  ebp, esp
    call main
    mov  eax, 1
    int  0x80

main:
    push ebp
    mov  ebp, esp
    sub  esp, 12        ; allocate locals (x, y, result)
    mov  eax, 10
    mov  [ebp - 4], eax ; x = 10
    mov  eax, 32
    mov  [ebp - 8], eax ; y = 32
    ; ... call add, store result, printf ...
    mov  esp, ebp
    pop  ebp
    ret
```

**Output**
```
42
```
