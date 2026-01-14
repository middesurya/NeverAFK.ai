"""
PRD-023: GraphQL Module

This module provides GraphQL support for the Creator Support AI API.
Includes schema definitions, resolvers, and subscription management.
"""

from app.graphql.schema import (
    GraphQLType,
    Field,
    ObjectType,
    SCHEMA,
    parse_schema,
    validate_query,
    GraphQLError,
    GraphQLValidationError,
)

from app.graphql.resolvers import (
    GraphQLResolver,
    ChatResolver,
    ConversationResolver,
    UserResolver,
    SubscriptionManager,
)

__all__ = [
    "GraphQLType",
    "Field",
    "ObjectType",
    "SCHEMA",
    "parse_schema",
    "validate_query",
    "GraphQLError",
    "GraphQLValidationError",
    "GraphQLResolver",
    "ChatResolver",
    "ConversationResolver",
    "UserResolver",
    "SubscriptionManager",
]
