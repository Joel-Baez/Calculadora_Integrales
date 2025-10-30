# Calculadora Creativa de Integrales

Aplicación web con backend en Python que analiza integrales definidas o indefinidas, sugiere el método de integración más adecuado y muestra un ejemplo muy similar con pasos detallados en \(\LaTeX\). La antiderivada (o el valor de la integral definida) se calcula usando [SymPy](https://www.sympy.org/) y se presenta en notación matemática renderizada con MathJax.

## Características principales

- **Motor simbólico en Python**: el servidor Flask ejecuta SymPy para resolver integrales, evaluar límites definidos y generar expresiones en \(\LaTeX\).
- **Detección heurística de métodos**: identifica sustitución simple, integración por partes, sustitución trigonométrica y fracciones parciales, mostrando un ejemplo semejante con anotaciones de \(u\), \(du\), \(dv\), \(v\) y \(\theta\).
- **Análisis del integrando**: destaca características relevantes (polinomios, funciones racionales, raíces, logaritmos, etc.) e indica advertencias cuando aparecen variables adicionales o límites dependientes.
- **Interfaz responsiva y vistosa**: paneles translúcidos, tipografía moderna y modos de estado para guiar a la persona usuaria durante el cálculo.
- **Teclado matemático en pantalla**: inserta símbolos frecuentes (∫, √, π, sin, cos, tan, ln, exp, etc.) con gestión del cursor para facilitar la escritura.

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
3. Selecciona si deseas integrar de forma indefinida o definida, proporciona el integrando y (si corresponde) los límites. El resultado simbólico se generará junto con el método sugerido y el ejemplo guiado.

## Consejos de entrada

- Usa el selector de variable para indicar la letra principal (por defecto `x`). La sanitización también acepta notación como `sen`, `tg`, `√` o `π` y la traduce a funciones de SymPy.
- Escribe multiplicaciones explícitas (`*`) cuando el integrando pueda ser ambiguo (por ejemplo, `x*sin(x)` en lugar de `x sin(x)`).
- Para integrales definidas, introduce límites numéricos o simbólicos independientes de la variable de integración.
- El método sugerido puede diferir del utilizado internamente por SymPy, pero siempre se presenta un ejemplo muy similar con pasos claros para estudiar la técnica recomendada.

## Estructura del proyecto

- `app.py`: servidor Flask + lógica de análisis con SymPy.
- `index.html`: plantilla principal y estructura de la interfaz.
- `app.js`: lógica del teclado, validaciones y comunicación con el backend.
- `styles.css`: estilos y componentes visuales.
- `requirements.txt`: dependencias de Python.
