const integralInput = document.getElementById('integralInput');
const methodSuggestion = document.getElementById('methodSuggestion');
const keyboard = document.querySelector('.keyboard');
const solutionCard = document.getElementById('solutionCard');

const mathFunctions = [
  'sin', 'cos', 'tan', 'sec', 'csc', 'cot',
  'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
  'log', 'ln', 'exp', 'sqrt'
];

const updateMath = () => {
  if (window.MathJax && typeof MathJax.typesetPromise === 'function') {
    MathJax.typesetPromise();
  }
};

const escapeHTML = (unsafe) => unsafe
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  .replace(/'/g, '&#039;');

const methodDetails = {
  substitution: {
    title: 'Sustitución simple',
    badge: 'u-substitución',
    similarIntegral: '\\int (3x^2 + 1)\\,\\cos(x^3 + x)\\,dx',
    explanation: 'Se observa una composición de funciones donde la derivada del interior aparece multiplicando al exterior.',
    steps: [
      'Elige \(u = x^3 + x\), entonces \(du = (3x^2 + 1)\\,dx\).',
      'Reescribe la integral como \(\\int \\cos(u)\\,du\).',
      'Integra: \(\\int \\cos(u)\\,du = \\sin(u) + C\).',
      'Regresa a x: \(\\sin(x^3 + x) + C\).'
    ]
  },
  parts: {
    title: 'Integración por partes',
    badge: 'u dv',
    similarIntegral: '\\int x\\,e^x\\,dx',
    explanation: 'Se identifica un producto de funciones donde una se simplifica al derivar y la otra es fácil de integrar.',
    steps: [
      'Elige \(u = x\) y \(dv = e^x dx\).',
      'Calcula \(du = dx\) y \(v = e^x\).',
      'Aplica la fórmula: \(\\int u\\,dv = u v - \\int v\\,du\).',
      'Obtén \(x e^x - \\int e^x dx = x e^x - e^x + C\).'
    ]
  },
  trig: {
    title: 'Sustitución trigonométrica',
    badge: 'θ-substitución',
    similarIntegral: '\\int \\frac{dx}{\\sqrt{1 - x^2}}',
    explanation: 'La raíz cuadrada con \(1 - x^2\) sugiere un triángulo asociado a \(x = \\sin\\theta\).',
    steps: [
      'Define \(x = \\sin\\theta\), entonces \(dx = \\cos\\theta\\,d\\theta\).',
      'Sustituye: \(\\int \\frac{\\cos\\theta}{\\sqrt{1 - \\sin^2\\theta}}\\,d\\theta\).',
      'Usa la identidad \(1 - \\sin^2\\theta = \\cos^2\\theta\) y simplifica a \(\\int d\\theta\).',
      'Integra: \(\\theta + C\) y regresa a x: \(\\arcsin(x) + C\).'
    ]
  },
  partialFractions: {
    title: 'Fracciones parciales',
    badge: 'descomposición',
    similarIntegral: '\\int \\frac{2x + 3}{x^2 + 3x}\\,dx',
    explanation: 'Una función racional con denominador factorizable sugiere descomponer en fracciones más simples.',
    steps: [
      'Factoriza el denominador: \(x^2 + 3x = x(x + 3)\).',
      'Plantea \(\\frac{2x + 3}{x(x + 3)} = \\frac{A}{x} + \\frac{B}{x + 3}\).',
      'Encuentra A y B: resolviendo, \(A = 1\) y \(B = 1\).',
      'Integra cada término: \(\\int (\\frac{1}{x} + \\frac{1}{x + 3}) dx = \\ln|x| + \\ln|x + 3| + C\).'
    ]
  },
  default: {
    title: 'Exploración general',
    badge: 'observación',
    similarIntegral: '\\int (x^2 + 1)\\,dx',
    explanation: 'No se detectó una estructura clara. Revisa simplificaciones previas o prueba completar cuadrados.',
    steps: [
      'Simplifica el integrando para identificar patrones.',
      'Busca productos, composiciones o denominadores factorizables.',
      'Aplica técnicas básicas de integración término a término.'
    ]
  }
};

const formatSteps = (method) => {
  return `
    <div class="badge">${method.badge}</div>
    <h3>${method.title}</h3>
    <p>${method.explanation}</p>
    <p class="similar">Ejemplo similar: $$${method.similarIntegral}$$</p>
    <ul class="step-list">
      ${method.steps.map(step => `<li><span>${step}</span></li>`).join('')}
    </ul>
  `;
};

const detectMethod = (rawInput) => {
  const input = rawInput.toLowerCase().replace(/\s+/g, '');

  const hasTrig = /(sin|cos|tan|sec|csc|cot)/.test(input);
  const hasSqrt = /√|sqrt\(/.test(input);
  const hasLn = /ln\(/.test(input);
  const hasExp = /e\^|exp\(/.test(input);
  const hasProduct = /[a-z]([a-z]|\(|\^).*([a-z]|\^)/.test(input) && input.includes('*');
  const hasRational = /\//.test(input) && /(x\^\d|x\(|\)x)/.test(input);
  const hasComposite = /(\(.*x.*\))\^|sin\(|cos\(|tan\(|ln\(|exp\(/.test(input));

  if (hasTrig && hasSqrt) {
    return 'trig';
  }
  if (hasProduct || (hasLn && /x/.test(input)) || (hasExp && /x/.test(input))) {
    return 'parts';
  }
  if (hasRational) {
    return 'partialFractions';
  }
  if (hasComposite || hasTrig) {
    return 'substitution';
  }
  return 'default';
};

const renderMethod = (key) => {
  const method = methodDetails[key] ?? methodDetails.default;
  methodSuggestion.innerHTML = formatSteps(method);
};

const detectVariable = (rawInput) => {
  const match = rawInput.match(/d([a-z])\b/i);
  if (match && match[1]) {
    return match[1];
  }
  if (/\by\b/i.test(rawInput) && !/\bx\b/i.test(rawInput)) {
    return 'y';
  }
  return 'x';
};

const sanitizeExpression = (rawInput, variable) => {
  if (!rawInput) {
    return '';
  }

  const variablePattern = new RegExp(`d${variable}\\b`, 'gi');
  const genericDifferential = /d[a-z]\b/gi;
  const functionPattern = mathFunctions.join('|');

  let expr = rawInput
    .replace(/∫/gi, '')
    .replace(variablePattern, '')
    .replace(genericDifferential, '')
    .replace(/\\int/gi, '')
    .replace(/\\,|\\!/g, '')
    .replace(/π/gi, 'pi')
    .replace(/√/g, 'sqrt')
    .replace(/sen/gi, 'sin')
    .replace(/ctg/gi, 'cot')
    .replace(/[{}]/g, (char) => (char === '{' ? '(' : ')'))
    .replace(/\s+/g, '');

  expr = expr.replace(/ln(?=\()/gi, 'log');

  expr = expr
    .replace(new RegExp(`(\\d)${variable}`, 'g'), `$1*${variable}`)
    .replace(new RegExp(`(\\d)(?=${functionPattern}\\()`, 'gi'), '$1*')
    .replace(new RegExp(`${variable}(?=${functionPattern}\\()`, 'gi'), `${variable}*`)
    .replace(/\)\(/g, ')*(')
    .replace(new RegExp(`(${variable}|\\d)\(`, 'g'), '$1*(')
    .replace(new RegExp(`\)(${variable}|\\d)`, 'g'), ')*$1')
    .replace(new RegExp(`\)(?=${functionPattern}\\()`, 'gi'), ')*')
    .replace(new RegExp(`${variable}(?=${variable})`, 'g'), `${variable}*`);

  expr = expr.replace(/\*{2,}/g, '*');

  return expr.trim();
};

const integrateExpression = (expression, variable) => {
  if (typeof nerdamer === 'undefined') {
    throw new Error('nerdamer_not_loaded');
  }
  return nerdamer.integrate(expression, variable);
};

const renderSolution = (rawInput) => {
  if (!rawInput.trim()) {
    solutionCard.innerHTML = `
      <h3>Integral resuelta</h3>
      <p>Ingresa una integral para ver el resultado simbólico acompañado de la constante \(+C\).</p>
    `;
    return;
  }

  const variable = detectVariable(rawInput);
  const expression = sanitizeExpression(rawInput, variable);

  if (!expression) {
    solutionCard.innerHTML = `
      <h3>Integral resuelta</h3>
      <p class="solution-error">No se pudo interpretar la entrada. Revisa la sintaxis de la integral.</p>
    `;
    return;
  }

  try {
    const result = integrateExpression(expression, variable);
    const latex = result.toTeX();
    const interpretedExpression = escapeHTML(expression.replace(/\*/g, '·'));
    const safeVariable = escapeHTML(variable);

    solutionCard.innerHTML = `
      <h3>Integral resuelta</h3>
      <p class="solution-display">$$${latex} + C$$</p>
      <p class="solution-note">Variable integrada: <code>${safeVariable}</code></p>
      <p class="solution-note">Integrando interpretado: <code>${interpretedExpression}</code></p>
    `;
  } catch (error) {
    const message = error.message === 'nerdamer_not_loaded'
      ? 'No se pudo cargar el motor simbólico. Revisa tu conexión e intenta recargar.'
      : 'No se pudo integrar simbólicamente la entrada. Intenta reescribir el integrando.';
    solutionCard.innerHTML = `
      <h3>Integral resuelta</h3>
      <p class="solution-error">${message}</p>
      <p class="solution-note">Entrada interpretada: <code>${escapeHTML(expression)}</code></p>
    `;
  }
};

integralInput.addEventListener('input', (event) => {
  const value = event.target.value;
  if (!value.trim()) {
    methodSuggestion.innerHTML = '<p>Escribe una integral para analizar su estructura.</p>';
    renderSolution('');
    updateMath();
    return;
  }
  const methodKey = detectMethod(value);
  renderMethod(methodKey);
  renderSolution(value);
  updateMath();
});

keyboard.addEventListener('click', (event) => {
  if (event.target.matches('button[data-value]')) {
    event.preventDefault();
    const { value } = event.target.dataset;
    integralInput.focus();
    const selectionStart = integralInput.selectionStart ?? integralInput.value.length;
    const selectionEnd = integralInput.selectionEnd ?? selectionStart;
    const current = integralInput.value;
    const updated = `${current.slice(0, selectionStart)}${value}${current.slice(selectionEnd)}`;
    integralInput.value = updated;
    const newPos = selectionStart + value.length;
    requestAnimationFrame(() => {
      integralInput.setSelectionRange(newPos, newPos);
      integralInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
  }
});

renderMethod('default');
renderSolution('');
updateMath();

if (!(window.MathJax && typeof MathJax.typesetPromise === 'function')) {
  window.addEventListener('load', updateMath);
}
