import http from 'node:http';
let failures = 0;
const server = http.createServer((req, res) => {
  if (req.method !== 'POST' || req.url !== '/simulate') { res.writeHead(404); return res.end(); }
  failures = Math.min(failures + 1, 5);
  const retryAfter = 2 ** (failures - 1);
  res.writeHead(429, { 'content-type': 'application/json', 'retry-after': String(retryAfter) });
  res.end(JSON.stringify({ simulated: true, accepted: false, lockout: failures >= 5, retryAfterSeconds: retryAfter }));
});
server.listen(8080, '0.0.0.0');
