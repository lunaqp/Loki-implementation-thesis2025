"""Shared asyncio lock for DuckDB access.
DuckDB connections are not safe to use concurrently across async tasks.
"""
import asyncio

duckdb_lock = asyncio.Lock()