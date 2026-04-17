from app.registry.db_type_registry import DBTypeDescriptor, register_db_type

register_db_type(
    DBTypeDescriptor(
        canonical_name="mongodb",
        aliases=["mongodb", "mongo"],
        display_label="MongoDB",
        icon_name="mongodb",
        helm_chart_url="https://gitlab.example.com/PLACEHOLDER/mongodb-helm-chart",
    )
)
