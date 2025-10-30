const form = document.getElementById('integralForm');
const integralInput = document.getElementById('integralInput');
const variableInput = document.getElementById('variableInput');
const boundsSection = document.querySelector('[data-bounds]');
const lowerBoundInput = document.getElementById('lowerBound');
const upperBoundInput = document.getElementById('upperBound');
const keyboard = document.querySelector('.keyboard');
const statusMessage = document.getElementById('statusMessage');
const analysisCard = document.getElementById('analysisCard');
const solutionCard = document.getElementById('solutionCard');
const methodSuggestion = document.getElementById('methodSuggestion');

const TYPES = {
  indefinite: 'indefinida',
  definite: 'definida'
};

const setStatus = (message, variant = 'idle') => {
  statusMessage.textContent = message;
  statusMessage.className = `status ${variant}`;
};

const updateBoundsVisibility = () => {
  const type = form.elements['integralType'].value;
  if (type === 'definite') {
    boundsSection.hidden = false;
    boundsSection.classList.add('visible');
  } else {
    boundsSection.hidden = true;
    boundsSection.classList.remove('visible');
    lowerBoundInput.value = '';
    upperBoundInput.value = '';
  }
};

Array.from(form.elements['integralType']).forEach((radio) => {
  radio.addEventListener('change', updateBoundsVisibility);
});

const insertAtCursor = (field, value) => {
  const start = field.selectionStart;
  const end = field.selectionEnd;
  const original = field.value;
  let insertion = value;
  let newPosition = start + value.length;

  if (value.endsWith('()')) {
    newPosition = start + value.length - 1;
  }

  field.value = `${original.slice(0, start)}${insertion}${original.slice(end)}`;

  field.focus();
  field.setSelectionRange(newPosition, newPosition);
};

keyboard.addEventListener('click', (event) => {
  if (!(event.target instanceof HTMLButtonElement)) {
    return;
  }
  const { value } = event.target.dataset;
  if (!value) {
    return;
  }
  insertAtCursor(integralInput, value);
});

const renderAnalysis = (analysis) => {
  const { sanitized_expression: sanitized, variable, type, detected_features: features = [], warnings = [] } = analysis;
  const featureList = features.length
    ? `<ul class="feature-list">${features.map((item) => `<li>${item}</li>`).join('')}</ul>`
    : '<p>No se detectaron patrones especiales más allá de la forma general.</p>';

  const warningsList = warnings.length
    ? `<div class="warnings"><h4>Advertencias</h4><ul>${warnings.map((item) => `<li>${item}</li>`).join('')}</ul></div>`
    : '';

  analysisCard.innerHTML = `
    <h3>Análisis del integrando</h3>
    <p><strong>Variable:</strong> ${variable}</p>
    <p><strong>Tipo seleccionado:</strong> ${TYPES[type] ?? type}</p>
    <p><strong>Integrando interpretado:</strong> $$${sanitized || '0'}$$</p>
    ${featureList}
    ${warningsList}
  `;
};

const renderSolution = (result, type) => {
  if (!result || result.status !== 'ok') {
    solutionCard.innerHTML = `
      <h3>Resultado simbólico</h3>
      <p>No se pudo calcular la integral. Revisa el mensaje de error y vuelve a intentarlo.</p>
    `;
    return;
  }

  const { integral_latex: latexResult, evaluation_latex: evaluationLatex, extra_notes: notes = [] } = result;

  const evaluationSection = evaluationLatex
    ? `<div class="evaluation"><h4>Evaluación</h4><p>$$${evaluationLatex}$$</p></div>`
    : '';

  const notesSection = notes.length
    ? `<div class="notes"><h4>Notas</h4><ul>${notes.map((item) => `<li>${item}</li>`).join('')}</ul></div>`
    : '';

  solutionCard.innerHTML = `
    <h3>Resultado simbólico (${TYPES[type] ?? type})</h3>
    <p class="solution">$$${latexResult}$$</p>
    ${evaluationSection}
    ${notesSection}
  `;
};

const renderMethod = (method) => {
  if (!method) {
    methodSuggestion.innerHTML = `
      <h3>Método sugerido</h3>
      <p>No fue posible determinar un método predominante.</p>
    `;
    return;
  }

  const { title, badge, summary, example, steps = [] } = method;

  const stepsList = steps.length
    ? `<ol class="step-list">${steps.map((step) => `<li>${step}</li>`).join('')}</ol>`
    : '';

  methodSuggestion.innerHTML = `
    <div class="badge">${badge}</div>
    <h3>${title}</h3>
    <p>${summary}</p>
    <p class="similar">Ejemplo similar:</p>
    <p class="similar-example">$$${example}$$</p>
    ${stepsList}
  `;
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
  const type = form.elements['integralType'].value;
  const lower = lowerBoundInput.value.trim();
  const upper = upperBoundInput.value.trim();

  if (!expression) {
    setStatus('Por favor escribe un integrando antes de analizar.', 'error');
    return;
  }

  if (!/^[-+*/^(){}\\s0-9a-zA-Zπ√.,]+$/.test(expression.replace(/(sin|cos|tan|cot|sec|csc|asin|acos|atan|sinh|cosh|tanh|log|ln|exp)/g, ''))){
    setStatus('Se detectaron símbolos no soportados. Usa funciones matemáticas estándar.', 'error');
    return;
  }

  if (!/^[a-zA-Z]+$/.test(variable)) {
    setStatus('La variable principal debe contener solo letras.', 'error');
    return;
  }

  if (type === 'definite' && (!lower || !upper)) {
    setStatus('Para integrales definidas debes indicar límites inferior y superior.', 'error');
    return;
  }

  setStatus('Analizando y resolviendo la integral con Python…', 'loading');
  solutionCard.classList.add('loading');

  try {
    const payload = {
      expression,
      variable,
      type,
      lower_bound: type === 'definite' ? lower : null,
      upper_bound: type === 'definite' ? upper : null
    };

    const data = await requestAnalysis(payload);

    if (data.status !== 'ok') {
      throw new Error(data.error || 'No se pudo procesar la integral.');
    }

    renderAnalysis(data.analysis);
    renderSolution(data.result, data.analysis.type);
    renderMethod(data.method);
    setStatus('Integral procesada correctamente.', 'success');
  } catch (error) {
    console.error(error);
    setStatus(error.message || 'Ocurrió un error al procesar la integral.', 'error');
    renderSolution(null);
    renderMethod(null);
  } finally {
    solutionCard.classList.remove('loading');
    retypeset();
  }
});

updateBoundsVisibility();
retypeset();
