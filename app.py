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
    Wild,
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
            r'Una función compuesta $f(g(x))$ cuya derivada $g\'(x)$ aparece multiplicando '
            r'permite introducir $u = g(x)$ para integrar en una sola variable auxiliar.'
        ),
    },
    'parts': {
        'title': 'Integración por partes',
        'badge': '$u$ · $dv$',
        'summary': (
            r'Cuando el integrando es un producto, conviene derivar la parte que se simplifica '
            r'y antiderivar la que mantiene una forma manejable.'
        ),
    },
    'trig': {
        'title': 'Sustitución trigonométrica',
        'badge': '$\theta$-sustitución',
        'summary': (
            r'Las raíces de la forma $\sqrt{a^2 - x^2}$, $\sqrt{a^2 + x^2}$ o '
            r'$\sqrt{x^2 - a^2}$ sugieren introducir un ángulo $\theta$ para aprovechar identidades trigonométricas.'
        ),
    },
    'partial_fractions': {
        'title': 'Fracciones parciales',
        'badge': 'descomposición',
        'summary': (
            r'Un cociente de polinomios factorizable se puede expresar como suma de fracciones '
            r'más simples cuya integración es directa.'
        ),
    },
    'repeated_factors': {
        'title': 'Fracciones parciales con factores repetidos',
        'badge': 'potencias lineales',
        'summary': (
            r'Cuando el denominador tiene factores lineales elevados a una potencia, cada potencia requiere '
            r'un término separado en la descomposición para integrar sin complicaciones.'
        ),
    },
    'default': {
        'title': 'Exploración general',
        'badge': 'observación',
        'summary': (
            r'No se detectó un patrón dominante. Simplifica el integrando, separa en sumas '
            r'o intenta sustituciones básicas para avanzar.'
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


def build_step(title: str, description: str, equations: List[str] | None = None) -> Dict[str, object]:
    payload: Dict[str, object] = {'title': title, 'description': description}
    if equations:
        payload['equations'] = equations
    return payload


def describe_trig_substitution(inner_expr, var: Symbol):
    inner = simplify(inner_expr)
    a = Wild('a', exclude=[var])
    k = Wild('k', exclude=[var])

    patterns = [
        (a**2 - (k * var) ** 2, 'sqrt(a^2 - (bx)^2)'),
        ((k * var) ** 2 - a**2, 'sqrt((bx)^2 - a^2)'),
        (a**2 + (k * var) ** 2, 'sqrt(a^2 + (bx)^2)'),
        ((k * var) ** 2 + a**2, 'sqrt(a^2 + (bx)^2)'),
    ]

    for pattern_expr, pattern_label in patterns:
        match = inner.match(pattern_expr)
        if match and match.get(a) not in (None, 0) and match.get(k) not in (None, 0):
            a_val = simplify(abs(match[a]))
            b_val = simplify(abs(match[k]))
            return {'pattern': pattern_label, 'a': a_val, 'b': b_val}

    return None


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
        {'label': 'u', 'value': latex(shifted_inner)},
        {'label': 'du', 'value': latex(derived) + rf"\\,d{latex(var)}"},
    ]
    reduced_integral = integrate(outer(u_symbol), u_symbol)
    steps = [
        build_step(
            '1) Identificamos la función compuesta',
            (
                'Notamos que la parte interior '
                f"${latex(shifted_inner)}$ aparece junto con su derivada ${latex(derived)}$ "
                'multiplicando a la función exterior.'
            ),
            [make_integral_latex(example_integrand, var)],
        ),
        build_step(
            '2) Declaramos la sustitución',
            'Elegimos una variable auxiliar que simplifique la composición.',
            [
                rf"u = {latex(shifted_inner)}",
                rf"du = {latex(derived)}\\,d{latex(var)}",
            ],
        ),
        build_step(
            '3) Integramos en términos de $u$',
            'Reescribimos la integral con la nueva variable y resolvemos la primitiva elemental.',
            [rf"\int {latex(outer(u_symbol))}\\,du = {latex(reduced_integral)}"],
        ),
        build_step(
            '4) Volvemos a la variable original',
            'Sustituimos $u$ por la expresión inicial y añadimos la constante de integración.',
            [format_antiderivative(antiderivative, var)],
        ),
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
        {'label': 'u', 'value': latex(poly_example)},
        {'label': 'du', 'value': latex(du) + rf"\\,d{latex(var)}"},
        {'label': 'dv', 'value': latex(other) + rf"\\,d{latex(var)}"},
        {'label': 'v', 'value': latex(v)},
    ]
    steps = [
        build_step(
            '1) Elegimos integración por partes',
            'Reorganizamos el producto para derivar la parte algebraica y antiderivar la parte especial.',
            [make_integral_latex(example_integrand, var)],
        ),
        build_step(
            '2) Fijamos las asignaciones',
            'Asignamos $u$ y $dv$ para que la derivada de $u$ reduzca el grado del polinomio.',
            [
                rf"u = {latex(poly_example)} \Rightarrow du = {latex(du)}\\,d{latex(var)}",
                rf"dv = {latex(other)}\\,d{latex(var)} \Rightarrow v = {latex(v)}",
            ],
        ),
        build_step(
            '3) Aplicamos la fórmula',
            'Utilizamos $\int u\\,dv = uv - \int v\\,du$ y simplificamos la integral restante.',
            [
                rf"\int {latex(poly_example * other)}\\,d{latex(var)} = {latex(poly_example)}{latex(v)} - \int {latex(v)}\\,{latex(du)}",
            ],
        ),
        build_step(
            '4) Presentamos la primitiva final',
            'Sumamos el resultado y añadimos la constante de integración.',
            [format_antiderivative(antiderivative, var)],
        ),
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
    description = describe_trig_substitution(inner, var)
    a = description['a'] if description else 1
    b = description['b'] if description else 1
    pattern = description['pattern'] if description else 'sqrt(a^2 + (bx)^2)'
    theta = Symbol('theta')

    if pattern == 'sqrt(a^2 - (bx)^2)':
        example_integrand = 1 / sqrt(a**2 - (b * var) ** 2)
        substitution_expr = (a / b) * sin(theta)
        inverse = latex(asin(var * b / a))
    elif pattern == 'sqrt((bx)^2 - a^2)':
        example_integrand = sqrt((b * var) ** 2 - a**2) / var
        substitution_expr = (a / b) * sec(theta)
        inverse = latex(acos(a / (b * var)))
    else:
        example_integrand = 1 / sqrt(a**2 + (b * var) ** 2)
        substitution_expr = (a / b) * tan(theta)
        inverse = latex(atan(var * b / a))

    dx_theta = diff(substitution_expr, theta)
    substitution = rf"{latex(var)} = {latex(substitution_expr)}"
    differential = rf"d{latex(var)} = {latex(dx_theta)}\\,d\\theta"
    integrand_theta = simplify(example_integrand.subs(var, substitution_expr) * dx_theta)
    theta_integral = latex(integrand_theta)
    theta_antiderivative = latex(integrate(integrand_theta, theta))
    antiderivative = integrate(example_integrand, var)

    setup = [
        {'label': 'Sustitución', 'value': substitution},
        {'label': 'Diferencial', 'value': differential},
        {'label': 'Inversa', 'value': inverse},
    ]

    steps = [
        build_step(
            '1) Reconocemos el patrón cuadrático',
            'La raíz identifica el uso de una identidad trigonométrica para eliminar la raíz.',
            [make_integral_latex(example_integrand, var)],
        ),
        build_step(
            '2) Realizamos la sustitución angular',
            'Expresamos $x$ y $dx$ con $\\theta$ para simplificar la raíz.',
            [substitution, differential],
        ),
        build_step(
            '3) Integramos en $\\theta$',
            'Resolvemos la integral elemental resultante y simplificamos.',
            [rf"\int {theta_integral}\\,d\\theta = {theta_antiderivative}"],
        ),
        build_step(
            '4) Retornamos a la variable $x$',
            'Aplicamos la sustitución inversa para expresar el resultado final en términos de la variable original.',
            [format_antiderivative(antiderivative, var)],
        ),
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
        {'label': 'Denominador', 'value': latex(factor(denominator))},
        {'label': 'Descomposición', 'value': latex(decomposition)},
    ]
    steps = [
        build_step(
            '1) Factorizamos el denominador',
            'El objetivo es expresar el cociente como suma de términos simples.',
            [latex(factor(denominator))],
        ),
        build_step(
            '2) Planteamos las fracciones parciales',
            'Escribimos la descomposición y hallamos los coeficientes que la satisfacen.',
            [latex(decomposition)],
        ),
        build_step(
            '3) Integramos término a término',
            'Cada fracción elemental tiene una primitiva directa, que sumamos al final.',
            [format_antiderivative(antiderivative, var)],
        ),
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
        {'label': 'Factor repetido', 'value': latex(dominant)},
        {'label': 'Descomposición', 'value': latex(decomposition)},
    ]
    steps = [
        build_step(
            '1) Aislamos el factor repetido',
            'Identificamos el factor dominante y preparamos términos para cada potencia.',
            [latex(dominant)],
        ),
        build_step(
            '2) Asignamos fracciones parciales escalonadas',
            'Cada potencia genera una fracción con numeradores constantes a determinar.',
            [latex(decomposition)],
        ),
        build_step(
            '3) Integramos sumando cada contribución',
            'Aparecen potencias y logaritmos según la potencia del factor.',
            [format_antiderivative(antiderivative, var)],
        ),
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
        build_step(
            '1) Separar en sumas manejables',
            'Dividimos la integral en términos independientes.',
            [latex(example_integrand)],
        ),
        build_step(
            '2) Aplicar reglas básicas',
            'Integramos cada potencia usando la regla $\int x^{n}\\,dx = x^{n+1}/(n+1)$.',
            [format_antiderivative(antiderivative, var)],
        ),
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
            inner = simplify(radicand.args[0])
            description = describe_trig_substitution(inner, var)
            if description:
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
