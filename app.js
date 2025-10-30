const form = document.getElementById('integralForm');
const integralInput = document.getElementById('integralInput');
const variableInput = document.getElementById('variableInput');
const statusMessage = document.getElementById('statusMessage');
const analysisCard = document.getElementById('analysisCard');
const methodSuggestion = document.getElementById('methodSuggestion');
const exampleCard = document.getElementById('exampleCard');
const keyboardTabs = document.getElementById('keyboardTabs');
const keyboardGrid = document.getElementById('keyboardGrid');
const examplePills = document.querySelectorAll('.pill');

const KEYBOARD_GROUPS = [
  {
    id: 'general',
    label: 'General',
    keys: [
      { label: '∫', value: '∫' },
      { label: 'dx', value: 'dx' },
      { label: '(', value: '(' },
      { label: ')', value: ')' },
      { label: '√', value: '√()' },
      { label: '^', value: '^' },
      { label: 'π', value: 'π' },
      { label: 'e^x', value: 'exp()' },
      { label: 'ln', value: 'ln()' },
      { label: 'log', value: 'log()' }
    ]
  },
  {
    id: 'operadores',
    label: 'Operadores',
    keys: [
      { label: '+', value: '+' },
      { label: '−', value: '-' },
      { label: '·', value: '*' },
      { label: '÷', value: '/' },
      { label: '1/', value: '1/' },
      { label: 'xⁿ', value: '^' },
      { label: '·10ⁿ', value: '*10^' }
    ]
  },
  {
    id: 'funciones',
    label: 'Funciones',
    keys: [
      { label: 'sin', value: 'sin()' },
      { label: 'cos', value: 'cos()' },
      { label: 'tan', value: 'tan()' },
      { label: 'sec', value: 'sec()' },
      { label: 'csc', value: 'csc()' },
      { label: 'cot', value: 'cot()' },
      { label: 'sinh', value: 'sinh()' },
      { label: 'cosh', value: 'cosh()' },
      { label: 'tanh', value: 'tanh()' },
      { label: 'asin', value: 'asin()' },
      { label: 'acos', value: 'acos()' },
      { label: 'atan', value: 'atan()' }
    ]
  },
  {
    id: 'sustitucion',
    label: 'Sustitución',
    keys: [
      { label: 'u', value: 'u' },
      { label: 'du', value: 'du' },
      { label: 'dx', value: 'dx' },
      { label: 'g(x)', value: 'g(x)' },
      { label: 'h(x)', value: 'h(x)' },
      { label: 'f(g(x))', value: 'f(g(x))' }
    ]
  },
  {
    id: 'partes',
    label: 'Por partes',
    keys: [
      { label: 'u', value: 'u' },
      { label: 'du', value: 'du' },
      { label: 'v', value: 'v' },
      { label: 'dv', value: 'dv' },
      { label: 'uv', value: 'u*v' },
      { label: '∫v·du', value: '∫v*du' },
      { label: '∫u·dv', value: '∫u*dv' }
    ]
  },
  {
    id: 'trig',
    label: 'Sust. trig.',
    keys: [
      { label: 'sin', value: 'sin()' },
      { label: 'cos', value: 'cos()' },
      { label: 'tan', value: 'tan()' },
      { label: 'sec', value: 'sec()' },
      { label: 'csc', value: 'csc()' },
      { label: 'cot', value: 'cot()' },
      { label: 'asin', value: 'asin()' },
      { label: 'acos', value: 'acos()' },
      { label: 'atan', value: 'atan()' }
    ]
  },
  {
    id: 'fracciones',
    label: 'Fracciones parciales',
    keys: [
      { label: '1/x', value: '1/x' },
      { label: '1/(x+a)', value: '1/(x+a)' },
      { label: '(ax+b)/(cx+d)', value: '(a*x+b)/(c*x+d)' },
      { label: 'factor', value: '(x+a)*(x+b)' },
      { label: 'A/x + B/(x+a)', value: 'A/x + B/(x+a)' },
      { label: 'polinomio', value: 'x^2 + a*x + b' }
    ]
  }
];

const METHOD_TO_GROUP = {
  substitution: 'sustitucion',
  parts: 'partes',
  trig: 'trig',
  partial_fractions: 'fracciones'
};

let activeGroup = KEYBOARD_GROUPS[0].id;

const setStatus = (message, variant = 'idle') => {
  statusMessage.textContent = message;
  statusMessage.className = `status ${variant}`;
};

const autoResize = (element) => {
  if (!element) return;
  element.style.height = 'auto';
  element.style.height = `${element.scrollHeight}px`;
};

autoResize(integralInput);
integralInput.addEventListener('input', () => autoResize(integralInput));

const insertAtCursor = (field, value) => {
  const start = field.selectionStart;
  const end = field.selectionEnd;
  const original = field.value;
  let newValue = value;
  let newPosition = start + value.length;

  if (value === '()' || value.endsWith('()')) {
    newValue = value === '()' ? '()' : value;
    newPosition = start + newValue.length - 1;
  }

  field.value = `${original.slice(0, start)}${newValue}${original.slice(end)}`;
  field.focus();
  field.setSelectionRange(newPosition, newPosition);
  autoResize(field);
};

const renderKeyboardTabs = () => {
  keyboardTabs.innerHTML = KEYBOARD_GROUPS.map(({ id, label }) => `
    <button type="button" class="tab ${id === activeGroup ? 'active' : ''}" data-group="${id}" role="tab">
      ${label}
    </button>
  `).join('');
};

const renderKeyboardKeys = () => {
  const group = KEYBOARD_GROUPS.find(({ id }) => id === activeGroup) ?? KEYBOARD_GROUPS[0];
  keyboardGrid.innerHTML = group.keys.map(({ label, value }) => `
    <button type="button" class="key" data-value="${value}">${label}</button>
  `).join('');
};

const refreshKeyboard = () => {
  renderKeyboardTabs();
  renderKeyboardKeys();
};

keyboardTabs.addEventListener('click', (event) => {
  if (!(event.target instanceof HTMLButtonElement)) {
    return;
  }
  const { group } = event.target.dataset;
  if (!group || group === activeGroup) {
    return;
  }
  activeGroup = group;
  refreshKeyboard();
});

keyboardGrid.addEventListener('click', (event) => {
  if (!(event.target instanceof HTMLButtonElement)) {
    return;
  }
  const { value } = event.target.dataset;
  if (!value) {
    return;
  }
  insertAtCursor(integralInput, value);
});

refreshKeyboard();

document.addEventListener('keydown', (event) => {
  if (event.key === 'Tab' && document.activeElement === integralInput) {
    event.preventDefault();
    insertAtCursor(integralInput, '    ');
  }
});

examplePills.forEach((pill) => {
  pill.addEventListener('click', () => {
    const { example } = pill.dataset;
    if (!example) return;
    integralInput.value = example;
    autoResize(integralInput);
    integralInput.focus();
  });
});

const renderAnalysis = (analysis) => {
  const {
    sanitized_expression: sanitized,
    variable,
    detected_features: features = [],
    warnings = [],
  } = analysis;

  const featureList = features.length
    ? `<ul class="feature-list">${features.map((item) => `<li>${item}</li>`).join('')}</ul>`
    : '<p>No se detectaron patrones especiales adicionales.</p>';

  const warningsList = warnings.length
    ? `<div class="warnings"><h4>Advertencias</h4><ul>${warnings.map((item) => `<li>${item}</li>`).join('')}</ul></div>`
    : '';

  analysisCard.innerHTML = `
    <h3>Análisis del integrando</h3>
    <p><strong>Variable principal:</strong> ${variable}</p>
    <p><strong>Interpretación simbólica:</strong> $$${sanitized || '0'}$$</p>
    ${featureList}
    ${warningsList}
  `;
};

const renderMethod = (method) => {
  if (!method) {
    methodSuggestion.innerHTML = `
      <h3>Método sugerido</h3>
      <p>No fue posible determinar un método predominante. Simplifica el integrando y vuelve a intentarlo.</p>
    `;
    exampleCard.innerHTML = `
      <h3>Ejemplo guiado</h3>
      <p>No se generó un ejemplo porque no hay método sugerido.</p>
    `;
    return;
  }

  const { title, badge, summary, example_integral: exampleIntegral, example_solution: exampleSolution, steps = [], setup = [], key } = method;

  const stepsList = steps.length
    ? `<ol class="step-list">${steps.map((step) => `<li>${step}</li>`).join('')}</ol>`
    : '';

  const setupList = setup.length
    ? `<div class="setup"><h4>Datos clave</h4><div class="setup-grid">${setup
        .map(({ label, value }) => `<div class="setup-item"><span class="setup-label">${label}</span><span class="setup-value">$$${value}$$</span></div>`)
        .join('')}</div></div>`
    : '';

  methodSuggestion.innerHTML = `
    <div class="badge">${badge}</div>
    <h3>${title}</h3>
    <p>${summary}</p>
  `;

  exampleCard.innerHTML = `
    <h3>Ejemplo guiado</h3>
    <p class="similar">Integral modelo:</p>
    <p class="similar-example">$$${exampleIntegral}$$</p>
    <p class="similar">Resultado esperado:</p>
    <p class="similar-example">$$${exampleSolution}$$</p>
    ${setupList}
    ${stepsList}
  `;

  highlightKeyboardGroup(key);
};

const highlightKeyboardGroup = (methodKey) => {
  const group = METHOD_TO_GROUP[methodKey];
  if (!group) {
    return;
  }
  if (activeGroup !== group) {
    activeGroup = group;
    refreshKeyboard();
  } else {
    refreshKeyboard();
  }
};

const requestAnalysis = async (payload) => {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Error inesperado en el servidor.');
  }

  return response.json();
};

const retypeset = () => {
  if (window.MathJax && typeof MathJax.typesetPromise === 'function') {
    MathJax.typesetPromise();
  }
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const expression = integralInput.value.trim();
  const variable = variableInput.value.trim() || 'x';

  if (!expression) {
    setStatus('Por favor escribe un integrando antes de analizar.', 'error');
    return;
  }

  if (!/^[a-zA-Z]+$/.test(variable)) {
    setStatus('La variable principal debe escribirse únicamente con letras.', 'error');
    return;
  }

  setStatus('Analizando la integral en el servidor de Python…', 'loading');

  try {
    const payload = {
      expression,
      variable
    };

    const data = await requestAnalysis(payload);

    if (data.status !== 'ok') {
      throw new Error(data.error || 'No se pudo procesar la integral.');
    }

    renderAnalysis(data.analysis);
    renderMethod(data.method);
    setStatus('Análisis completado. Revisa el método sugerido y el ejemplo.', 'success');
  } catch (error) {
    console.error(error);
    setStatus(error.message || 'Ocurrió un error al procesar la integral.', 'error');
    renderMethod(null);
  } finally {
    retypeset();
  }
});

retypeset();
