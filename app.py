import re
from typing import Dict, List

from flask import Flask, jsonify, request, send_from_directory
from sympy import (
    E,
    Symbol,
    acos,
    asin,
    atan,
    cos,
    cosh,
    cot,
    csc,
    diff,
    exp,
    latex,
    log,
    pi,
    sec,
    sin,
    sinh,
    sqrt,
    symbols,
    tan,
    tanh,
)
from sympy.core.function import AppliedUndef
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    TokenError,
    function_exponentiation,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

app = Flask(__name__, static_url_path='', static_folder='.')

TRANSFORMATIONS = (
    standard_transformations
    + (implicit_multiplication_application, function_exponentiation)
)

ALLOWED_FUNCTIONS = {
    'sin': sin,
    'cos': cos,
    'tan': tan,
    'asin': asin,
    'acos': acos,
    'atan': atan,
    'sinh': sinh,
    'cosh': cosh,
    'tanh': tanh,
    'cot': cot,
    'sec': sec,
    'csc': csc,
    'exp': exp,
    'log': log,
    'ln': log,
    'sqrt': sqrt,
    'E': E,
    'pi': pi,
}

METHOD_DETAILS: Dict[str, Dict[str, object]] = {
    'substitution': {
        'title': 'Sustitución simple',
        'badge': 'u-substitución',
        'summary': (
            'Una función compuesta $f(g(x))$ cuya derivada $g\'(x)$ aparece multiplicando '
            'permite introducir $u = g(x)$ para integrar en una sola variable auxiliar.'
        ),
        'example_integral': r'\int (3x^2 + 1)\cos(x^3 + x)\,dx',
        'example_solution': r'\sin(x^3 + x) + C',
        'setup': [
            {'label': '$u$', 'value': 'x^3 + x'},
            {'label': '$du$', 'value': '(3x^2 + 1)\\,dx'},
        ],
        'steps': [
            r'Identifica $u = x^3 + x$ porque su diferencial $du = (3x^2 + 1)\,dx$ aparece completo.',
            r'Reemplaza el integrando por $\int \cos(u)\,du$ y calcula la antiderivada $\sin(u) + C$.',
            r'Retorna a la variable original sustituyendo $u$ por $x^3 + x$.'
        ],
    },
    'parts': {
        'title': 'Integración por partes',
        'badge': '$u$ · $dv$',
        'summary': (
            'Cuando el integrando es un producto, conviene derivar la parte que se simplifica '
            'y antiderivar la que mantiene una forma manejable.'
        ),
        'example_integral': r'\int x e^x\,dx',
        'example_solution': r'x e^x - e^x + C',
        'setup': [
            {'label': '$u$', 'value': 'x'},
            {'label': '$du$', 'value': 'dx'},
            {'label': '$dv$', 'value': 'e^x\\,dx'},
            {'label': '$v$', 'value': 'e^x'},
        ],
        'steps': [
            r'Aplica $\int u\,dv = uv - \int v\,du$ con las elecciones indicadas.',
            r'Calcula $uv = x e^x$ y $\int v\,du = \int e^x\,dx = e^x$.',
            r'Resta ambos términos para obtener $x e^x - e^x + C$.'
        ],
    },
    'trig': {
        'title': 'Sustitución trigonométrica',
        'badge': '$\\theta$-sustitución',
        'summary': (
            'Las raíces de la forma $\\sqrt{a^2 - x^2}$, $\\sqrt{a^2 + x^2}$ o '
            '$\\sqrt{x^2 - a^2}$ sugieren introducir un ángulo $\\theta$ para aprovechar identidades trigonométricas.'
        ),
        'example_integral': r'\int \frac{dx}{\sqrt{1 - x^2}}',
        'example_solution': r'\arcsin(x) + C',
        'setup': [
            {'label': '$x$', 'value': '\\sin\\theta'},
            {'label': '$dx$', 'value': '\\cos\\theta\\,d\\theta'},
            {'label': '$\\theta$', 'value': '\\arcsin(x)'},
        ],
        'steps': [
            r'Sustituye $x = \sin\\theta$ para transformar la raíz en $\\sqrt{1 - \sin^2\\theta} = \cos\\theta$.',
            r'Reemplaza $dx$ por $\cos\\theta\,d\\theta$ y simplifica la integral a $\int d\\theta$.',
            r'Integra para obtener $\\theta + C$ y regresa a términos de $x$ mediante $\\theta = \arcsin(x)$.'
        ],
    },
    'partial_fractions': {
        'title': 'Fracciones parciales',
        'badge': 'descomposición',
        'summary': (
            'Un cociente de polinomios factorizable se puede expresar como suma de fracciones '
            'más simples cuya integración es directa.'
        ),
        'example_integral': r'\int \frac{2x + 3}{x^2 + 3x}\,dx',
        'example_solution': r'\ln|x| + \ln|x + 3| + C',
        'setup': [
            {
                'label': 'Descomposición',
                'value': r'\frac{2x + 3}{x(x + 3)} = \frac{1}{x} + \frac{1}{x + 3}'
            }
        ],
        'steps': [
            r'Factoriza el denominador $x^2 + 3x = x(x + 3)$.',
            r'Descompón en fracciones parciales y obtén coeficientes unitarios.',
            r'Integra cada término para llegar a $\ln|x| + \ln|x + 3| + C$.'
        ],
    },
    'default': {
        'title': 'Exploración general',
        'badge': 'observación',
        'summary': (
            'No se detectó un patrón dominante. Simplifica el integrando, separa en sumas '
            'o intenta sustituciones básicas para avanzar.'
        ),
        'example_integral': r'\int (x^2 + 1)\,dx',
        'example_solution': r'\tfrac{x^3}{3} + x + C',
        'steps': [
            r'Divide la integral en términos elementales y aplica reglas de potencia.',
            r'Comprueba si una sustitución sencilla reduce aún más la expresión.'
        ],
    },
}


def sanitize_expression(expression: str, variable: str) -> str:
    expr = expression or ''
    expr = expr.replace('∫', '')
    expr = re.sub(rf'd{re.escape(variable)}\b', '', expr, flags=re.IGNORECASE)
    expr = re.sub(r'd[a-zA-Z]\b', '', expr)
    replacements = [
        ('^', '**', False),
        ('√', 'sqrt', False),
        ('π', 'pi', False),
        ('sen', 'sin', True),
        ('tg', 'tan', True),
        ('ctg', 'cot', True),
        ('ln', 'log', True),
    ]
    for pattern, replacement, is_alpha in replacements:
        if is_alpha:
            expr = re.sub(pattern, replacement, expr, flags=re.IGNORECASE)
        else:
            expr = expr.replace(pattern, replacement)
    expr = re.sub(r'\\int', '', expr, flags=re.IGNORECASE)
    expr = expr.replace('\\,', '').replace('\\!', '')
    expr = re.sub(r'\\left|\\right', '', expr)
    expr = expr.replace('{', '(').replace('}', ')')
    expr = re.sub(r'\s+', '', expr)
    return expr


def parse_expression(expression: str, variable: str):
    local_dict = dict(ALLOWED_FUNCTIONS)
    local_dict[variable] = Symbol(variable)
    try:
        parsed = parse_expr(
            expression,
            local_dict=local_dict,
            transformations=TRANSFORMATIONS,
            evaluate=True,
        )
    except (SympifyError, TokenError) as exc:
        raise ValueError(f'No se pudo interpretar el integrando: {exc}') from exc
    if parsed.has(AppliedUndef):
        raise ValueError('Se detectaron funciones no soportadas.')
    return parsed


def describe_features(expr, var: Symbol) -> List[str]:
    features: List[str] = []
    if expr.is_polynomial(var):
        features.append('Polinomio en la variable principal.')
    if expr.is_rational_function(var) and not expr.is_polynomial(var):
        features.append('Cociente de polinomios: candidato a fracciones parciales.')
    if expr.has(log):
        features.append('Aparecen logaritmos naturales en el integrando.')
    if expr.has(exp):
        features.append('Incluye exponenciales $e^{x}$ u $\exp(x)$.')
    if expr.has(sin) or expr.has(cos) or expr.has(tan) or expr.has(cot) or expr.has(sec) or expr.has(csc):
        features.append('Contiene funciones trigonométricas.')
    if expr.has(sqrt):
        features.append('Incluye raíces cuadradas que podrían simplificarse con sustitución trigonométrica.')
    if expr.has(var) and expr.is_Mul:
        features.append('Producto de factores con la variable principal.')
    return features


def detect_method(expr, var: Symbol) -> str:
    if expr.is_rational_function(var) and not expr.is_polynomial(var):
        return 'partial_fractions'

    if expr.has(sqrt):
        for radicand in expr.atoms(sqrt):
            inner = radicand.args[0]
            if inner.is_polynomial(var) and inner.as_poly(var).degree() == 2:
                return 'trig'

    if expr.is_Mul:
        polynomial_part = any(f.as_poly(var) is not None for f in expr.args if f.has(var))
        transcendental_part = any(
            f.has(exp, log, sin, cos, tan, cot, sec, csc, sinh, cosh, tanh)
            for f in expr.args
        )
        if polynomial_part and transcendental_part:
            return 'parts'

    if expr.has(sin, cos, tan, cot, sec, csc, exp, log, sinh, cosh, tanh):
        derivatives = [
            diff(arg, var)
            for arg in expr.atoms(exp, log, sin, cos, tan, cot, sec, csc, sinh, cosh, tanh)
        ]
        if any(expr.has(der) for der in derivatives):
            return 'substitution'

    return 'substitution' if expr.has(exp, log, sin, cos, tan, cot, sec, csc, sinh, cosh, tanh) else 'default'


def integral_to_latex(expr) -> str:
    return latex(expr)


@app.route('/')
def root():
    return send_from_directory('.', 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    payload = request.get_json(silent=True) or {}
    expression = payload.get('expression', '')
    variable_name = payload.get('variable', 'x')
    variable_name = re.sub(r'[^a-zA-Z]', '', variable_name) or 'x'

    sanitized = sanitize_expression(expression, variable_name)
    if not sanitized:
        return jsonify({'status': 'error', 'error': 'No se recibió ningún integrando.'}), 400

    try:
        expr = parse_expression(sanitized, variable_name)
    except ValueError as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 400

    var_symbol = symbols(variable_name)
    features = describe_features(expr, var_symbol)
    method_key = detect_method(expr, var_symbol)
    method = METHOD_DETAILS.get(method_key, METHOD_DETAILS['default'])

    warnings: List[str] = []
    extra_symbols = [latex(sym) for sym in expr.free_symbols if sym != var_symbol]
    if extra_symbols:
        warnings.append(
            'Se detectaron otras variables en el integrando: '
            + ', '.join(extra_symbols)
        )

    analysis = {
        'sanitized_expression': integral_to_latex(expr),
        'variable': variable_name,
        'detected_features': features,
        'warnings': warnings,
        'method_key': method_key,
    }

    method_payload = dict(method)
    method_payload['key'] = method_key

    response = {
        'status': 'ok',
        'analysis': analysis,
        'method': method_payload,
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
