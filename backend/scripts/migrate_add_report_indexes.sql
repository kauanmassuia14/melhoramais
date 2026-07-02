-- migrate_add_report_indexes.sql
-- Cria o índice funcional no PostgreSQL para otimizar buscas do relatório customizado (/reports/generate)
-- Utiliza sintaxe de subscripting compatível com a compilação padrão do SQLAlchemy no PostgreSQL 14+

CREATE INDEX IF NOT EXISTS idx_eval_metrics_pd_dep_float
ON genetics.genetic_evaluations (
    (
        COALESCE(
            (metrics['PD-EDg'] ->> 'dep')::double precision,
            (metrics['DP210'] ->> 'dep')::double precision,
            (metrics['DP120'] ->> 'dep')::double precision
        )
    )
);
