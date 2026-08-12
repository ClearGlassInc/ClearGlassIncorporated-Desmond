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

// FastAPI serves the Swagger UI at /docs, but only when this page is served by
// the gateway itself. The same file is also published on the marketing site,
// where that path does not exist — so resolve the link at runtime and leave it
// inert (and visibly so) wherever the API is not actually reachable.
(function wireOpenApi() {
  const link = document.querySelector('#openapi');
  if (!link) return;
  const endpoint = link.getAttribute('data-endpoint');
  fetch(endpoint, {method: 'HEAD'})
    .then(function (response) {
      if (!response.ok) throw new Error(String(response.status));
      link.href = endpoint;
    })
    .catch(function () {
      link.setAttribute('aria-disabled', 'true');
      link.title = 'Available when the NEXUS Gateway service is running';
    });
})();

refresh();
