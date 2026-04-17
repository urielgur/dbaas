from app.registry.db_type_registry import DBTypeDescriptor, register_db_type

register_db_type(
    DBTypeDescriptor(
        canonical_name="elasticsearch",
        aliases=["elasticsearch", "elastic", "es", "opensearch"],
        display_label="Elasticsearch",
        icon_name="elasticsearch",
        helm_chart_url="https://gitlab.example.com/PLACEHOLDER/elasticsearch-helm-chart",
    )
)
