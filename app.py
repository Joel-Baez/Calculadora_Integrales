import re
from typing import Dict, List

from flask import Flask, jsonify, request, send_from_directory
from sympy import (
    E,
    Integral,
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
    integrate,
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
            'La estructura compuesta permite definir una variable auxiliar '
            'cuyo diferencial aparece multiplicando en la integral.'
        ),
        'example': r'\int (3x^2 + 1)\cos(x^3 + x)\,dx',
        'steps': [
            r'Selecciona $u = x^3 + x$ y calcula $du = (3x^2 + 1)\,dx$.',
            r'Reemplaza en la integral: $\int \cos(u)\,du$.',
            r'Integra $\cos(u)$ para obtener $\sin(u) + C$.',
            r'Retorna a la variable original: $\sin(x^3 + x) + C$.'
        ],
    },
    'parts': {
        'title': 'Integración por partes',
        'badge': '$u$ $dv$',
        'summary': (
            'Se identifica un producto donde una función simplifica al derivarla '
            'y la otra es sencilla de integrar.'
        ),
        'example': r'\int x e^x\,dx',
        'steps': [
            r'Elige $u = x$ y $dv = e^x\,dx$; entonces $du = dx$ y $v = e^x$.',
            r'Aplica la fórmula $\int u\,dv = uv - \int v\,du$.',
            r'Obtén $x e^x - \int e^x dx = x e^x - e^x + C$.'
        ],
    },
    'trig': {
        'title': 'Sustitución trigonométrica',
        'badge': '$\\theta$-sustitución',
        'summary': (
            'La presencia de raíces cuadráticas en expresiones cuadráticas sugiere '
            'introducir un ángulo $\\theta$ para aprovechar identidades trigonométricas.'
        ),
        'example': r'\int \frac{dx}{\sqrt{1 - x^2}}',
        'steps': [
            r'Usa $x = \sin\\theta$ y $dx = \cos\\theta\,d\\theta$.',
            r'Sustituye y simplifica: $\int \frac{\cos\\theta}{\sqrt{1 - \sin^2\\theta}}\,d\\theta = \int d\\theta$.',
            r'Integra para obtener $\\theta + C$ y regresa a $x$ con $\\theta = \arcsin(x)$.'
        ],
    },
    'partial_fractions': {
        'title': 'Fracciones parciales',
        'badge': 'descomposición',
        'summary': (
            'Un cociente de polinomios permite descomponer en fracciones más '
            'simples que se integran término a término.'
        ),
        'example': r'\int \frac{2x + 3}{x^2 + 3x}\,dx',
        'steps': [
            r'Factoriza $x^2 + 3x = x(x + 3)$.',
            r'Plantea $\frac{2x + 3}{x(x + 3)} = \frac{A}{x} + \frac{B}{x + 3}$.',
            r'Resuelve para $A$ y $B$ y luego integra cada término por separado.'
        ],
    },
    'default': {
        'title': 'Exploración general',
        'badge': 'observación',
        'summary': (
            'No se detectó un patrón dominante. Simplifica el integrando, '
            'usa sustituciones básicas o separa en sumas para avanzar.'
        ),
        'example': r'\int (x^2 + 1)\,dx',
        'steps': [
            r'Integra término a término y considera transformaciones algebraicas sencillas.'
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


def evaluate_integral(expr, var: Symbol, lower_expr=None, upper_expr=None):
    try:
        antiderivative = integrate(expr, var)
    except Exception as exc:  # pylint: disable=broad-except
        raise ValueError(f'La integral simbólica no pudo resolverse: {exc}') from exc

    if antiderivative.has(Integral):
        raise ValueError('SymPy no pudo encontrar una antiderivada cerrada para esta expresión.')

    result: Dict[str, object] = {'status': 'ok', 'integral_latex': '', 'extra_notes': []}

    if lower_expr is None or upper_expr is None:
        result['integral_latex'] = f"{integral_to_latex(antiderivative)} + C"
        result['extra_notes'].append('Se incluye la constante de integración $+C$.')
        return result

    try:
        definite_value = integrate(expr, (var, lower_expr, upper_expr))
    except Exception as exc:  # pylint: disable=broad-except
        raise ValueError(f'No se pudo evaluar la integral definida: {exc}') from exc

    antiderivative_latex = integral_to_latex(antiderivative)
    lower_latex = integral_to_latex(lower_expr)
    upper_latex = integral_to_latex(upper_expr)
    evaluated_upper = integral_to_latex(antiderivative.subs(var, upper_expr))
    evaluated_lower = integral_to_latex(antiderivative.subs(var, lower_expr))
    value_latex = integral_to_latex(definite_value)

    result['integral_latex'] = value_latex
    result['evaluation_latex'] = (
        f"{antiderivative_latex}\\Big|_{{{lower_latex}}}^{{{upper_latex}}}"
        f" = {evaluated_upper} - {evaluated_lower} = {value_latex}"
    )
    result['extra_notes'].append(
        'El valor corresponde a evaluar el primitivo entre los límites indicados.'
    )
    return result


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
    integral_type = payload.get('type', 'indefinite')
    lower = payload.get('lower_bound')
    upper = payload.get('upper_bound')

    variable_name = re.sub(r'[^a-zA-Z]', '', variable_name) or 'x'
    integral_type = 'definite' if integral_type == 'definite' else 'indefinite'

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

    lower_expr = upper_expr = None
    if integral_type == 'definite':
        lower_sanitized = sanitize_expression(lower or '', variable_name)
        upper_sanitized = sanitize_expression(upper or '', variable_name)
        if not lower_sanitized or not upper_sanitized:
            return jsonify({
                'status': 'error',
                'error': 'Los límites de integración no pudieron interpretarse.',
            }), 400
        try:
            lower_expr = parse_expression(lower_sanitized, variable_name)
            upper_expr = parse_expression(upper_sanitized, variable_name)
        except ValueError as exc:
            return jsonify({'status': 'error', 'error': str(exc)}), 400

        if lower_expr.has(var_symbol) or upper_expr.has(var_symbol):
            warnings.append(
                'Los límites dependen de la variable de integración; revisa si se trata de '
                'una integral impropia o paramétrica.'
            )

    analysis = {
        'sanitized_expression': integral_to_latex(expr),
        'variable': variable_name,
        'type': integral_type,
        'detected_features': features,
        'warnings': warnings,
    }

    result = {}
    try:
        result = evaluate_integral(expr, var_symbol, lower_expr, upper_expr)
    except ValueError as exc:
        return jsonify({'status': 'error', 'error': str(exc)}), 400

    response = {
        'status': 'ok',
        'analysis': analysis,
        'result': result,
        'method': method,
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
