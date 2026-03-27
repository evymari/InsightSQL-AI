from typing import Optional

from .query_service import QueryService
from .schema_service import SchemaService

_schema_service: Optional[SchemaService] = None
_query_service: Optional[QueryService] = None


def initialize_services(schema_service: SchemaService, query_service: QueryService) -> None:
    global _schema_service, _query_service
    _schema_service = schema_service
    _query_service = query_service


def get_schema_service() -> Optional[SchemaService]:
    return _schema_service


def get_query_service() -> Optional[QueryService]:
    return _query_service
