-- Find the marketing view, then collect columns. Do not invent registry names.

SELECT owner, view_name
FROM all_views
WHERE UPPER(view_name) LIKE '%MKT%'
   OR UPPER(view_name) LIKE '%MARKET%'
ORDER BY owner, view_name;

-- After you know owner + view_name, set MKT_VIEW_OWNER / MKT_VIEW_NAME and run:

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
  AND c.table_name = 'MKT$ERP_SALE_REP'
ORDER BY c.column_id;
