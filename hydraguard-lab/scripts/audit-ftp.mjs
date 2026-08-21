const allowed = new Set(['lab-ftp','localhost','127.0.0.1']);
const target = process.argv[process.argv.indexOf('--target')+1] ?? 'lab-ftp';
if (!allowed.has(target)) { console.error('BLOCKED: target is outside the local HydraGuard lab.'); process.exit(2); }
console.log(JSON.stringify({ simulation: true, target, port: 21, checks: ['banner','tls-capability','anonymous-config','timeout'], credentialsObtained: false, exploitationPerformed: false }));
