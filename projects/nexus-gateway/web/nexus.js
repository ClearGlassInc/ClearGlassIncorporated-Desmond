const output = document.querySelector('#output');
const health = document.querySelector('#health');
const requestId = document.querySelector('#request-id');

async function refresh() {
  output.textContent = 'Querying public platform health…';
  try {
    const response = await fetch('/healthz', {cache: 'no-store'});
    const data = await response.json();
    requestId.textContent = response.headers.get('x-request-id') || 'NO REQUEST ID';
    health.textContent = response.ok ? 'GATEWAY ONLINE' : 'DEGRADED';
    output.textContent = JSON.stringify(data, null, 2) + '\n\nAuthenticated operational data is available at /api/v1/sitrep.';
  } catch (error) {
    health.textContent = 'OFFLINE';
    output.textContent = `Health check failed: ${error.message}`;
  }
}

document.querySelector('#refresh').addEventListener('click', refresh);
refresh();
