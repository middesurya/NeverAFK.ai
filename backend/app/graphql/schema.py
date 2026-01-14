"""
PRD-023: GraphQL Schema Definition

Defines the GraphQL schema for the Creator Support AI API.
Includes type definitions, input types, and schema parsing utilities.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import re


class GraphQLType(Enum):
    """GraphQL operation types."""
    QUERY = "Query"
    MUTATION = "Mutation"
    SUBSCRIPTION = "Subscription"


@dataclass
class Field:
    """Represents a GraphQL field definition."""
    name: str
    type: str
    args: Optional[Dict[str, str]] = None
    nullable: bool = True
    description: Optional[str] = None


@dataclass
class ObjectType:
    """Represents a GraphQL object type definition."""
    name: str
    fields: List[Field]
    description: Optional[str] = None


# GraphQL Schema Definition
SCHEMA = '''
type Query {
    chat(message: String!, creatorId: String!): ChatResponse
    conversations(userId: String!): [Conversation]
    conversation(id: String!): Conversation
    user(id: String!): User
}

type Mutation {
    sendMessage(input: SendMessageInput!): ChatResponse
    createConversation(creatorId: String!): Conversation
    deleteConversation(id: String!): Boolean
}

type Subscription {
    conversationUpdated(conversationId: String!): ConversationUpdate
    newMessage(creatorId: String!): Message
}

type ChatResponse {
    response: String!
    sources: [Source]
    shouldEscalate: Boolean
    conversationId: String
}

type Conversation {
    id: String!
    creatorId: String!
    messages: [Message]
    createdAt: String
    updatedAt: String
}

type Message {
    id: String!
    role: String!
    content: String!
    timestamp: String
}

type Source {
    title: String!
    score: Float
    excerpt: String
}

type User {
    id: String!
    email: String
    name: String
    creditsRemaining: Int
}

type ConversationUpdate {
    type: String!
    conversationId: String!
    message: Message
}

input SendMessageInput {
    message: String!
    creatorId: String!
    conversationId: String
}
'''


class GraphQLError(Exception):
    """Base exception for GraphQL errors."""

    def __init__(
        self,
        message: str,
        path: Optional[List[str]] = None,
        locations: Optional[List[Dict[str, int]]] = None,
        extensions: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.path = path or []
        self.locations = locations or []
        self.extensions = extensions or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        error_dict = {"message": self.message}
        if self.path:
            error_dict["path"] = self.path
        if self.locations:
            error_dict["locations"] = self.locations
        if self.extensions:
            error_dict["extensions"] = self.extensions
        return error_dict

    def __str__(self) -> str:
        return self.message


class GraphQLValidationError(GraphQLError):
    """Exception raised for GraphQL validation errors."""

    def __init__(
        self,
        message: str,
        path: Optional[List[str]] = None,
        field_name: Optional[str] = None
    ):
        super().__init__(message, path)
        self.field_name = field_name


def parse_schema(schema_string: str) -> Dict[str, Any]:
    """
    Parse a GraphQL schema string into a structured dictionary.

    Args:
        schema_string: The GraphQL schema definition string.

    Returns:
        Dictionary containing parsed type definitions with their fields.
    """
    result: Dict[str, Any] = {}

    # Pattern to match type definitions
    type_pattern = r'type\s+(\w+)\s*\{([^}]+)\}'

    # Find all type definitions
    type_matches = re.findall(type_pattern, schema_string, re.DOTALL)

    for type_name, type_body in type_matches:
        fields: Dict[str, Any] = {}

        # Pattern to match field definitions
        field_pattern = r'(\w+)(?:\(([^)]*)\))?\s*:\s*(\[?\w+!?\]?!?)'

        field_matches = re.findall(field_pattern, type_body)

        for field_name, args_str, field_type in field_matches:
            field_info: Dict[str, Any] = {
                "type": field_type,
                "nullable": not field_type.endswith("!")
            }

            if args_str:
                # Parse arguments
                args: Dict[str, str] = {}
                arg_pattern = r'(\w+)\s*:\s*(\w+!?)'
                arg_matches = re.findall(arg_pattern, args_str)
                for arg_name, arg_type in arg_matches:
                    args[arg_name] = arg_type
                field_info["args"] = args

            fields[field_name] = field_info

        result[type_name] = {"fields": fields}

    # Parse input types
    input_pattern = r'input\s+(\w+)\s*\{([^}]+)\}'
    input_matches = re.findall(input_pattern, schema_string, re.DOTALL)

    for input_name, input_body in input_matches:
        fields = {}
        field_pattern = r'(\w+)\s*:\s*(\[?\w+!?\]?!?)'
        field_matches = re.findall(field_pattern, input_body)

        for field_name, field_type in field_matches:
            fields[field_name] = {
                "type": field_type,
                "nullable": not field_type.endswith("!")
            }

        result[input_name] = {"fields": fields, "is_input": True}

    return result


def validate_query(query: str, strict: bool = False) -> bool:
    """
    Validate a GraphQL query string.

    Args:
        query: The GraphQL query string to validate.
        strict: If True, raises exceptions for validation errors.

    Returns:
        True if the query is valid.

    Raises:
        GraphQLValidationError: If strict is True and validation fails.
    """
    if not query or not query.strip():
        if strict:
            raise GraphQLValidationError("Query cannot be empty")
        return False

    # Parse the schema to get valid fields
    parsed_schema = parse_schema(SCHEMA)
    query_fields = parsed_schema.get("Query", {}).get("fields", {})
    mutation_fields = parsed_schema.get("Mutation", {}).get("fields", {})

    # Check for operation type
    is_query = "query" in query.lower()
    is_mutation = "mutation" in query.lower()

    if not is_query and not is_mutation:
        if strict:
            raise GraphQLValidationError("Query must specify operation type")
        return False

    # Extract field names from query
    field_pattern = r'(\w+)\s*(?:\([^)]*\))?\s*\{'
    requested_fields = re.findall(field_pattern, query)

    # Skip operation keywords
    operation_keywords = {'query', 'mutation', 'subscription'}
    requested_fields = [f for f in requested_fields if f.lower() not in operation_keywords]

    if strict:
        for field_name in requested_fields:
            if is_query and field_name not in query_fields:
                if field_name not in mutation_fields:
                    raise GraphQLValidationError(
                        f"Invalid field: {field_name}",
                        field_name=field_name
                    )
            elif is_mutation and field_name not in mutation_fields:
                if field_name not in query_fields:
                    raise GraphQLValidationError(
                        f"Invalid field: {field_name}",
                        field_name=field_name
                    )

        # Validate required arguments for known fields
        for field_name in requested_fields:
            field_def = query_fields.get(field_name) or mutation_fields.get(field_name)
            if field_def and field_def.get("args"):
                required_args = [
                    arg_name for arg_name, arg_type in field_def["args"].items()
                    if arg_type.endswith("!")
                ]
                if required_args:
                    # Check if arguments are provided in query
                    arg_check_pattern = rf'{field_name}\s*\(([^)]*)\)'
                    arg_match = re.search(arg_check_pattern, query)
                    if not arg_match:
                        raise GraphQLValidationError(
                            f"Missing required arguments for {field_name}: {required_args}",
                            field_name=field_name
                        )

    return True


def get_type_definition(type_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the definition of a type from the schema.

    Args:
        type_name: Name of the type to look up.

    Returns:
        Dictionary containing the type definition, or None if not found.
    """
    parsed = parse_schema(SCHEMA)
    return parsed.get(type_name)


def get_field_definition(type_name: str, field_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the definition of a field within a type.

    Args:
        type_name: Name of the parent type.
        field_name: Name of the field to look up.

    Returns:
        Dictionary containing the field definition, or None if not found.
    """
    type_def = get_type_definition(type_name)
    if type_def:
        return type_def.get("fields", {}).get(field_name)
    return None
