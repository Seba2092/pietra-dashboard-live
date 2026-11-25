const SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1nRWkUGnENJzFJDowZQDinW1aMvCT7rbFYKKEJ_ud9fw/edit';
const START_DATE = '2026-09-01'; // Fecha fija: nunca pierde histórico al avanzar los días

function getToday() {
  const tz = AdsApp.currentAccount().getTimeZone();
  return Utilities.formatDate(new Date(), tz, 'yyyy-MM-dd');
}

function main() {
  const ss = SpreadsheetApp.openByUrl(SPREADSHEET_URL);
  const endDate = getToday();
  const dateFilter = `segments.date BETWEEN '${START_DATE}' AND '${endDate}'`;

  // 1. Campañas diarias (histórico completo desde START_DATE)
  exportReport(ss, 'Campañas_Diario', `
    SELECT
      segments.date,
      campaign.id,
      campaign.name,
      campaign.advertising_channel_type,
      campaign.status,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.conversions_value
    FROM campaign
    WHERE ${dateFilter}
      AND metrics.impressions > 0
  `);

  // 2. Keywords (Search) con tipo de concordancia
  exportReport(ss, 'Keywords', `
    SELECT
      segments.date,
      campaign.name,
      ad_group_criterion.keyword.text,
      ad_group_criterion.keyword.match_type,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.conversions_value
    FROM keyword_view
    WHERE ${dateFilter}
      AND metrics.impressions > 0
  `);

  // 3. Rangos Etarios (con fecha para filtrar por mes)
  exportReport(ss, 'Edad', `
    SELECT
      segments.date,
      campaign.name,
      ad_group_criterion.age_range.type,
      metrics.clicks,
      metrics.impressions,
      metrics.cost_micros,
      metrics.conversions
    FROM age_range_view
    WHERE ${dateFilter}
      AND metrics.impressions > 0
  `);

  // 4. Productos Shopping / PMax
  exportReport(ss, 'Productos_PMax', `
    SELECT
      segments.date,
      campaign.name,
      segments.product_title,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.conversions_value
    FROM shopping_performance_view
    WHERE ${dateFilter}
      AND metrics.clicks > 0
  `);

  Logger.log('Exportación completa: ' + START_DATE + ' a ' + endDate);
}

function exportReport(ss, sheetName, query) {
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  } else {
    sheet.clearContents();
  }
  const report = AdsApp.report(query);
  report.exportToSheet(sheet);
}
