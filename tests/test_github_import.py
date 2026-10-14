"""
Unit tests for GitHub import, URL parsing, and repo analysis features.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.github_service import (
    parse_github_url,
    analyze_github_codebase,
    _heuristic_analysis,
)

client = TestClient(app)


def test_parse_github_url_valid():
    owner, repo, branch = parse_github_url("https://github.com/facebook/react")
    assert owner == "facebook"
    assert repo == "react"
    assert branch is None

    owner, repo, branch = parse_github_url("https://github.com/torvalds/linux.git")
    assert owner == "torvalds"
    assert repo == "linux"
    assert branch is None

    owner, repo, branch = parse_github_url("https://github.com/fastapi/fastapi/tree/master")
    assert owner == "fastapi"
    assert repo == "fastapi"
    assert branch == "master"


def test_parse_github_url_invalid():
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/user/project")

    with pytest.raises(ValueError):
        parse_github_url("not-a-url")

    with pytest.raises(ValueError):
        parse_github_url("https://github.com/justonepart")


def test_analyze_github_codebase_heuristic():
    repo_data = {
        "repo_name": "ecommerce-api",
        "description": "An e-commerce backend built with FastAPI, PostgreSQL and Redis",
        "primary_language": "Python",
        "languages": ["Python", "Dockerfile"],
        "readme": "# E-Commerce API\nOnline shopping store backend with user authentication and payment processing.",
        "tree": [
            {"path": "app/main.py", "type": "blob"},
            {"path": "app/routers/auth.py", "type": "blob"},
            {"path": "app/models/orders.py", "type": "blob"},
            {"path": "alembic/versions/init.sql", "type": "blob"},
            {"path": "requirements.txt", "type": "blob"},
        ],
        "dependencies": ["fastapi", "uvicorn", "asyncpg", "sqlalchemy", "redis"],
        "schemas": [
            {"path": "alembic/versions/init.sql", "content": "CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR);"}
        ],
    }

    # Test fallback heuristics directly
    analysis = _heuristic_analysis(
        owner="testuser",
        repo="ecommerce-api",
        desc="An e-commerce backend built with FastAPI, PostgreSQL and Redis",
        readme="# E-Commerce API\nOnline shopping store backend with user authentication and payment processing.",
        deps="fastapi\nuvicorn\nasyncpg\nsqlalchemy\nredis",
        file_list=["app/main.py", "app/routers/auth.py", "app/models/orders.py", "alembic/versions/init.sql"],
        schema_samples="CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR);",
    )
    assert "Ecommerce Api" in analysis["title"]
    assert "Python" in analysis["tech_stack"] or "FastAPI" in analysis["tech_stack"]
    assert len(analysis["modules"]) > 0
    assert analysis["database_used"] != ""


def test_analyze_github_endpoint_invalid_url():
    # Malformed URL returns 400 Bad Request with descriptive message
    response = client.post("/api/v1/projects/analyze-github", json={"github_url": "invalid-url"})
    assert response.status_code == 400
    assert "Invalid GitHub repository URL" in response.json()["detail"]

    # Non-GitHub URL returns 400 Bad Request
    response = client.post("/api/v1/projects/analyze-github", json={"url": "https://gitlab.com/user/project"})
    assert response.status_code == 400


def test_parse_sql_ddl():
    from app.services.github_service import parse_sql_ddl

    sql = """
    CREATE TABLE customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL
    );

    CREATE TABLE invoices (
        invoice_id INT PRIMARY KEY,
        customer_id INT REFERENCES customers(id),
        total DECIMAL(10, 2) NOT NULL
    );
    """
    res = parse_sql_ddl(sql)
    assert len(res["tables"]) == 2
    assert res["tables"][0]["table_name"] == "customers"
    assert res["tables"][1]["table_name"] == "invoices"
    assert len(res["relationships"]) == 1
    assert res["relationships"][0]["from_table"] == "invoices"
    assert res["relationships"][0]["to_table"] == "customers"
    assert "Data Dictionary" in res["data_dictionary_md"]


@pytest.mark.asyncio
async def test_diagram_generation_and_serving():
    from app.services.diagram_service import generate_diagram_image

    url, path = await generate_diagram_image(
        project_id="test_proj_diag",
        diagram_type="ch3_architecture_diagram",
        prompt="System Architecture Diagram",
        title="Test System"
    )
    assert path.exists()
    assert url.startswith("/api/v1/diagrams/test_proj_diag/")

    # Test serving via API endpoint
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

