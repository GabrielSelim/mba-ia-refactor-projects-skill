// Smoke test dos endpoints originais do ecommerce-api-legacy (mesmas chamadas do api.http + casos de erro).
// Uso: node smoke_project2.js http://127.0.0.1:3000
const BASE = (process.argv[2] || 'http://127.0.0.1:3000').replace(/\/$/, '');

async function call(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let shape;
  try {
    const json = JSON.parse(text);
    shape = Array.isArray(json)
      ? `array[${json.length}] ${json[0] ? JSON.stringify(Object.keys(json[0]).sort()) : ''}`
      : JSON.stringify(Object.keys(json).sort());
  } catch {
    shape = `text "${text.slice(0, 60)}"`;
  }
  console.log(`${method.padEnd(6)} ${path.padEnd(30)} -> ${res.status}  ${shape}`);
  return text;
}

(async () => {
  await call('POST', '/api/checkout', { usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: '4111222233334444' });
  await call('POST', '/api/checkout', { usr: 'João', eml: 'joao@teste.com', pwd: '123', c_id: 1, card: '5111222233334444' });
  await call('POST', '/api/checkout', { usr: 'Sem curso', eml: 'x@teste.com', pwd: 'abc', c_id: 999, card: '4111222233334444' });
  await call('POST', '/api/checkout', { usr: 'Faltando' });
  await call('POST', '/api/checkout', { usr: 'Leonan', eml: 'leonan@fullcycle.com.br', pwd: '123', c_id: 2, card: '4000000000000002' });
  const report = await call('GET', '/api/admin/financial-report');
  console.log('       report:', report);
  await call('DELETE', '/api/users/1');
  const after = await call('GET', '/api/admin/financial-report');
  console.log('       report after delete:', after);
})().catch((err) => { console.error(err); process.exit(1); });
