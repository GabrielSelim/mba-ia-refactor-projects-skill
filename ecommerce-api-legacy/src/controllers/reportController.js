// Relatório financeiro: agrega em memória o resultado de uma única query.
const { PAYMENT_STATUS } = require('../services/paymentGateway');

const UNKNOWN_STUDENT = 'Unknown';

function buildFinancialReport(rows) {
  const byCourse = new Map();
  for (const row of rows) {
    if (!byCourse.has(row.course_id)) {
      byCourse.set(row.course_id, { course: row.course, revenue: 0, students: [] });
    }
    if (row.enrollment_id === null) continue;
    const entry = byCourse.get(row.course_id);
    if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
    entry.students.push({ student: row.student || UNKNOWN_STUDENT, paid: row.amount || 0 });
  }
  return [...byCourse.values()];
}

function createReportController({ models }) {
  async function financialReport(req, res) {
    res.json(buildFinancialReport(await models.reports.financialRows()));
  }
  return { financialReport };
}

module.exports = { createReportController, buildFinancialReport };
