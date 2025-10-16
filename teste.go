// --- Arquivo de Teste: teste.go ---
// Escrito usando o subconjunto da linguagem Go que nosso compilador atual entende.

// 1. Testando declaração e impressão de todos os tipos
// A sintaxe 'var nome tipo = valor' é compatível com Go.
// Usamos 'Println' com 'P' maiúsculo, como definido no nosso Lexer, em vez de 'fmt.Println'.
Println("--- Teste de Variaveis ---")
var meu_numero int = 100
var meu_texto string = "Ola, Go!"
var e_verdade bool = true

Println(meu_numero)
Println(meu_texto)
Println(e_verdade)
Println("--------------------------")
Println("") // Linha em branco para separar

// 2. Testando estruturas de controle
// Usamos 'for' (mapeado para 'while' no seu código) e 'if/else'.
Println("--- Teste de Estruturas de Controle ---")
var a int = 20
a = a / 2
var b int = a + 5 // b deve ser 15

if (b > 10) {
  Println("O valor de 'b' e maior que 10")
} else {
  Println("O valor de 'b' nao e maior que 10")
}

var contador int = 3
for (contador > 0) { // No seu Lexer, 'for' vira um token 'WHILE'
  Println("Contagem regressiva...")
  contador = contador - 1
}
Println("-------------------------------------")
Println("")

// 3. Testando concatenação de string e operadores lógicos
Println("--- Teste de Novas Operacoes ---")
var s1 string = "Juntando"
var s2 string = " "
var s3 string = "strings!"
var frase string = s1 + s2 + s3 // Concatenação é igual em Go
Println(frase)

var cond1 bool = true
var cond2 bool = false
Println(cond1 && cond2) // false
Println(cond1 || cond2) // true
Println(!cond2)         // true
Println("----------------------------------")
Println("")


// 4. Testando a entrada de dados
Println("--- Teste de Entrada (Scanln) ---")
Println("Por favor, digite um numero inteiro:")
var entrada int = Scanln() // Função customizada do nosso subconjunto
entrada = entrada * 2
Println("O dobro do numero digitado e:")
Println(entrada)
Println("---------------------------------")