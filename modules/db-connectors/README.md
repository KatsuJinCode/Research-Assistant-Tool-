# Research Assistant DB Connectors

Database connection abstractions and implementations for the Research Assistant Tool platform with support for both synchronous and asynchronous PostgreSQL operations.

## Features

- **Abstract Interfaces** - DatabaseInterface and AsyncDatabaseInterface for decoupling
- **PostgreSQL Support** - Both sync (psycopg2) and async (asyncpg) implementations
- **Connection Pooling** - Async connector uses connection pooling for performance
- **Transaction Support** - Manual and automatic transaction management
- **Context Managers** - Clean resource management with `with` statements
- **Type Safety** - Full type hints for all methods
- **Comprehensive Testing** - 50+ tests with mocking

## Installation

```bash
cd modules/db-connectors
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Usage

### Synchronous PostgreSQL

```python
from research_assistant_db import PostgreSQLConnector

# Create connector
db = PostgreSQLConnector(
    host="localhost",
    port=5432,
    database="research_db",
    user="research_user",
    password="secret"
)

# Connect
db.connect()

# Execute query
db.execute("INSERT INTO users (name, email) VALUES (%s, %s)",
           params=("Alice", "alice@example.com"))

# Fetch data
users = db.fetch_all("SELECT * FROM users WHERE active = %s", params=(True,))
for user in users:
    print(user["name"], user["email"])

# Fetch single row
user = db.fetch_one("SELECT * FROM users WHERE id = %s", params=(1,))

# Disconnect
db.disconnect()
```

### Context Manager (Recommended)

```python
from research_assistant_db import PostgreSQLConnector

with PostgreSQLConnector(host="localhost", port=5432, database="research_db",
                         user="user", password="pass") as db:
    # Use database
    users = db.fetch_all("SELECT * FROM users")

# Automatically disconnected
```

### Transactions

```python
from research_assistant_db import PostgreSQLConnector

db = PostgreSQLConnector(**config)

# Manual transaction control
with db.transaction() as tx:
    db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = %s", (1,))
    db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = %s", (2,))

    # Explicitly commit
    tx.commit()

# Auto-commit (if no manual commit/rollback)
with db.transaction():
    db.execute("INSERT INTO logs (message) VALUES (%s)", ("Transaction started",))
    # Automatically commits on exit

# Auto-rollback on exception
try:
    with db.transaction():
        db.execute("INSERT INTO users (name) VALUES (%s)", ("Bob",))
        raise ValueError("Something went wrong")
        # Never reaches here
except ValueError:
    pass  # Transaction automatically rolled back
```

### Asynchronous PostgreSQL

```python
import asyncio
from research_assistant_db import AsyncPostgreSQLConnector

async def main():
    # Create async connector with connection pooling
    db = AsyncPostgreSQLConnector(
        host="localhost",
        port=5432,
        database="research_db",
        user="research_user",
        password="secret",
        min_pool_size=10,
        max_pool_size=20
    )

    # Connect (creates connection pool)
    await db.connect()

    # Execute query
    await db.execute(
        "INSERT INTO users (name, email) VALUES ($1, $2)",
        params=("Alice", "alice@example.com")
    )

    # Fetch data
    users = await db.fetch_all("SELECT * FROM users WHERE active = $1", params=(True,))
    for user in users:
        print(user["name"], user["email"])

    # Fetch single row
    user = await db.fetch_one("SELECT * FROM users WHERE id = $1", params=(1,))

    # Disconnect (closes pool)
    await db.disconnect()

# Run
asyncio.run(main())
```

### Async Context Manager

```python
import asyncio
from research_assistant_db import AsyncPostgreSQLConnector

async def main():
    async with AsyncPostgreSQLConnector(**config) as db:
        users = await db.fetch_all("SELECT * FROM users")
        # Use database
    # Automatically disconnected

asyncio.run(main())
```

### Async Transactions

```python
import asyncio
from research_assistant_db import AsyncPostgreSQLConnector

async def transfer_funds(db, from_id, to_id, amount):
    async with db.transaction() as tx:
        await db.execute(
            "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
            (amount, from_id)
        )
        await db.execute(
            "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
            (amount, to_id)
        )

        # Explicitly commit
        await tx.commit()

async def main():
    async with AsyncPostgreSQLConnector(**config) as db:
        await transfer_funds(db, from_id=1, to_id=2, amount=100)

asyncio.run(main())
```

### Execute Many (Bulk Operations)

```python
# Sync
db = PostgreSQLConnector(**config)
users_data = [
    ("Alice", "alice@example.com"),
    ("Bob", "bob@example.com"),
    ("Charlie", "charlie@example.com"),
]
db.execute_many(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    users_data
)

# Async
async def bulk_insert():
    async with AsyncPostgreSQLConnector(**config) as db:
        users_data = [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
        ]
        await db.execute_many(
            "INSERT INTO users (name, email) VALUES ($1, $2)",
            users_data
        )
```

### Health Checks

```python
# Sync ping
db = PostgreSQLConnector(**config)
if db.ping():
    print("✓ Database is alive")
else:
    print("✗ Database is unreachable")

# Async ping
async def check_health():
    async with AsyncPostgreSQLConnector(**config) as db:
        is_alive = await db.ping()
        print("✓ Database is alive" if is_alive else "✗ Database is unreachable")
```

## API Reference

### DatabaseInterface (Abstract Base Class)

**Methods:**
- `connect() -> None` - Establish database connection
- `disconnect() -> None` - Close database connection
- `is_connected() -> bool` - Check if connected
- `execute(query, params=None, fetch=False)` - Execute query
- `execute_many(query, params_list)` - Execute with multiple parameter sets
- `fetch_one(query, params=None)` - Fetch single row
- `fetch_all(query, params=None)` - Fetch all rows
- `transaction()` - Context manager for transactions
- `ping() -> bool` - Check database connectivity

### PostgreSQLConnector

Synchronous PostgreSQL connector using psycopg2.

**Constructor:**
```python
PostgreSQLConnector(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    **kwargs  # Additional psycopg2 connection parameters
)
```

**Features:**
- Uses `RealDictCursor` for dict-based results
- Auto-reconnection on queries if disconnected
- Transaction support with auto-commit/rollback
- Context manager support

### AsyncPostgreSQLConnector

Asynchronous PostgreSQL connector using asyncpg with connection pooling.

**Constructor:**
```python
AsyncPostgreSQLConnector(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    min_pool_size: int = 10,
    max_pool_size: int = 20,
    **kwargs  # Additional asyncpg connection parameters
)
```

**Features:**
- Connection pooling for high performance
- Async/await support
- Transaction support with auto-commit/rollback
- Async context manager support

**Note:** asyncpg uses `$1`, `$2` placeholders instead of `%s`:
```python
# psycopg2 (sync)
db.execute("SELECT * FROM users WHERE id = %s", (1,))

# asyncpg (async)
await db.execute("SELECT * FROM users WHERE id = $1", (1,))
```

### TransactionContext

**Methods:**
- `commit() -> None` - Commit the transaction (async: `await tx.commit()`)
- `rollback() -> None` - Rollback the transaction (async: `await tx.rollback()`)

## Development

### Running Tests

```bash
pytest
```

### Test Coverage

```bash
pytest --cov
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Examples

### Example 1: Simple CRUD Operations

```python
from research_assistant_db import PostgreSQLConnector

with PostgreSQLConnector(**config) as db:
    # Create
    db.execute(
        "INSERT INTO documents (title, content) VALUES (%s, %s)",
        ("Research Paper", "Content here...")
    )

    # Read
    docs = db.fetch_all("SELECT * FROM documents ORDER BY created_at DESC")

    # Update
    db.execute(
        "UPDATE documents SET title = %s WHERE id = %s",
        ("Updated Title", 1)
    )

    # Delete
    db.execute("DELETE FROM documents WHERE id = %s", (1,))
```

### Example 2: Complex Async Operations

```python
import asyncio
from research_assistant_db import AsyncPostgreSQLConnector

async def process_documents(db, user_id):
    """Process documents for a user."""
    # Fetch user's documents
    docs = await db.fetch_all(
        "SELECT * FROM documents WHERE user_id = $1",
        (user_id,)
    )

    # Process each document
    for doc in docs:
        async with db.transaction():
            # Update processing status
            await db.execute(
                "UPDATE documents SET status = $1 WHERE id = $2",
                ("processing", doc["id"])
            )

            # Create processing record
            await db.execute(
                "INSERT INTO processing_logs (doc_id, started_at) VALUES ($1, NOW())",
                (doc["id"],)
            )

            # Simulate processing
            await asyncio.sleep(0.1)

            # Mark complete
            await db.execute(
                "UPDATE documents SET status = $1 WHERE id = $2",
                ("completed", doc["id"])
            )

async def main():
    async with AsyncPostgreSQLConnector(**config) as db:
        # Process documents for multiple users concurrently
        await asyncio.gather(
            process_documents(db, user_id=1),
            process_documents(db, user_id=2),
            process_documents(db, user_id=3),
        )

asyncio.run(main())
```

### Example 3: Error Handling and Retries

```python
from research_assistant_db import PostgreSQLConnector
import time

def insert_with_retry(db, data, max_retries=3):
    """Insert data with retry logic."""
    for attempt in range(max_retries):
        try:
            with db.transaction() as tx:
                db.execute(
                    "INSERT INTO logs (message, level) VALUES (%s, %s)",
                    data
                )
                tx.commit()
                return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

    return False

# Usage
with PostgreSQLConnector(**config) as db:
    success = insert_with_retry(db, ("Application started", "INFO"))
    if success:
        print("✓ Data inserted successfully")
```

### Example 4: Using with Config Module

```python
from research_assistant_config import load_config
from research_assistant_db import PostgreSQLConnector

# Load configuration
config = load_config("config/config.yaml")

# Create database connector from config
db = PostgreSQLConnector(
    host=config.database.host,
    port=config.database.port,
    database=config.database.name,
    user=config.database.user,
    password=config.database.password,
)

# Or use connection string
import psycopg2
conn = psycopg2.connect(config.database.connection_string)
```

## Best Practices

1. **Always use context managers** - Ensures proper cleanup
   ```python
   # ✓ Good
   with PostgreSQLConnector(**config) as db:
       users = db.fetch_all("SELECT * FROM users")

   # ✗ Bad
   db = PostgreSQLConnector(**config)
   db.connect()
   users = db.fetch_all("SELECT * FROM users")
   # Might forget to disconnect
   ```

2. **Use transactions for multi-step operations**
   ```python
   with db.transaction():
       db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
       db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
   ```

3. **Use async for I/O-heavy workloads**
   ```python
   # If you have many concurrent database operations, use async
   async with AsyncPostgreSQLConnector(**config) as db:
       results = await asyncio.gather(
           db.fetch_all("SELECT * FROM table1"),
           db.fetch_all("SELECT * FROM table2"),
           db.fetch_all("SELECT * FROM table3"),
       )
   ```

4. **Always use parameterized queries** - Prevents SQL injection
   ```python
   # ✓ Good - parameterized
   db.execute("SELECT * FROM users WHERE email = %s", (email,))

   # ✗ Bad - SQL injection risk
   db.execute(f"SELECT * FROM users WHERE email = '{email}'")
   ```

5. **Check connectivity before critical operations**
   ```python
   if not db.ping():
       db.connect()  # Reconnect if needed
   ```

## License

MIT
