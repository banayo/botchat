-- Collect the real view structure. Do not invent registry columns.
-- Run as EXP_READ or EXPORT_AI.

SELECT
    c.column_id,
    c.column_name,
    c.data_type,
    c.data_length,
    cc.comments
FROM all_tab_columns c
LEFT JOIN all_col_comments cc
       ON cc.owner = c.owner
      AND cc.table_name = c.table_name
      AND cc.column_name = c.column_name
WHERE c.owner = 'KMPROD'
  AND c.table_name = 'EXP$ERP_SALE_REP_EXP'
ORDER BY c.column_id;
