# Calculadora Creativa de Integrales

Aplicación web estática que analiza una integral indefinida escrita por la persona usuaria y sugiere un método de integración apropiado. En lugar de resolver la integral exacta introducida, muestra un ejemplo muy similar explicado paso a paso con notación \(\LaTeX\), destacando las variables auxiliares (\(u\), \(du\), \(dv\), \(v\), \(\theta\)) según corresponda.

## Características
- Detección heurística de métodos: sustitución simple, integración por partes, sustitución trigonométrica y fracciones parciales.
- Ejemplos similares completamente desarrollados con explicaciones secuenciales.
- Interfaz vistosa con paneles translúcidos y tipografía moderna.
- Teclado matemático en pantalla para introducir símbolos comunes como ∫, √, π, funciones trigonométricas y operadores.
- Compatibilidad con MathJax para renderizar las expresiones en \(\LaTeX\).

## Uso
1. Abre `index.html` en tu navegador.
2. Escribe una integral en el cuadro de texto o utiliza el teclado matemático integrado.
3. Observa el método sugerido y estudia el ejemplo guiado paso a paso.

> La herramienta está orientada al aprendizaje: la integral proporcionada por la persona usuaria **no se resuelve directamente**, sino que se presenta una integral similar que ejemplifica el método recomendado.
