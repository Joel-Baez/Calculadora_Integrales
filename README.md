# Calculadora Creativa de Integrales

Aplicación web con backend en Python que analiza integrales indefinidas, sugiere el método de integración más adecuado y muestra un ejemplo muy similar con pasos detallados en \(\LaTeX\). El motor basado en [SymPy](https://www.sympy.org/) se centra en reconocer patrones y generar la guía didáctica, no en resolver exactamente la integral ingresada por la persona usuaria.

## Características principales

- **Motor de análisis en Python**: el servidor Flask utiliza SymPy para validar la expresión, detectar patrones e interpretar el integrando en \(\LaTeX\), sin exponer directamente la integral ingresada como resultado.
- **Detección heurística de métodos**: identifica sustitución simple, integración por partes, sustitución trigonométrica, fracciones parciales y casos con factores repetidos, mostrando un ejemplo semejante con anotaciones de \(u\), \(du\), \(dv\), \(v\), \(\theta\) y los retornos a la variable original.
- **Editor con vista previa en \(\LaTeX\)**: el área de captura personalizada acepta notación \(\LaTeX\) directamente, ofrece vista previa instantánea y se complementa con el teclado contextual de números, operadores, funciones, trigonometría y ayudas de método.
- **Ejemplo guiado en LaTeX**: cada método trae un problema representativo, su solución final y un cuadro con los datos clave (como \(u\), \(du\) o el ángulo \(\theta\)) para seguir el razonamiento paso a paso.
- **Pasos numerados con ecuaciones destacadas**: el ejemplo similar reproduce la secuencia didáctica con títulos, explicaciones y fórmulas renderizadas en \(\LaTeX\) para facilitar la comparación con la integral original.
- **Interfaz responsiva y vistosa**: paneles translúcidos, tipografía moderna y estados informativos que acompañan el flujo de análisis.
- **Teclado matemático segmentado**: botones agrupados por categorías (general, funciones, sustitución, fracciones parciales, etc.) que facilitan la captura del integrando desde la propia interfaz.

## Requisitos

- Python 3.10 o superior.
- Dependencias listadas en `requirements.txt` (Flask y SymPy).

Instala las dependencias con:

```bash
pip install -r requirements.txt
```

## Ejecución del servidor

1. Desde la raíz del proyecto, inicia el servidor Flask:

   ```bash
   flask --app app --debug run
   ```

   (También puedes ejecutar `python app.py` para un arranque simple con `debug=True`).

2. Abre `http://127.0.0.1:5000/` en tu navegador.
3. Proporciona la integral indefinida que quieras estudiar (integrando y variable principal). El sistema responderá con el método recomendado y un ejemplo similar completamente resuelto para guiarte.

## Consejos de entrada

- Usa el selector de variable para indicar la letra principal (por defecto `x`). La sanitización también acepta notación como `sen`, `tg`, `√`, `π`, `\sin`, `\frac{}`, etc., y la traduce a funciones de SymPy.
- Aprovecha el editor con vista previa en \(\LaTeX\): escribe directamente en el campo interactivo, utiliza el teclado integrado para insertar fracciones, raíces, trigonometría y símbolos auxiliares y verifica el resultado en la vista previa de la integral completa.
- Recuerda que solo se analizan integrales indefinidas: la respuesta consiste en la técnica sugerida y un ejemplo análogo resuelto, no en la antiderivada de tu entrada.
- El método sugerido puede diferir del que usarías manualmente, pero siempre viene acompañado de las sustituciones (\(u\), \(du\), \(dv\), \(v\), \(\theta\), etc.) y los pasos para replicarlo.

## Estructura del proyecto

- `app.py`: servidor Flask + lógica de análisis con SymPy.
- `index.html`: plantilla principal y estructura de la interfaz.
- `app.js`: lógica del teclado, validaciones y comunicación con el backend.
- `styles.css`: estilos y componentes visuales.
- `requirements.txt`: dependencias de Python.
