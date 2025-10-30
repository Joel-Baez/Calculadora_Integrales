import re
from typing import Dict, List

from flask import Flask, jsonify, request, send_from_directory
from sympy import (
    E,
    Integral,
    Symbol,
    acos,
    apart,
    asin,
    atan,
    cos,
    cosh,
    cot,
    csc,
    diff,
    exp,
    factor,
    fraction,
    integrate,
    latex,
    log,
    pi,
    sec,
    simplify,
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
    },
    'parts': {
        'title': 'Integración por partes',
        'badge': '$u$ · $dv$',
        'summary': (
            'Cuando el integrando es un producto, conviene derivar la parte que se simplifica '
            'y antiderivar la que mantiene una forma manejable.'
        ),
    },
    'trig': {
        'title': 'Sustitución trigonométrica',
        'badge': '$\theta$-sustitución',
        'summary': (
            'Las raíces de la forma $\sqrt{a^2 - x^2}$, $\sqrt{a^2 + x^2}$ o '
            '$\sqrt{x^2 - a^2}$ sugieren introducir un ángulo $\theta$ para aprovechar identidades trigonométricas.'
        ),
    },
    'partial_fractions': {
        'title': 'Fracciones parciales',
        'badge': 'descomposición',
        'summary': (
            'Un cociente de polinomios factorizable se puede expresar como suma de fracciones '
            'más simples cuya integración es directa.'
        ),
    },
    'repeated_factors': {
        'title': 'Fracciones parciales con factores repetidos',
        'badge': 'potencias lineales',
        'summary': (
            'Cuando el denominador tiene factores lineales elevados a una potencia, cada potencia requiere '
            'un término separado en la descomposición para integrar sin complicaciones.'
        ),
    },
    'default': {
        'title': 'Exploración general',
        'badge': 'observación',
        'summary': (
            'No se detectó un patrón dominante. Simplifica el integrando, separa en sumas '
            'o intenta sustituciones básicas para avanzar.'
        ),
    },
}


def make_integral_latex(expr, variable: Symbol) -> str:
    return rf"\int {latex(expr)}\\,d{latex(variable)}"


def format_antiderivative(expr, variable: Symbol) -> str:
    constant = Symbol('C')
    if isinstance(expr, Integral):
        return latex(expr)
    return latex(expr + constant)


def describe_trig_substitution(inner_poly, var: Symbol):
    coeffs = inner_poly.all_coeffs()
    if len(coeffs) != 3:
        return None
    a2, b, c = coeffs
    if b != 0:
        return None
    a2 = simplify(a2)
    c = simplify(c)
    if a2.is_zero:
        return None
    pattern = None
    if a2.is_negative and c.is_positive:
        pattern = 'sqrt(a^2 - (bx)^2)'
    elif a2.is_positive and c.is_positive:
        pattern = 'sqrt(a^2 + (bx)^2)'
    elif a2.is_positive and c.is_negative:
        pattern = 'sqrt((bx)^2 - a^2)'
    if pattern is None:
        return None
    return {
        'pattern': pattern,
        'a': simplify(abs(c) ** 0.5),
        'b': simplify(abs(a2) ** 0.5),
    }


def generate_substitution_example(expr, var: Symbol):
    composites = [
        f for f in expr.atoms(exp, log, sin, cos, tan, cot, sec, csc, sinh, cosh, tanh, sqrt)
        if f.has(var)
    ]
    if composites:
        outer = composites[0].func
        inner = composites[0].args[0]
    else:
        inner = var**3 + var
        outer = sin
    derived = diff(inner, var)
    shifted_inner = simplify(inner + 1)
    example_integrand = simplify(derived * outer(shifted_inner))
    antiderivative = integrate(example_integrand, var)
    u_symbol = Symbol('u')
    setup = [
        {'label': '$u$', 'value': latex(shifted_inner)},
        {'label': '$du$', 'value': latex(derived) + rf"\\,d{latex(var)}"},
    ]
    steps = [
        rf"Reconoce la composición ${latex(outer(shifted_inner))}$ y que su derivada interna es ${latex(derived)}$.",
        rf"Plantea $u = {latex(shifted_inner)}$ para obtener $du = {latex(derived)}\\,d{latex(var)}$.",
        rf"Reescribe la integral como $\int {latex(outer(u_symbol))}\\,du$ e intégrala.",
        "Sustituye nuevamente $u$ por la expresión original para volver a la variable principal.",
    ]
    return {
        'example_integral': make_integral_latex(example_integrand, var),
        'example_solution': format_antiderivative(antiderivative, var),
        'setup': setup,
        'steps': steps,
    }


def split_product(expr, var: Symbol):
    factors = list(expr.as_ordered_factors()) if expr.is_Mul else [expr]
    polynomial = None
    other = None
    for factor_candidate in factors:
        poly = factor_candidate.as_poly(var)
        if poly is not None:
            polynomial = factor_candidate
            break
    if polynomial is None:
        polynomial = var
        other = expr / var
    else:
        remaining = simplify(expr / polynomial)
        other = remaining
    return polynomial, other


def generate_parts_example(expr, var: Symbol):
    poly, other = split_product(expr, var)
    poly_example = simplify(poly + 1)
    example_integrand = simplify(poly_example * other)
    du = diff(poly_example, var)
    try:
        v = integrate(other, var)
    except Exception:  # pragma: no cover
        v = Integral(other, var)
    antiderivative = integrate(example_integrand, var)
    setup = [
        {'label': '$u$', 'value': latex(poly_example)},
        {'label': '$du$', 'value': latex(du) + rf"\\,d{latex(var)}"},
        {'label': '$dv$', 'value': latex(other) + rf"\\,d{latex(var)}"},
        {'label': '$v$', 'value': latex(v)},
    ]
    steps = [
        rf"Elige $u = {latex(poly_example)}$ porque su derivada $du = {latex(du)}\\,d{latex(var)}$ simplifica el producto.",
        rf"Antideriva $dv = {latex(other)}\\,d{latex(var)}$ para obtener $v = {latex(v)}$.",
        "Aplica la fórmula $\\int u\\,dv = uv - \\int v\\,du$ y simplifica el resultado.",
    ]
    return {
        'example_integral': make_integral_latex(example_integrand, var),
        'example_solution': format_antiderivative(antiderivative, var),
        'setup': setup,
        'steps': steps,
    }


def generate_trig_example(expr, var: Symbol):
    radicands = [term.args[0] for term in expr.atoms(sqrt) if term.has(var)]
    inner = radicands[0] if radicands else var**2 + 1
    poly = inner.as_poly(var)
    if poly is None:
        poly = (var**2 + 1).as_poly(var)
    description = describe_trig_substitution(poly, var)
    a = description['a'] if description else 1
    b = description['b'] if description else 1
    pattern = description['pattern'] if description else 'sqrt(a^2 + (bx)^2)'
    if pattern == 'sqrt(a^2 - (bx)^2)':
        example_integrand = 1 / sqrt(a**2 - (b * var)**2)
        substitution = rf"{latex(var)} = {latex(a / b)}\\sin\\theta"
        differential = rf"d{latex(var)} = {latex(a)}\\cos\\theta\\,d\\theta"
        inverse = latex(asin(var * b / a))
    elif pattern == 'sqrt((bx)^2 - a^2)':
        example_integrand = sqrt((b * var)**2 - a**2) / var
        substitution = rf"{latex(var)} = {latex(a / b)}\\sec\\theta"
        differential = rf"d{latex(var)} = {latex(a / b)}\\sec\\theta\\tan\\theta\\,d\\theta"
        inverse = latex(acos(a / (b * var)))
    else:
        example_integrand = 1 / sqrt(a**2 + (b * var)**2)
        substitution = rf"{latex(var)} = {latex(a / b)}\\tan\\theta"
        differential = rf"d{latex(var)} = {latex(a / b)}\\sec^2\\theta\\,d\\theta"
        inverse = latex(atan(var * b / a))
    antiderivative = integrate(example_integrand, var)
    setup = [
        {'label': '$x$', 'value': substitution},
        {'label': '$dx$', 'value': differential},
        {'label': '$\\theta$', 'value': inverse},
    ]
    steps = [
        "Identifica la raíz cuadrática y elige una sustitución trigonométrica acorde al patrón $a^2 \\pm x^2$.",
        "Expresa $dx$ y la raíz en términos de $\\theta$ para obtener una integral elemental.",
        "Integra respecto de $\\theta$ y usa la sustitución inversa para regresar a $x$.",
    ]
    return {
        'example_integral': make_integral_latex(example_integrand, var),
        'example_solution': format_antiderivative(antiderivative, var),
        'setup': setup,
        'steps': steps,
    }


def generate_partial_fractions_example(expr, var: Symbol):
    numerator, denominator = fraction(expr)
    denominator = simplify(denominator)
    numerator = simplify(numerator + 1)
    example_integrand = simplify(numerator / denominator)
    decomposition = apart(example_integrand, var, full=True)
    antiderivative = integrate(example_integrand, var)
    setup = [
        {'label': 'Descomposición', 'value': latex(decomposition)},
    ]
    steps = [
        rf"Factoriza el denominador ${latex(factor(denominator))}$ para identificar términos simples.",
        rf"Expresa la fracción como ${latex(decomposition)}$ y determina los coeficientes parciales.",
        "Integra cada término independiente y suma las antiderivadas obtenidas.",
    ]
    return {
        'example_integral': make_integral_latex(example_integrand, var),
        'example_solution': format_antiderivative(antiderivative, var),
        'setup': setup,
        'steps': steps,
    }


def generate_repeated_factors_example(expr, var: Symbol):
    _, denominator = fraction(expr)
    factors = factor(denominator)
    factor_terms = factors.as_ordered_factors() if factors != 0 else []
    dominant = factor_terms[0] if factor_terms else (var - 1) ** 2
    example_integrand = 1 / dominant
    antiderivative = integrate(example_integrand, var)
    decomposition = apart(example_integrand, var, full=True)
    setup = [
        {'label': 'Factor dominante', 'value': latex(dominant)},
        {'label': 'Descomposición', 'value': latex(decomposition)},
    ]
    steps = [
        "Escribe un término de fracción parcial para cada potencia del factor repetido.",
        "Determina las constantes comparando coeficientes o evaluando la identidad resultante.",
        "Integra cada término obteniendo potencias y logaritmos según corresponda.",
    ]
    return {
        'example_integral': make_integral_latex(example_integrand, var),
        'example_solution': format_antiderivative(antiderivative, var),
        'setup': setup,
        'steps': steps,
    }


def generate_default_example(var: Symbol):
    example_integrand = var**2 + 2 * var + 3
    antiderivative = integrate(example_integrand, var)
    steps = [
        "Divide la integral en sumas de potencias simples.",
        "Aplica la regla de la potencia y suma las antiderivadas.",
    ]
    return {
        'example_integral': make_integral_latex(example_integrand, var),
        'example_solution': format_antiderivative(antiderivative, var),
        'setup': [],
        'steps': steps,
    }


EXAMPLE_GENERATORS = {
    'substitution': generate_substitution_example,
    'parts': generate_parts_example,
    'trig': generate_trig_example,
    'partial_fractions': generate_partial_fractions_example,
    'repeated_factors': generate_repeated_factors_example,
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
        ('\\pi', 'pi', False),
        ('\\sqrt', 'sqrt', False),
        ('\\sin', 'sin', False),
        ('\\cos', 'cos', False),
        ('\\tan', 'tan', False),
        ('\\sec', 'sec', False),
        ('\\csc', 'csc', False),
        ('\\cot', 'cot', False),
        ('\\sinh', 'sinh', False),
        ('\\cosh', 'cosh', False),
        ('\\tanh', 'tanh', False),
        ('\\arcsin', 'asin', False),
        ('\\arccos', 'acos', False),
        ('\\arctan', 'atan', False),
        ('\\exp', 'exp', False),
        ('\\ln', 'log', False),
        ('\\log', 'log', False),
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
    expr = expr.replace('\\cdot', '*').replace('\\times', '*')
    expr = expr.replace('\\,', '').replace('\\!', '')
    expr = re.sub(r'\\left|\\right', '', expr)
    def _replace_frac(match):
        numerator, denominator = match.group(1), match.group(2)
        return f'(({numerator}))/(({denominator}))'

    expr = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', _replace_frac, expr)
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
        _, denominator = fraction(expr)
        poly = denominator.as_poly(var)
        if poly is not None:
            factors = poly.factor_list()[1]
            if any(multiplicity > 1 for _, multiplicity in factors):
                features.append('Se detectaron factores repetidos en el denominador.')
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
        _, denominator = fraction(expr)
        poly = denominator.as_poly(var)
        if poly is not None:
            factors = poly.factor_list()[1]
            if any(multiplicity > 1 for _, multiplicity in factors):
                return 'repeated_factors'
        return 'partial_fractions'

    if expr.has(sqrt):
        for radicand in expr.atoms(sqrt):
            inner = radicand.args[0]
            poly = inner.as_poly(var)
            if poly is not None and poly.degree() == 2 and describe_trig_substitution(poly, var):
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
        'latex_integral': make_integral_latex(expr, var_symbol),
        'variable': variable_name,
        'detected_features': features,
        'warnings': warnings,
        'method_key': method_key,
    }

    generator = EXAMPLE_GENERATORS.get(method_key)
    try:
        example_payload = generator(expr, var_symbol) if generator else generate_default_example(var_symbol)
    except Exception:  # pragma: no cover
        example_payload = generate_default_example(var_symbol)

    method_payload = dict(method)
    method_payload['key'] = method_key
    method_payload.update(example_payload)

    response = {
        'status': 'ok',
        'analysis': analysis,
        'method': method_payload,
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
