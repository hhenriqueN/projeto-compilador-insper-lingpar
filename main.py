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

        resultado = 0

        if lex.next.kind != 'INT':

            raise Exception(f"A operação não começa com um número. Primeiro caractere: {lex.next}")
        
        else:
            resultado += lex.next.value
            lex.select_next()

            while lex.next.kind == 'MINUS' or lex.next.kind == 'PLUS':

                operador = lex.next.kind
                lex.select_next()

                if lex.next.kind != 'INT':
                    raise Exception(f"Não é possivel realizar a operação pois o segundo valor não é um número. Valor: {self.lex.next.value}")
                
            
                else:

                    if operador == 'MINUS':
                        resultado -= lex.next.value

                    else:
                        resultado += lex.next.value

                lex.select_next()

        return resultado

        


        

    @staticmethod
    def run(source_code):

        lex = Lexer(source_code)

        lex.select_next()

        

        resultado = Parser.parse_expression(lex)

        if lex.next.kind != "EOF":
            raise Exception("Erro de sintaxe: tokens sobrando no fim da expressão")

        return resultado



def main():
    source_code = "10 - 3 + 2"
    resultado = Parser.run(source_code)
    print(resultado)


if __name__ == '__main__':

    main()
        

        