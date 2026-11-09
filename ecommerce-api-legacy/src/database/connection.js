// Conexão SQLite com helpers baseados em Promise e transações serializadas.
const sqlite3 = require('sqlite3');

function openDatabase(filename) {
  const raw = new sqlite3.Database(filename);
  let txQueue = Promise.resolve();

  const run = (sql, params = []) => new Promise((resolve, reject) => {
    raw.run(sql, params, function onRun(err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
    });
  });

  const get = (sql, params = []) => new Promise((resolve, reject) => {
    raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });

  const all = (sql, params = []) => new Promise((resolve, reject) => {
    raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });

  const exec = (sql) => new Promise((resolve, reject) => {
    raw.exec(sql, (err) => (err ? reject(err) : resolve()));
  });

  // Uma conexão só: as transações entram em fila para não se intercalarem.
  const transaction = (work) => {
    const result = txQueue.then(async () => {
      await run('BEGIN IMMEDIATE');
      try {
        const value = await work();
        await run('COMMIT');
        return value;
      } catch (err) {
        await run('ROLLBACK');
        throw err;
      }
    });
    txQueue = result.catch(() => {});
    return result;
  };

  const close = () => new Promise((resolve, reject) => raw.close((err) => (err ? reject(err) : resolve())));

  return { run, get, all, exec, transaction, close };
}

module.exports = { openDatabase };
