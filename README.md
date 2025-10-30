# Calculadora Creativa de Integrales

Aplicación web estática que analiza una integral indefinida escrita por la persona usuaria, sugiere un método de integración apropiado y resuelve simbólicamente la integral introducida. Además, presenta un ejemplo muy similar explicado paso a paso con notación \(\LaTeX\), destacando las variables auxiliares (\(u\), \(du\), \(dv\), \(v\), \(\theta\)) según corresponda.

## Características
- Detección heurística de métodos: sustitución simple, integración por partes, sustitución trigonométrica y fracciones parciales.
- Ejemplos similares completamente desarrollados con explicaciones secuenciales.
- Resolución simbólica del integrando introducido utilizando [Nerdamer](https://nerdamer.com/) y presentación del resultado en \(\LaTeX\) con la constante \(+C\).
- Interfaz vistosa con paneles translúcidos y tipografía moderna.
- Teclado matemático en pantalla para introducir símbolos comunes como ∫, √, π, funciones trigonométricas y operadores.
- Compatibilidad con MathJax para renderizar las expresiones en \(\LaTeX\).

## Uso
1. Abre `index.html` en tu navegador.
2. Escribe una integral en el cuadro de texto o utiliza el teclado matemático integrado. Puedes indicar la variable de integración con el diferencial (por ejemplo, `dx`).
3. Observa el método sugerido, revisa el ejemplo guiado paso a paso y consulta la solución simbólica con la constante de integración \(+C\).

### Consejos de entrada

- Usa `x` como variable principal cuando sea posible. Si solo aparece otra variable (por ejemplo, `y`), la calculadora la detectará automáticamente.
- Especifica multiplicaciones explícitas (`*`) cuando el integrando pueda resultar ambiguo, por ejemplo `x * sin(x)` en lugar de `x sin(x)`.
- Si la librería simbólica no se carga (requiere conexión a internet para descargar Nerdamer desde la CDN), se mostrará un mensaje informativo.
