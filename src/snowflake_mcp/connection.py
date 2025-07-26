"""Connection management for Snowflake MCP Server."""

import os
from typing import Any, Dict, List, Optional

import snowflake.connector
from cryptography.hazmat.primitives import serialization


class SnowflakeConnection:
    """Manages Snowflake database connections."""

    def __init__(self, connection_name: Optional[str] = None) -> None:
        """Initialize connection manager.
        
        Args:
            connection_name: Name of connection in connections.toml file
        """
        self.connection: Optional[snowflake.connector.SnowflakeConnection] = None
        self.connection_name = connection_name

    def _get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters from environment variables.

        Returns:
            Dict[str, Any]: Connection parameters for Snowflake
        """
        params = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
        }

        # Keypair authentication
        private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
        if private_key_path:
            with open(private_key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "").encode()
                    or None,
                )

            pkb = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            params["private_key"] = pkb

        # OAuth authentication (alternative)
        oauth_token = os.getenv("SNOWFLAKE_OAUTH_TOKEN")
        if oauth_token:
            params["token"] = oauth_token
            params["authenticator"] = "oauth"

        return params

    async def connect(self) -> None:
        """Connect to Snowflake database."""
        if self.connection_name:
            # Use Snowflake connector's native connections.toml support
            self.connection = snowflake.connector.connect(connection_name=self.connection_name)
        else:
            # Use environment variables
            connection_params = self._get_connection_params()
            self.connection = snowflake.connector.connect(**connection_params)

    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results.

        Args:
            query: SQL query string to execute

        Returns:
            List[Dict[str, Any]]: Query results as list of dictionaries
        """
        if not self.connection:
            await self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()

    async def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
