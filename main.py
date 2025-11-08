import sys
import re
import os

name_map = {
    "int":"INT","mult":"MULT","div":"DIV","plus":"PLUS","minus":"MINUS",
    "end":"EOL","EOF":"EOL",
    "iden":"IDEN","open_par":"OPEN_PAR","close_par":"CLOSE_PAR",
    "open_bra":"OPEN_BRA","close_bra":"CLOSE_BRA",
    "bool":"BOOL","str":"STR","assign":"ASSIGN","equals":"EQUALS",
    "gt":"GT","lt":"LT","or":"OR","and":"AND","not":"NOT",
    "print":"PRINT","println":"PRINTLN","var":"VAR","scanln":"SCANLN","scan":"SCAN"
}

op_map = {"plus": "add", "minus": "sub", "mult": "imul", "div": "idiv"}

class Token:
    def __init__(self, kind, value):
        self.kind: str = kind
        self.value: str | int = value

class PrepPro():
    @staticmethod
    def filter(code: str) -> str:
        return re.sub(r"//.*", "", code)

class Variable():
    def __init__(self, value: int, type: str, shift: int|None = None, func: bool = False):
        self.value: int = value
        self.type: str = type
        self.shift: int = shift
        self.func: bool = func

class SymbolTable():
    def __init__(self, parent = None):
        self.table: dict[str, Variable] = {}
        self.parent: 'SymbolTable' = parent

    def create_variable(self, name: str, type: str):
        if name in self.table:
            raise Exception("[Semantic] Declaracao dupla (tentou declarar variavel ja declarada)")
        shift = (len(self.table) + 1) * 4
        self.table[name] = Variable(None, type, shift)
        return shift

    def create_function(self, name: str, func_node, return_type: str|None):
        if name in self.table:
            raise Exception("[Semantic] Declaracao dupla (tentou declarar funcao ja declarada)")
        self.table[name] = Variable(func_node, return_type, shift=None, func=True)

    def set(self, name: str, var: Variable) -> None:
        if name in self.table:
            declared = self.table[name]
            if declared.func:
                raise Exception(f"[Semantic] '{name}' é uma função e não pode receber atribuição")
            if declared.type != var.type:
                raise Exception("[Semantic] Atribuicao de tipo invalido")
            declared.value = var.value
            return
        if self.parent:
            self.parent.set(name, var)
            return
        raise Exception(f"[Semantic] Variável '{name}' não declarada")

    def get(self, name: str) -> Variable:
        if name in self.table:
            return self.table[name]
        if self.parent:
            return self.parent.get(name)
        raise Exception(f"[Semantic] Variável '{name}' não definida")

class ReturnException(Exception):
    def __init__(self, var: Variable):
        super().__init__("return")
        self.value = var

class Node:
    id: int = 0
    def __init__(self, value, children):
        self.value: str | int = value
        self.children: list['Node'] = children
        self.id = Node.newId()
    def evaluate(self, st):
        pass
    def generate(self, st: SymbolTable):
        pass
    @staticmethod
    def newId():
        Node.id += 1
        return Node.id

class Code:
    instructions = []
    def append(code: str) -> None:
        Code.instructions.append(code)
    def dump(filename: str) -> None:
        header = """section .data
format_out: db "%d", 10, 0
format_in:  db "%d", 0
scan_int:   dd 0

section .text
extern printf
extern scanf
global _start

_start:
push ebp
mov  ebp, esp

; aqui começa o codigo gerado:
"""
        footer = """
; aqui termina o código gerado
mov esp, ebp
pop ebp
mov eax, 1
xor ebx, ebx
int 0x80
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            if Code.instructions:
                f.write("\n".join(Code.instructions))
                f.write("\n")
            f.write(footer)

class IntVal(Node):
    def __init__(self, value, children=[]): super().__init__(value, children)
    def evaluate(self, st):
        return Variable(self.value, "int")
    def generate(self, st):
        Code.append(f"mov eax, {self.value}")

class BoolVal(Node):
    def __init__(self, value, children=[]): super().__init__(value, children)
    def evaluate(self, st):
        return Variable(self.value, "bool")
    def generate(self, st):
        Code.append(f"mov eax, {1 if self.value else 0}")

class StringVal(Node):
    def __init__(self, value, children=[]): super().__init__(value, children)
    def evaluate(self, st):
        return Variable(self.value, "string")

class UnOp(Node):
    def evaluate(self, st):
        v = self.children[0].evaluate(st)
        if self.value == 'plus':
            if v.type != "int": raise Exception("[Semantic] Unário + exige int")
            return Variable(+v.value, "int")
        elif self.value == 'minus':
            if v.type != "int": raise Exception("[Semantic] Unário - exige int")
            return Variable(-v.value, "int")
        elif self.value == "not":
            if v.type != "bool": raise Exception("[Semantic] not exige bool")
            return Variable(not v.value, "bool")
        else:
            raise Exception(f"[Semantic] Operador unário inválido: {self.value}")
    def generate(self, st):
        self.children[0].generate(st)
        if self.value == 'plus':
            pass
        elif self.value == 'minus':
            Code.append("neg eax")
        elif self.value == "not":
            Code.append("not eax")

class BinOp(Node):
    def evaluate(self, st):
        a = self.children[0].evaluate(st)
        b = self.children[1].evaluate(st)
        op = self.value
        if op == 'plus':
            if a.type == "string" or b.type == "string":
                def coerce_to_str(v: Variable) -> str:
                    if v.type == "string": return v.value
                    if v.type == "int":    return str(v.value)
                    if v.type == "bool":   return "true" if v.value else "false"
                return Variable(coerce_to_str(a) + coerce_to_str(b), "string")
            if a.type == "int" and b.type == "int":
                return Variable(a.value + b.value, "int")
            raise Exception("[Semantic] Tipos incompatíveis para +")
        if op == 'minus':
            if a.type != "int" or b.type != "int": raise Exception("[Semantic] - exige ints")
            return Variable(a.value - b.value, "int")
        if op == 'mult':
            if a.type != "int" or b.type != "int": raise Exception("[Semantic] * exige ints")
            return Variable(a.value * b.value, "int")
        if op == 'div':
            if a.type != "int" or b.type != "int": raise Exception("[Semantic] // exige ints")
            if b.value == 0: raise Exception("[Semantic] Divisão por zero")
            return Variable(a.value // b.value, "int")
        if op == 'and':
            if a.type != "bool" or b.type != "bool": raise Exception("[Semantic] and exige bools")
            return Variable(a.value and b.value, "bool")
        if op == "or":
            if a.type != "bool" or b.type != "bool": raise Exception("[Semantic] or exige bools")
            return Variable(a.value or b.value, "bool")
        if op in ("gt", "lt"):
            if a.type == "int" and b.type == "int":
                return Variable(a.value > b.value, "bool") if op == "gt" else Variable(a.value < b.value, "bool")
            if a.type == "string" and b.type == "string":
                return Variable(a.value > b.value, "bool") if op == "gt" else Variable(a.value < b.value, "bool")
            raise Exception(f"[Semantic] {'>' if op=='gt' else '<'} exige tipos iguais (int ou string)")
        if op == "equals":
            if a.type != b.type: raise Exception("[Semantic] == exige tipos iguais")
            return Variable(a.value == b.value, "bool")
        raise Exception(f"[Semantic] Operador binário não suportado: {op}")
    def generate(self, st):
        self.children[1].generate(st)
        Code.append("push eax")
        self.children[0].generate(st)
        Code.append("pop ecx")
        if self.value == "plus":
            Code.append("add eax, ecx")
        elif self.value == "minus":
            Code.append("sub eax, ecx")
        elif self.value == "mult":
            Code.append("imul ecx")
        elif self.value == "div":
            Code.append("cdq")
            Code.append("idiv ecx")
        elif self.value == "equals":
            Code.append("cmp eax, ecx")
            Code.append("mov ecx, 1")
            Code.append("mov eax, 0")
            Code.append("cmove eax, ecx")
        elif self.value == "and":
            Code.append("test eax, eax")
            Code.append("setne al")
            Code.append("movzx eax, al")
            Code.append("test ecx, ecx")
            Code.append("setne cl")
            Code.append("movzx ecx, cl")
            Code.append("and eax, ecx")
        elif self.value == "or":
            Code.append("test eax, eax")
            Code.append("setne al")
            Code.append("movzx eax, al")
            Code.append("test ecx, ecx")
            Code.append("setne cl")
            Code.append("movzx ecx, cl")
            Code.append("or eax, ecx")
        elif self.value == "lt":
            Code.append("cmp eax, ecx")
            Code.append("mov eax, 0")
            Code.append("mov ecx, 1")
            Code.append("cmovl eax, ecx")
        elif self.value == "gt":
            Code.append("cmp eax, ecx")
            Code.append("mov eax, 0")
            Code.append("mov ecx, 1")
            Code.append("cmovg eax, ecx")

class VarDec(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        if var_type is None:
            raise Exception("[Semantic]")
        st.create_variable(var_name, var_type)
        if len(self.children) > 1:
            filho_direita = self.children[1].evaluate(st)
            if filho_direita.type != var_type:
                raise Exception("[Semantic] Valor de atribuição não bate com o tipo")
            st.set(var_name, Variable(filho_direita.value, var_type))
    def generate(self, st):
        var_name = self.children[0].value
        var_type = self.value or "int"
        if var_name in st.table:
            shift = st.table[var_name].shift
        else:
            shift = st.create_variable(var_name, var_type)
        Code.append("sub esp, 4")
        if len(self.children) > 1 and self.children[1]:
            self.children[1].generate(st)
            Code.append(f"mov [ebp - {shift}], eax")

class NoOp():
    def evaluate(self, st):
        return None
    def generate(self, st):
        pass

class Identifier(Node):
    def __init__(self, value, children=[]): super().__init__(value, children)
    def evaluate(self, st):
        var = st.get(self.value)
        if not var.func and var.value is None:
            raise Exception(f"[Semantic] Variável '{self.value}' declarada mas não inicializada")
        return var
    def generate(self, st):
        shift = st.get(self.value).shift
        Code.append(f"mov eax, dword [ebp - {shift}]")

class Print(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        v = self.children[0].evaluate(st)
        if v.type == "bool":
            print("true" if v.value else "false")
        else:
            print(v.value)
    def generate(self, st):
        self.children[0].generate(st)
        Code.append("push eax")
        Code.append("push format_out")
        Code.append("call printf")
        Code.append("add esp, 8")

class Assingment(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        var_name = self.children[0].value
        filho_direita = self.children[1].evaluate(st)
        declared = st.get(var_name)
        if filho_direita.type != declared.type:
            raise Exception("[Semantic] Atribuição de tipo inválido")
        st.set(var_name, Variable(filho_direita.value, declared.type))
    def generate(self, st):
        var_name = self.children[0].value
        self.children[1].generate(st)
        shift = st.get(var_name).shift
        Code.append(f"mov [ebp - {shift}], eax")

class Block(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        for child in self.children:
            if isinstance(child, Block):
                child_st = SymbolTable(st)
                try:
                    ret = child.evaluate(child_st)
                    if isinstance(ret, Variable):
                        return ret
                except ReturnException as rexc:
                    raise
            else:
                try:
                    res = child.evaluate(st)
                    if isinstance(res, Variable):
                        return res
                except ReturnException as rexc:
                    return rexc.value
        return None
    def generate(self, st):
        for child in self.children:
            child.generate(st)

class If(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        cond = self.children[0].evaluate(st)
        if cond.type != "bool":
            raise Exception("[Semantic] Condição do if deve ser bool")
        try:
            if cond.value:
                return self.children[1].evaluate(st)
            else:
                if len(self.children) > 2 and self.children[2]:
                    return self.children[2].evaluate(st)
        except ReturnException:
            raise
        return None
    def generate(self, st):
        uid = self.id
        self.children[0].generate(st)
        Code.append("cmp eax, 1")
        has_else = (len(self.children) > 2 and self.children[2])
        if has_else:
            Code.append(f"je then_{uid}")
            self.children[2].generate(st)
            Code.append(f"jmp exit_{uid}")
            Code.append(f"then_{uid}:")
            self.children[1].generate(st)
            Code.append(f"exit_{uid}:")
        else:
            Code.append(f"jne exit_{uid}")
            self.children[1].generate(st)
            Code.append(f"exit_{uid}:")

class For(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        while True:
            cond = self.children[0].evaluate(st)
            if cond.type != "bool":
                raise Exception("[Semantic] Condição do for deve ser bool")
            if not cond.value:
                break
            try:
                self.children[1].evaluate(st)
            except ReturnException:
                raise
        return None
    def generate(self, st):
        Code.append(f"loop_{self.id}:")
        self.children[0].generate(st)
        Code.append("cmp eax, 0")
        Code.append(f"je exit_{self.id}")
        self.children[1].generate(st)
        Code.append(f"jmp loop_{self.id}")
        Code.append(f"exit_{self.id}:")

class Read(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        entrada = int(input())
        return Variable(entrada, "int")
    def generate(self, st):
        Code.append("push scan_int")
        Code.append("push format_in")
        Code.append("call scanf")
        Code.append("add esp, 8")
        Code.append("mov eax, dword [scan_int]")

class FuncDec(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        nome = self.children[0].value
        st.create_function(nome, self, self.value)

class FuncCall(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        func_var = st.get(self.value)
        if not func_var or not func_var.func:
            raise Exception("[Semantic] Chamada de função inválida")
        func_node: FuncDec = func_var.value
        declared_params = func_node.children[1:-1]
        if len(self.children) != len(declared_params):
            raise Exception("[Semantic] Número de argumentos inválido na chamada de função")
        call_st = SymbolTable(st)
        for idx, p in enumerate(declared_params):
            ident = p.children[0].value
            ptype = p.value
            call_st.create_variable(ident, ptype)
            arg_val = self.children[idx].evaluate(st)
            if arg_val.type != ptype:
                raise Exception(f"[Semantic] Tipo de argumento incompatível em '{self.value}' para '{ident}'")
            call_st.set(ident, arg_val)
        body = func_node.children[-1]
        try:
            ret = body.evaluate(call_st)
            if func_node.value == "void":
                return None if ret is None else (_ for _ in ()).throw(Exception("[Semantic] Função void não deve retornar valor"))
            if isinstance(ret, Variable):
                if ret.type != func_node.value:
                    raise Exception(f"[Semantic] Tipo de retorno inválido: esperado {func_node.value}, recebeu {ret.type}")
                return ret
            raise Exception(f"[Semantic] Função '{self.value}' sem retorno (esperado {func_node.value})")
        except ReturnException as rexc:
            if func_node.value == "void":
                raise Exception("[Semantic] Função void não deve retornar valor")
            if rexc.value.type != func_node.value:
                raise Exception(f"[Semantic] Tipo de retorno inválido: esperado {func_node.value}, recebeu {rexc.value.type}")
            return rexc.value

class Return(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st):
        val = self.children[0].evaluate(st)
        raise ReturnException(val)

class Lexer:
    def __init__(self, source):
        self.source: str = source
        self.position: int = 0
        self.next: Token = None

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position] in (" ", "\t", "\r"):
            self.position += 1
        if self.position >= len(self.source):
            self.next = Token("EOF", None)
            return
        ch = self.source[self.position]
        if ch == '"':
            self.position += 1
            buf = []
            while self.position < len(self.source) and self.source[self.position] != '"':
                buf.append(self.source[self.position])
                self.position += 1
            if self.position >= len(self.source):
                raise Exception("[Lexer] String não terminada")
            self.position += 1
            self.next = Token("str", "".join(buf))
            return
        if ch == "+":
            self.next = Token("plus", "+"); self.position += 1; return
        elif ch == "-":
            self.next = Token("minus", "-"); self.position += 1; return
        elif ch == "*":
            self.next = Token("mult", "*"); self.position += 1; return
        elif ch == "/":
            self.next = Token("div", "/"); self.position += 1; return
        elif ch == "(":
            self.next = Token("open_par", "("); self.position += 1; return
        elif ch == ")":
            self.next = Token("close_par", ")"); self.position += 1; return
        elif ch == "{":
            self.next = Token("open_bra", "{"); self.position += 1; return
        elif ch == "}":
            self.next = Token("close_bra", "}"); self.position += 1; return
        elif ch == "=":
            self.position += 1
            if self.position < len(self.source) and self.source[self.position] == "=":
                self.next = Token("equals", "==")
                self.position += 1
            else:
                self.next = Token("assign", "=")
            return
        elif ch == ",":
            self.next = Token("comma", ","); self.position += 1; return
        elif ch == "!":
            self.next = Token("not", "!"); self.position += 1; return
        elif ch == "&":
            self.position += 1
            if self.position < len(self.source) and self.source[self.position] == "&":
                self.next = Token("and", "&&"); self.position += 1
            else:
                raise Exception("[Lexer] Caractere: & invalido")
            return
        elif ch == "|":
            self.position += 1
            if self.position < len(self.source) and self.source[self.position] == "|":
                self.next = Token("or", "||"); self.position += 1
            else:
                raise Exception("[Lexer] Caractere: | inválido")
            return
        elif ch == "<":
            self.next = Token("lt", "<"); self.position += 1; return
        elif ch == ">":
            self.next = Token("gt", ">"); self.position += 1; return
        elif ch == "\n":
            self.next = Token("end", "\n"); self.position += 1; return
        elif ch.isalpha():
            identifier = ""
            while (self.position < len(self.source) and
                   (self.source[self.position].isalnum() or self.source[self.position] == "_")):
                identifier += self.source[self.position]
                self.position += 1
            if identifier in ("string", "int", "bool"):
                self.next = Token("type", identifier)
            elif identifier == "true":
                self.next = Token("bool", True)
            elif identifier == "false":
                self.next = Token("bool", False)
            elif identifier in ("Println", "for", "if", "else", "Scanln", "var", "func", "return"):
                self.next = Token(identifier.lower(), identifier)
            else:
                self.next = Token("iden", identifier)
            return
        elif ch.isdigit():
            temp = ""
            while self.position < len(self.source) and self.source[self.position].isdigit():
                temp += self.source[self.position]
                self.position += 1
            self.next = Token("int", int(temp))
            return
        else:
            raise Exception(f"[Lexer] Invalid token {ch}")

class Parser:
    lex: 'Lexer'
    @staticmethod
    def _is_start_of_expr(kind: str) -> bool:
        return kind in ("int","iden","str","bool","open_par","plus","minus","not","scanln","scan","close_par","close_bra")
    def parseProgram() -> Node:
        block = Block(None, [])
        while Parser.lex.next.kind == "end":
            Parser.lex.select_next()
        while Parser.lex.next.kind in ("func", "var"):
            if Parser.lex.next.kind == "func":
                block.children.append(Parser.parseFuncDec())
            elif Parser.lex.next.kind == "var":
                block.children.append(Parser.parseVarDec())
            while Parser.lex.next.kind == "end":
                Parser.lex.select_next()
        block.children.append(FuncCall("main", []))
        while Parser.lex.next.kind == "end":
            Parser.lex.select_next()
        return block
    def parseBlock() -> Node:
        if Parser.lex.next.kind != "open_bra":
            raise Exception("[Parser] Bloco esperado: '{' nao encontrado")
        Parser.lex.select_next()
        if Parser.lex.next.kind == "close_bra":
            raise Exception("[Parser] Unexpected token CLOSE_BRA")
        block = Block(None, [])
        while True:
            if Parser.lex.next.kind == "EOF":
                raise Exception("[Parser] Unexpected token EOF (expected CLOSE_BRA)")
            if Parser.lex.next.kind == "close_bra":
                break
            block.children.append(Parser.parseStatement())
        Parser.lex.select_next()
        return block
    def parseStatement() -> Node:
        node = NoOp()
        if Parser.lex.next.kind == "close_bra":
            raise Exception("[Parser] Unexpected token CLOSE_BRA (expected EOF)")
        if Parser.lex.next.kind == "print" or Parser.lex.next.kind == "println":
            Parser.lex.select_next()
            if Parser.lex.next.kind != "open_par":
                kind = Parser.lex.next.kind
                name = name_map.get(kind, kind.upper())
                raise Exception(f"[Parser] Unexpected token {name} (expected OPEN_PAR)")
            Parser.lex.select_next()
            resp = Parser.parseBoolExpression()
            if Parser.lex.next.kind != "close_par":
                kind = Parser.lex.next.kind
                name = name_map.get(kind, kind.upper())
                raise Exception(f"[Parser] Unexpected token {name} (expected CLOSE_PAR)")
            Parser.lex.select_next()
            node = Print(None, [resp])
        if Parser.lex.next.kind == "open_bra":
            node = Parser.parseBlock()
            if Parser.lex.next.kind == "end":
                Parser.lex.select_next()
            return node
        if Parser.lex.next.kind == "var":
            return Parser.parseVarDec()
        elif Parser.lex.next.kind == "iden":
            identifier = Identifier(Parser.lex.next.value, [])
            Parser.lex.select_next()
            if Parser.lex.next.kind == "assign":
                Parser.lex.select_next()
                raiz = Parser.parseBoolExpression()
                node = Assingment("assign", [identifier, raiz])
            elif Parser.lex.next.kind == "open_par":
                raiz = FuncCall(identifier.value, [])
                Parser.lex.select_next()
                while Parser.lex.next.kind != "close_par":
                    raiz.children.append(Parser.parseBoolExpression())
                    if Parser.lex.next.kind == "comma":
                        Parser.lex.select_next()
                Parser.lex.select_next()
                node = raiz
        elif Parser.lex.next.kind == "return":
            Parser.lex.select_next()
            raiz = Parser.parseBoolExpression()
            node = Return(None, [raiz])
        if Parser.lex.next.kind == "for":
            Parser.lex.select_next()
            raiz = Parser.parseBoolExpression()
            if Parser.lex.next.kind != "open_bra":
                raise Exception("[Parser] Missing OPEN_BRA")
            Parser.lex.select_next()
            if Parser.lex.next.kind == "close_bra":
                raise Exception("[Parser] Unexpected token CLOSE_BRA")
            buffer = Block(None, [])
            while True:
                if Parser.lex.next.kind == "EOF":
                    raise Exception("[Parser] Unexpected token EOF")
                if Parser.lex.next.kind == "close_bra":
                    break
                buffer.children.append(Parser.parseStatement())
            Parser.lex.select_next()
            node = For(None, [raiz, buffer])
        if Parser.lex.next.kind == "if":
            Parser.lex.select_next()
            raiz = Parser.parseBoolExpression()
            if Parser.lex.next.kind != "open_bra":
                raise Exception("[Parser] Missing OPEN_BRA")
            Parser.lex.select_next()
            if Parser.lex.next.kind == "close_bra":
                raise Exception("[Parser] Unexpected token CLOSE_BRA")
            buffer = Block(None, [])
            while True:
                if Parser.lex.next.kind == "EOF":
                    raise Exception("[Parser] Missing CLOSE_BRA")
                if Parser.lex.next.kind == "close_bra":
                    break
                buffer.children.append(Parser.parseStatement())
            Parser.lex.select_next()
            node = If(None, [raiz, buffer])
            if Parser.lex.next.kind == "else":
                Parser.lex.select_next()
                if Parser.lex.next.kind != "open_bra":
                    raise Exception("[Parser] Unexpected token EOF")
                Parser.lex.select_next()
                if Parser.lex.next.kind == "close_bra":
                    raise Exception("[Parser] Unexpected token CLOSE_BRA")
                buffer2 = Block(None, [])
                while True:
                    if Parser.lex.next.kind == "EOF":
                        raise Exception("[Parser] Missing CLOSE_BRA")
                    if Parser.lex.next.kind == "close_bra":
                        break
                    buffer2.children.append(Parser.parseStatement())
                Parser.lex.select_next()
                node = If(None, [raiz, buffer, buffer2])
        if Parser.lex.next.kind == "end":
            Parser.lex.select_next()
            return node
        elif Parser.lex.next.kind in ("EOF", "close_bra"):
            return node
        else:
            kind = Parser.lex.next.kind
            name = name_map.get(kind, kind.upper())
            raise Exception(f"[Parser] Unexpected token {name}")
    def parseVarDec() -> Node:
        Parser.lex.select_next()
        if Parser.lex.next.kind != "iden":
            raise Exception("[Parser] Unexpected token (expected IDEN)")
        identifier = Identifier(Parser.lex.next.value, [])
        Parser.lex.select_next()
        if Parser.lex.next.kind != "type":
            raise Exception("[Parser] TYPE not found")
        var_type = Parser.lex.next.value
        Parser.lex.select_next()
        if Parser.lex.next.kind == "assign":
            Parser.lex.select_next()
            expr = Parser.parseBoolExpression()
            if Parser._is_start_of_expr(Parser.lex.next.kind):
                bad = name_map.get(Parser.lex.next.kind, Parser.lex.next.kind.upper())
                raise Exception(f"[Parser] Unexpected token {bad} after expression")
            return VarDec(var_type, [identifier, expr])
        return VarDec(var_type, [identifier])
    def parseFuncDec() -> Node:
        raiz = FuncDec(None, [])
        if Parser.lex.next.kind != "func":
            raise Exception("[Parser] Unexpected token")
        Parser.lex.select_next()
        if Parser.lex.next.kind != "iden":
            raise Exception("[Parser] Unexpected token")
        raiz.children.append(Identifier(Parser.lex.next.value, []))
        Parser.lex.select_next()
        if Parser.lex.next.kind != "open_par":
            raise Exception("[Parser] Unexpected token")
        Parser.lex.select_next()
        params = []
        if Parser.lex.next.kind != "close_par":
            while True:
                if Parser.lex.next.kind != "iden":
                    raise Exception("[Parser] Expected parameter name (IDEN)")
                ident = Identifier(Parser.lex.next.value, [])
                Parser.lex.select_next()
                if Parser.lex.next.kind != "type":
                    raise Exception("[Parser] Expected parameter type after name")
                param_type = Parser.lex.next.value
                Parser.lex.select_next()
                params.append(VarDec(param_type, [ident]))
                if Parser.lex.next.kind == "comma":
                    Parser.lex.select_next()
                    continue
                break
        if Parser.lex.next.kind != "close_par":
            raise Exception("[Parser] Unexpected token")
        Parser.lex.select_next()
        if Parser.lex.next.kind == "type":
            raiz.value = Parser.lex.next.value
            Parser.lex.select_next()
        else:
            raiz.value = "void"
        for p in params:
            raiz.children.append(p)
        raiz.children.append(Parser.parseBlock())
        return raiz
    def parseBoolExpression() ->Node:
        raiz = Parser.parseBoolTerm()
        while Parser.lex.next.kind == "or":
            Parser.lex.select_next()
            buffer = Parser.parseBoolTerm()
            raiz = BinOp("or", [raiz, buffer])
        return raiz
    def parseBoolTerm() ->Node:
        raiz = Parser.parseRelExpression()
        while Parser.lex.next.kind == "and":
            Parser.lex.select_next()
            buffer = Parser.parseRelExpression()
            raiz = BinOp("and", [raiz, buffer])
        return raiz
    def parseRelExpression() -> Node:
        raiz = Parser.parseExpression()
        while Parser.lex.next.kind in ("equals", "gt", "lt"):
            op = Parser.lex.next.kind
            Parser.lex.select_next()
            buffer = Parser.parseExpression()
            raiz = BinOp(op, [raiz, buffer])
        return raiz
    def parseExpression() -> Node:
        raiz = Parser.parseTerm()
        while Parser.lex.next.kind in ("plus", "minus"):
            op = Parser.lex.next.kind
            Parser.lex.select_next()
            buffer = Parser.parseTerm()
            raiz = BinOp(op, [raiz, buffer])
        return raiz
    def parseTerm() -> Node:
        raiz = Parser.parseFactor()
        while Parser.lex.next.kind in ("mult", "div"):
            op = Parser.lex.next.kind
            Parser.lex.select_next()
            buffer = Parser.parseFactor()
            raiz = BinOp(op, [raiz, buffer])
        return raiz
    def parseFactor() -> Node:
        if Parser.lex.next.kind == "int":
            resp = IntVal(Parser.lex.next.value, [])
            Parser.lex.select_next()
            return resp
        elif Parser.lex.next.kind == "open_par":
            Parser.lex.select_next()
            resp = Parser.parseBoolExpression()
            if Parser.lex.next.kind != "close_par":
                raise Exception("[Parser] Missing CLOSE_PAR")
            Parser.lex.select_next()
            return resp
        elif Parser.lex.next.kind == "plus":
            Parser.lex.select_next()
            return UnOp("plus", [Parser.parseFactor()])
        elif Parser.lex.next.kind == "minus":
            Parser.lex.select_next()
            return UnOp("minus", [Parser.parseFactor()])
        elif Parser.lex.next.kind == "iden":
            name = Parser.lex.next.value
            Parser.lex.select_next()
            if Parser.lex.next.kind == "open_par":
                Parser.lex.select_next()
                args = []
                if Parser.lex.next.kind != "close_par":
                    args.append(Parser.parseBoolExpression())
                    while Parser.lex.next.kind == "comma":
                        Parser.lex.select_next()
                        args.append(Parser.parseBoolExpression())
                if Parser.lex.next.kind != "close_par":
                    raise Exception("[Parser] Missing CLOSE_PAR in function call")
                Parser.lex.select_next()
                return FuncCall(name, args)
            else:
                return Identifier(name, [])
        elif Parser.lex.next.kind == "not":
            Parser.lex.select_next()
            return UnOp("not", [Parser.parseFactor()])
        elif Parser.lex.next.kind in ("scanln", "scan"):
            Parser.lex.select_next()
            if Parser.lex.next.kind != "open_par":
                raise Exception("[Parser] Era esperado um parenteses de abertura")
            Parser.lex.select_next()
            if Parser.lex.next.kind != "close_par":
                raise Exception("[Parser] Era esperado um parenteses de fechamento")
            Parser.lex.select_next()
            return Read(None, [])
        elif Parser.lex.next.kind == "bool":
            resp = BoolVal(Parser.lex.next.value, [])
            Parser.lex.select_next()
            return resp
        elif Parser.lex.next.kind == "str":
            resp = StringVal(Parser.lex.next.value, [])
            Parser.lex.select_next()
            return resp
        else:
            kind = Parser.lex.next.kind
            name = name_map.get(kind, kind.upper())
            raise Exception(f"[Parser] Unexpected token {name}")
    def run(code: str) -> int:
        Parser.lex = Lexer(code)
        Parser.lex.select_next()
        resp = Parser.parseProgram()
        if Parser.lex.next.kind != "EOF":
            raise Exception("[Parser] Houve algum erro no consumo da entrada.")
        return resp

def main():
    if len(sys.argv) < 2:
        sys.exit("[Runner] Missing input filename")
    arquivo = sys.argv[1]
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        sys.exit(str(e))
    try:
        code = PrepPro.filter(code)
    except Exception as e:
        sys.exit(str(e))
    try:
        ast = Parser.run(code)
    except Exception as e:
        sys.exit(str(e))
    try:
        st = SymbolTable()
        ast.evaluate(st)
    except Exception as e:
        sys.exit(str(e))

if __name__ == "__main__":
    main()
