from app.registry.db_type_registry import DBTypeDescriptor, register_db_type

register_db_type(
    DBTypeDescriptor(
        canonical_name="postgresql",
        aliases=["postgresql", "postgres", "pg", "psql"],
        display_label="PostgreSQL",
        icon_name="postgresql",
        helm_chart_url="https://gitlab.example.com/PLACEHOLDER/postgresql-helm-chart",
    )
)
