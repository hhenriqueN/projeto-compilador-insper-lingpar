import sys

class Token():

    def __init__(self, kind, value):

        self.kind = kind
        self.value = value


class Lexer():

    def __init__(self, source):

        self.source = source
        self.position = 0
        self.next = None

    def select_next(self):

    
        while self.position < len(self.source) and self.source[self.position] == " ":

            self.position += 1

        if self.position == len(self.source):

            self.next = Token('EOF', '')
            return self.next

        elif self.source[self.position] == "+":

            self.next = Token('PLUS', self.source[self.position])
            self.position += 1
            return self.next

        elif self.source[self.position] == "-":

            self.next = Token('MINUS', self.source[self.position])
            self.position += 1
            return self.next
        
        elif self.source[self.position] == "*":
            
            self.next = Token('MULT', self.source[self.position])
            self.position += 1
            return self.next
        
        elif self.source[self.position] == "/":
            
            self.next = Token('DIV', self.source[self.position])
            self.position += 1
            return self.next
        
        elif self.source[self.position] == "(":
            
            self.next = Token('OPEN_PAR', self.source[self.position])
            self.position += 1
            return self.next
        
        elif self.source[self.position] == ")":
            
            self.next = Token('CLOSE_PAR', self.source[self.position])
            self.position += 1
            return self.next
        
    
        elif self.source[self.position].isdigit():

            numero = ''

            while self.position < len(self.source) and self.source[self.position].isdigit():

                numero += self.source[self.position]
                self.position += 1
                
            numero = int(numero)
            self.next = Token('INT', numero)
            return self.next
        
        else:

            raise Exception(f"Caractere inválido: {self.source[self.position]}")



class Parser():

    
    @staticmethod
    def parse_expression(lex):
        
        resultado = Parser.parse_term(lex)

        while lex.next.kind in ("PLUS", "MINUS"):
            operador = lex.next.kind
            lex.select_next()
            rhs = Parser.parse_term(lex)
            if operador == "PLUS":
                resultado += rhs
            else:
                resultado -= rhs

        return resultado


        

    @staticmethod
    def parse_term(lex):
        
        resultado = Parser.parse_factor(lex)

        while lex.next.kind in ("MULT", "DIV"):
            operador = lex.next.kind
            lex.select_next()
            rhs = Parser.parse_factor(lex)
            if operador == "MULT":
                resultado *= rhs
            else:
                resultado //= rhs  

        return resultado
        

    
    
    @staticmethod
    def parse_factor(lex):
        
        
        if lex.next.kind == "INT":
            valor = lex.next.value
            lex.select_next()
            return valor

        elif lex.next.kind == "PLUS":
            lex.select_next()
            return Parser.parse_factor(lex)

        elif lex.next.kind == "MINUS":
            lex.select_next()
            return -Parser.parse_factor(lex)

        elif lex.next.kind == "OPEN_PAR":
            lex.select_next()
            valor = Parser.parse_expression(lex)
            if lex.next.kind != "CLOSE_PAR":
                raise Exception("Faltando fechar parêntese")
            lex.select_next()
            return valor

        else:
            raise Exception(f"Token inesperado: {lex.next.kind}")
        
        

    @staticmethod
    def run(source_code):

        lex = Lexer(source_code)

        lex.select_next()

        

        resultado = Parser.parse_expression(lex)

        if lex.next.kind != "EOF":
            raise Exception("Erro de sintaxe: tokens sobrando no fim da expressão")

        return resultado
    
    
    
    



def main():
    source_code = sys.stdin.read().strip()

    # Se não veio nada, tenta pelo input() (linha interativa)
    if not source_code:
        try:
            source_code = input().strip()
        except EOFError:
            source_code = ""

    # Se ainda estiver vazio, tenta argv
    if not source_code and len(sys.argv) > 1:
        # Junta todos os argumentos passados
        source_code = " ".join(sys.argv[1:]).strip()

    if not source_code:
        raise Exception("Nenhum código recebido!")

    resultado = Parser.run(source_code)
    print(resultado)
    
    


if __name__ == '__main__':

    main()
        

        