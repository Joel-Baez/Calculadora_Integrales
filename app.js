const form = document.getElementById('integralForm');
const mathfieldElement = document.getElementById('mathField');
const latexPreview = document.getElementById('latexPreview');
const hiddenInput = document.getElementById('integralInput');
const variableInput = document.getElementById('variableInput');
const variableDisplay = document.getElementById('variableDisplay');
const statusMessage = document.getElementById('statusMessage');
const analysisCard = document.getElementById('analysisCard');
const methodSuggestion = document.getElementById('methodSuggestion');
const exampleCard = document.getElementById('exampleCard');
const keyboardTabs = document.getElementById('keyboardTabs');
const keyboardGrid = document.getElementById('keyboardGrid');
const examplePills = document.querySelectorAll('.pill');

let mathField = null;

const KEYBOARD_GROUPS = [
  {
    id: 'general',
    label: 'General',
    keys: [
      { label: '7', latex: '7' },
      { label: '8', latex: '8' },
      { label: '9', latex: '9' },
      { label: '4', latex: '4' },
      { label: '5', latex: '5' },
      { label: '6', latex: '6' },
      { label: '1', latex: '1' },
      { label: '2', latex: '2' },
      { label: '3', latex: '3' },
      { label: '0', latex: '0' },
      { label: 'x', latex: 'x' },
      { label: 'y', latex: 'y' },
      { label: '(', latex: '(' },
      { label: ')', latex: ')' },
      { label: '| |', latex: '\\left|\\placeholder{}\\right|' },
      { label: '√', latex: '\\sqrt{\\placeholder{}}' },
      { label: 'xⁿ', latex: 'x^{\\placeholder{}}' },
      { label: 'eˣ', latex: 'e^{\\placeholder{}}' },
      { label: 'π', latex: '\\pi' },
      { label: 'e', latex: 'e' }
    ]
  },
  {
    id: 'operadores',
    label: 'Operadores',
    keys: [
      { label: '+', latex: '+' },
      { label: '−', latex: '-' },
      { label: '·', latex: '\\cdot' },
      { label: '÷', latex: '\\div' },
      { label: '=', latex: '=' },
      { label: '^', latex: '^{\\placeholder{}}' },
      { label: '()', latex: '\\left(\\placeholder{}\\right)' },
      { label: '[ ]', latex: '\\left[\\placeholder{}\\right]' }
    ]
  },
  {
    id: 'funciones',
    label: 'Funciones',
    keys: [
      { label: 'exp', latex: '\\exp\\left(\\placeholder{}\\right)' },
      { label: 'ln', latex: '\\ln\\left(\\placeholder{}\\right)' },
      { label: 'log', latex: '\\log\\left(\\placeholder{}\\right)' },
      { label: 'abs', latex: '\\left|\\placeholder{}\\right|' },
      { label: '√()', latex: '\\sqrt{\\placeholder{}}' }
    ]
  },
  {
    id: 'trigonometria',
    label: 'Trigonometría',
    keys: [
      { label: 'sin', latex: '\\sin\\left(\\placeholder{}\\right)' },
      { label: 'cos', latex: '\\cos\\left(\\placeholder{}\\right)' },
      { label: 'tan', latex: '\\tan\\left(\\placeholder{}\\right)' },
      { label: 'sec', latex: '\\sec\\left(\\placeholder{}\\right)' },
      { label: 'csc', latex: '\\csc\\left(\\placeholder{}\\right)' },
      { label: 'cot', latex: '\\cot\\left(\\placeholder{}\\right)' },
      { label: 'asin', latex: '\\arcsin\\left(\\placeholder{}\\right)' },
      { label: 'acos', latex: '\\arccos\\left(\\placeholder{}\\right)' },
      { label: 'atan', latex: '\\arctan\\left(\\placeholder{}\\right)' },
      { label: 'θ', latex: '\\theta' }
    ]
  },
  {
    id: 'fracciones',
    label: 'Fracciones',
    keys: [
      { label: 'a/b', latex: '\\frac{\\placeholder{}}{\\placeholder{}}' },
      { label: '1/x', latex: '\\frac{1}{\\placeholder{}}' },
      { label: '1/(x+a)', latex: '\\frac{1}{\\left(\\placeholder{}\\right)}' },
      { label: '(ax+b)/(cx+d)', latex: '\\frac{\\placeholder{}}{\\placeholder{}}' }
    ]
  },
  {
    id: 'estrategias',
    label: 'Estrategias',
    keys: [
      { label: 'u', latex: 'u' },
      { label: 'du', latex: '\\,du' },
      { label: 'v', latex: 'v' },
      { label: 'dv', latex: '\\,dv' },
      { label: 'dx', latex: '\\,dx' },
      { label: 'dθ', latex: '\\,d\\theta' },
      { label: 'u = g(x)', latex: 'u=\\placeholder{}' },
      { label: "g'(x)", latex: "g'(\\placeholder{})" }
    ]
  }
];

const METHOD_TO_GROUP = {
  substitution: 'estrategias',
  parts: 'estrategias',
  trig: 'trigonometria',
  partial_fractions: 'fracciones',
  repeated_factors: 'fracciones'
};

let activeGroup = KEYBOARD_GROUPS[0].id;

const setStatus = (message, variant = 'idle') => {
  if (!statusMessage) return;
  statusMessage.textContent = message;
  statusMessage.className = `status ${variant}`;
};

const retypeset = () => {
  if (window.MathJax && typeof MathJax.typesetPromise === 'function') {
    MathJax.typesetPromise();
  }
};

const sanitizeVariable = (value) => {
  const letters = (value || '').replace(/[^a-zA-Z]/g, '');
  return letters || 'x';
};

const updateVariableDisplay = () => {
  const sanitized = sanitizeVariable(variableInput.value);
  variableInput.value = sanitized;
  variableDisplay.textContent = sanitized;
  updatePreview();
};

const getLatexValue = () => {
  if (mathField) {
    return mathField.getValue('latex-expanded') || '';
  }
  return hiddenInput?.value || '';
};

const setLatexValue = (value) => {
  if (mathField) {
    mathField.setValue(value, { format: 'latex' });
  } else if (hiddenInput) {
    hiddenInput.value = value;
  }
  handleLatexInput();
};

const updateHiddenValue = () => {
  if (hiddenInput) {
    hiddenInput.value = getLatexValue();
  }
};

const updatePreview = () => {
  if (!latexPreview) {
    return;
  }
  const latex = getLatexValue();
  const variable = sanitizeVariable(variableInput.value);
  if (!latex) {
    latexPreview.innerHTML = '<span class="preview-placeholder">Vista previa en LaTeX</span>';
  } else {
    latexPreview.innerHTML = `$$\\int ${latex}\\,d${variable}$$`;
  }
  retypeset();
};

const handleLatexInput = () => {
  mathfieldElement?.classList.remove('invalid');
  updateHiddenValue();
  updatePreview();
  if (getLatexValue()) {
    setStatus('Expresión actualizada. Pulsa «Sugerir método».', 'idle');
  } else {
    setStatus('Escribe un integrando para comenzar.', 'idle');
  }
};

const insertLatex = (snippet) => {
  if (mathField) {
    mathField.focus();
    mathField.insert(snippet);
    handleLatexInput();
    return;
  }
  setStatus('No se pudo insertar el símbolo porque el editor no está disponible.', 'error');
};

const initializeMathField = () => {
  if (!mathfieldElement) {
    setStatus('No se encontró el editor de integrales en la página.', 'error');
    return;
  }

  if (!window.MathLive || typeof window.MathLive.makeMathField !== 'function') {
    setStatus('No se pudo cargar el editor matemático. Verifica tu conexión e intenta de nuevo.', 'error');
    return;
  }

  mathField = window.MathLive.makeMathField(mathfieldElement, {
    smartMode: true,
    smartFence: true,
    virtualKeyboardMode: 'manual',
    virtualKeyboardTheme: 'material',
    readOnly: false
  });

  mathField.on('input', handleLatexInput);
  mathfieldElement.addEventListener('focusin', () => mathfieldElement.classList.remove('invalid'));
  handleLatexInput();
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
  keyboardGrid.innerHTML = group.keys
    .map(({ label, latex }) => `
      <button type="button" class="key" data-latex="${latex}">${label}</button>
    `)
    .join('');
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
  const { latex } = event.target.dataset;
  if (!latex) {
    return;
  }
  insertLatex(latex);
});

initializeMathField();

refreshKeyboard();

examplePills.forEach((pill) => {
  pill.addEventListener('click', () => {
    const latex = pill.dataset.latex;
    if (!latex) return;
    if (mathField) {
      setLatexValue(latex);
      mathField.focus();
    }
    setStatus('Ejemplo cargado. Ajusta la expresión si lo necesitas.', 'idle');
  });
});

const renderAnalysis = (analysis) => {
  const {
    latex_integral: latexIntegral = '',
    variable = 'x',
    detected_features: features = [],
    warnings = []
  } = analysis;

  const featureList = features.length
    ? `<ul class="feature-list">${features.map((item) => `<li>${item}</li>`).join('')}</ul>`
    : '<p>No se detectaron patrones especiales adicionales.</p>';

  const warningsList = warnings.length
    ? `<div class="warnings"><h4>Advertencias</h4><ul>${warnings.map((item) => `<li>${item}</li>`).join('')}</ul></div>`
    : '';

  analysisCard.innerHTML = `
    <h3>Análisis del integrando</h3>
    <p class="integral-display">$$${latexIntegral || ''}$$</p>
    <div class="analysis-details">
      <div><span class="detail-label">Variable principal</span><span class="detail-value">${variable}</span></div>
    </div>
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

  const {
    title,
    badge,
    summary,
    example_integral: exampleIntegral,
    example_solution: exampleSolution,
    steps = [],
    setup = [],
    key
  } = method;

  const stepsList = steps.length
    ? `<ol class="step-list">${steps
        .map(({ title, description, equations = [] }) => `
          <li>
            <h4>${title}</h4>
            <p>${description}</p>
            ${
              equations.length
                ? `<div class="equation-group">${equations
                    .map((eq) => `<p class="equation">$$${eq}$$</p>`)
                    .join('')}</div>`
                : ''
            }
          </li>
        `)
        .join('')}</ol>`
    : '';

  const setupList = setup.length
    ? `<div class="setup"><h4>Datos clave</h4><div class="setup-grid">${setup
        .map(({ label, value }) => `
          <div class="setup-item">
            <span class="setup-label">${label}</span>
            <span class="setup-value">$$${value}$$</span>
          </div>
        `)
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

updateVariableDisplay();
updateHiddenValue();
updatePreview();

variableInput.addEventListener('input', updateVariableDisplay);

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const latexExpression = getLatexValue().trim();
  const variable = sanitizeVariable(variableInput.value);

  if (!latexExpression) {
    setStatus('Por favor completa el integrando en el editor antes de analizar.', 'error');
    mathfieldElement?.classList.add('invalid');
    return;
  }

  if (latexExpression.includes('\\placeholder')) {
    setStatus('Completa los espacios vacíos del teclado antes de enviar la integral.', 'error');
    mathfieldElement?.classList.add('invalid');
    return;
  }

  setStatus('Analizando la integral en el servidor de Python…', 'loading');

  try {
    const payload = {
      expression: latexExpression,
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
