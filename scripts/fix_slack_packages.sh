#!/bin/bash
# Fix slack team package build configurations
# These packages have incorrect pyproject.toml that reference a non-existent src/ subdirectory

set -e

echo "Fixing slack package configurations..."

# Detect OS for sed compatibility
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_INPLACE="sed -i ''"
else
    SED_INPLACE="sed -i"
fi

# Fix chat_api
$SED_INPLACE 's/package-dir = {"" = "src"}/package-dir = {"" = "."}/' external/slack_team/src/chat_api/pyproject.toml
$SED_INPLACE 's/where = \["src"\]/where = ["."]/' external/slack_team/src/chat_api/pyproject.toml

# Fix slack_adapter
$SED_INPLACE 's/package-dir = {"" = "src"}/package-dir = {"" = "."}/' external/slack_team/src/slack_adapter/pyproject.toml
$SED_INPLACE 's/where = \["src"\]/where = ["."]/' external/slack_team/src/slack_adapter/pyproject.toml

# Fix slack_api
$SED_INPLACE 's/package-dir = {"" = "src"}/package-dir = {"" = "."}/' external/slack_team/src/slack_api/pyproject.toml
$SED_INPLACE 's/where = \["src"\]/where = ["."]/' external/slack_team/src/slack_api/pyproject.toml

# Fix slack_impl
$SED_INPLACE 's/where = \["src"\]/where = ["."]/' external/slack_team/src/slack_impl/pyproject.toml

# Fix slack_service
$SED_INPLACE 's/package-dir = {"" = "src"}/package-dir = {"" = "."}/' external/slack_team/src/slack_service/pyproject.toml
$SED_INPLACE 's/where = \["src"\]/where = ["."]/' external/slack_team/src/slack_service/pyproject.toml

echo "Slack package configurations fixed"
