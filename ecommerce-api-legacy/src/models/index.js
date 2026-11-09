// Models: acesso a dados com SQL parametrizado, um objeto por entidade.
function createUserModel(db) {
  return {
    findByEmail: (email) => db.get('SELECT id, name, email FROM users WHERE email = ?', [email]),
    findById: (id) => db.get('SELECT id, name, email FROM users WHERE id = ?', [id]),
    async create({ name, email, passwordHash }) {
      const { lastID } = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
      return lastID;
    },
    deleteById: (id) => db.run('DELETE FROM users WHERE id = ?', [id]),
  };
}

function createCourseModel(db) {
  return {
    findActiveById: (id) => db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [id]),
  };
}

function createEnrollmentModel(db) {
  return {
    async create({ userId, courseId }) {
      const { lastID } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
      return lastID;
    },
    deleteByUser: (userId) => db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]),
  };
}

function createPaymentModel(db) {
  return {
    create: ({ enrollmentId, amount, status }) =>
      db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollmentId, amount, status]),
    deleteByUser: (userId) =>
      db.run('DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)', [userId]),
  };
}

function createAuditLogModel(db) {
  return {
    record: (action) => db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]),
  };
}

function createReportModel(db) {
  return {
    // Uma única query no lugar de 1 + C + 2×M queries (N+1).
    financialRows: () => db.all(`
      SELECT c.id AS course_id, c.title AS course, e.id AS enrollment_id,
             u.name AS student, p.amount, p.status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.enrollment_id = e.id
      ORDER BY c.id, e.id`),
  };
}

function createModels(db) {
  return {
    users: createUserModel(db),
    courses: createCourseModel(db),
    enrollments: createEnrollmentModel(db),
    payments: createPaymentModel(db),
    auditLogs: createAuditLogModel(db),
    reports: createReportModel(db),
  };
}

module.exports = { createModels };
