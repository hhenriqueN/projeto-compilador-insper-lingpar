def compilador(string):

    # chamando função para ignorar espaços
    string = limpa_string(string)

    operadores = ['+', '-']

    string_validada = valida_operacao(string)


    if not string_validada:
        raise Exception("A string não possui uma operação válida.")
    
    # caso válida, executar operação

    else:
    
        lista_numeros = []
        lista_operadores = []
        numero_atual = ''

        for caractere in string:
             
            
            if caractere not in operadores:
                 
                 # se entrou aqui é um número
                 numero_atual += caractere

            else:
                # se entrou aqui, é um operador
                lista_numeros.append(int(numero_atual))
                lista_operadores.append(caractere)

                numero_atual = ''

        # colocando o numero que sobrou da iteração
        if numero_atual:
            lista_numeros.append(int(numero_atual))
             


    resultado = executa_operacao(lista_numeros, lista_operadores)
    print(resultado)

    return resultado
                
                 
def valida_operacao(string):

    numeros = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    operadores = ['+', '-']

    contador_numeros = 0
    contador_operadores = 0

    # validando operaçao na string
    # percorrer a string como uma lista e verificar se possuo pelo menos dois números e um operador
    for caractere in string:

        if caractere in numeros:
            contador_numeros += 1

        if caractere in operadores:
            contador_operadores += 1

    if contador_numeros < 2 or contador_operadores == 0:

        return False
    
    return True


             
def executa_operacao(lista_numeros, lista_operadores):

    resultado_operacao = lista_numeros[0]

    for i in range(len(lista_operadores)):

        if lista_operadores[i] == "+":

            resultado_operacao += lista_numeros[i + 1]

        elif lista_operadores[i] == "-":

            resultado_operacao -= lista_numeros[i + 1]

    return resultado_operacao


def limpa_string(string):

    string_limpa = ''
    
    for i in range(len(string)):

        if string[i] != ' ':

            string_limpa += string[i]
            
    #print(string_limpa)
    return string_limpa


        



