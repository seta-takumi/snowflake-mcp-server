"""Main entry point for Snowflake MCP Server."""

import argparse
from snowflake_mcp_server.server import create_snowflake_mcp_server


def main() -> None:
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Snowflake MCP Server")
    parser.add_argument(
        "--connection-name",
        "-c",
        type=str,
        help="Connection name from connections.toml file",
    )

    args = parser.parse_args()

    # Create and run server with connection name
    mcp = create_snowflake_mcp_server(connection_name=args.connection_name)
    mcp.run()


if __name__ == "__main__":
    main()
