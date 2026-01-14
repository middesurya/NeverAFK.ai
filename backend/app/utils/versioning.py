"""
API versioning utilities.
Provides version detection, validation, and deprecation handling.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Set
from enum import Enum
import re


class APIVersion(Enum):
    """
    API version enum.

    Represents supported API versions with deprecation status.
    """
    V1 = "v1"
    V2 = "v2"

    @property
    def is_deprecated(self) -> bool:
        """Check if this version is deprecated."""
        return self in DEPRECATED_VERSIONS


@dataclass
class VersionInfo:
    """
    Information about an API version.

    Attributes:
        version: The API version
        deprecated: Whether this version is deprecated
        sunset_date: Optional date when this version will be removed
    """
    version: APIVersion
    deprecated: bool = False
    sunset_date: Optional[str] = None

    def __eq__(self, other):
        if not isinstance(other, VersionInfo):
            return False
        return (
            self.version == other.version and
            self.deprecated == other.deprecated and
            self.sunset_date == other.sunset_date
        )


# Current version (latest stable)
CURRENT_VERSION = APIVersion.V2

# Default version when not specified
DEFAULT_VERSION = APIVersion.V2

# Set of all supported versions
SUPPORTED_VERSIONS: Set[APIVersion] = {APIVersion.V1, APIVersion.V2}

# Set of deprecated versions
DEPRECATED_VERSIONS: Set[APIVersion] = {APIVersion.V1}

# Sunset dates for deprecated versions (ISO 8601 format)
VERSION_SUNSET_DATES: Dict[APIVersion, str] = {
    APIVersion.V1: "2025-12-31"
}

# Version path patterns
VERSION_PATH_PATTERN = re.compile(r'^/v(\d+)(?:/|$)')


def parse_version_string(version_str: Optional[str]) -> Optional[APIVersion]:
    """
    Parse a version string into an APIVersion enum.

    Args:
        version_str: Version string like 'v1', 'v2', 'V1', etc.

    Returns:
        APIVersion if valid, None otherwise
    """
    if version_str is None:
        return None

    version_str = version_str.strip().lower()

    if not version_str:
        return None

    try:
        return APIVersion(version_str)
    except ValueError:
        return None


def extract_version(path: str, headers: Dict[str, str]) -> APIVersion:
    """
    Extract API version from request path or headers.

    Priority:
    1. URL path (/v1/..., /v2/...)
    2. Accept-Version header
    3. X-API-Version header
    4. API-Version header
    5. Default version

    Args:
        path: Request URL path
        headers: Request headers (case-insensitive keys)

    Returns:
        Detected APIVersion, defaults to DEFAULT_VERSION
    """
    # Normalize headers to lowercase keys
    normalized_headers = {k.lower(): v for k, v in headers.items()}

    # 1. Check path first: /v1/resource, /v2/resource
    if path:
        # Match exact /v1 or /v2 at start of path
        if path.startswith("/v2"):
            # Ensure it's /v2 and not /v20 etc
            if len(path) == 3 or path[3] == '/':
                return APIVersion.V2
        if path.startswith("/v1"):
            # Ensure it's /v1 and not /v10 etc
            if len(path) == 3 or path[3] == '/':
                return APIVersion.V1

    # 2. Check Accept-Version header
    accept_version = normalized_headers.get("accept-version")
    if accept_version:
        parsed = parse_version_string(accept_version)
        if parsed:
            return parsed

    # 3. Check X-API-Version header
    x_api_version = normalized_headers.get("x-api-version")
    if x_api_version:
        parsed = parse_version_string(x_api_version)
        if parsed:
            return parsed

    # 4. Check API-Version header
    api_version = normalized_headers.get("api-version")
    if api_version:
        parsed = parse_version_string(api_version)
        if parsed:
            return parsed

    # 5. Return default version
    return DEFAULT_VERSION


def is_version_supported(version: APIVersion) -> bool:
    """
    Check if a version is currently supported.

    Args:
        version: The API version to check

    Returns:
        True if version is supported, False otherwise
    """
    return version in SUPPORTED_VERSIONS


def get_version_info(version: APIVersion) -> VersionInfo:
    """
    Get detailed information about an API version.

    Args:
        version: The API version

    Returns:
        VersionInfo with version details
    """
    return VersionInfo(
        version=version,
        deprecated=version in DEPRECATED_VERSIONS,
        sunset_date=VERSION_SUNSET_DATES.get(version)
    )


def get_deprecation_message(version: APIVersion) -> Optional[str]:
    """
    Get deprecation warning message for a version.

    Args:
        version: The API version

    Returns:
        Deprecation message if version is deprecated, None otherwise
    """
    if version not in DEPRECATED_VERSIONS:
        return None

    sunset_date = VERSION_SUNSET_DATES.get(version)

    if sunset_date:
        return (
            f"API version {version.value} is deprecated and will be removed on {sunset_date}. "
            f"Please migrate to {CURRENT_VERSION.value}."
        )
    else:
        return (
            f"API version {version.value} is deprecated. "
            f"Please migrate to {CURRENT_VERSION.value}."
        )


def get_supported_versions() -> Set[APIVersion]:
    """
    Get set of all supported API versions.

    Returns:
        Set of supported APIVersion values
    """
    return SUPPORTED_VERSIONS.copy()


def get_deprecated_versions() -> Set[APIVersion]:
    """
    Get set of deprecated API versions.

    Returns:
        Set of deprecated APIVersion values
    """
    return DEPRECATED_VERSIONS.copy()


def is_version_deprecated(version: APIVersion) -> bool:
    """
    Check if a version is deprecated.

    Args:
        version: The API version to check

    Returns:
        True if version is deprecated, False otherwise
    """
    return version in DEPRECATED_VERSIONS


__all__ = [
    "APIVersion",
    "VersionInfo",
    "extract_version",
    "parse_version_string",
    "is_version_supported",
    "get_version_info",
    "get_deprecation_message",
    "get_supported_versions",
    "get_deprecated_versions",
    "is_version_deprecated",
    "CURRENT_VERSION",
    "DEFAULT_VERSION",
    "SUPPORTED_VERSIONS",
    "DEPRECATED_VERSIONS",
    "VERSION_SUNSET_DATES",
]
