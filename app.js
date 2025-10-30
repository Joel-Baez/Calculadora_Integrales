const integralInput = document.getElementById('integralInput');
const methodSuggestion = document.getElementById('methodSuggestion');
const keyboard = document.querySelector('.keyboard');

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
  MathJax.typesetPromise();
};

integralInput.addEventListener('input', (event) => {
  const value = event.target.value;
  if (!value.trim()) {
    methodSuggestion.innerHTML = '<p>Escribe una integral para analizar su estructura.</p>';
    return;
  }
  const methodKey = detectMethod(value);
  renderMethod(methodKey);
});

keyboard.addEventListener('click', (event) => {
  if (event.target.matches('button[data-value]')) {
    const { value } = event.target.dataset;
    const cursorPos = integralInput.selectionStart;
    const current = integralInput.value;
    const updated = `${current.slice(0, cursorPos)}${value}${current.slice(cursorPos)}`;
    integralInput.value = updated;
    integralInput.focus();
    const newPos = cursorPos + value.length;
    integralInput.setSelectionRange(newPos, newPos);
    integralInput.dispatchEvent(new Event('input'));
  }
});

renderMethod('default');
