# Satoshi AI

AI-powered content management system with Supabase authentication and security for internal company tooling, featuring meeting summaries, Discord integration, and AI-assisted tweet generation.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/NiftyLeague/satoshi-ai.git
cd satoshi-ai

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode with test and dev dependencies
pip install -e ".[test,dev]"

# Install Node.js dependencies
pnpm install:all

# Set up Git hooks
pnpm prepare

# Start development services
docker-compose up -d
```

### Development Setup

```bash
# Install test dependencies only
pip install -e ".[test]"

# Install all dependencies (including development tools)
pip install -e ".[test,dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=backend --cov-report=term-missing
```

### Dependency Management

This project uses `pyproject.toml` for dependency management. All Python dependencies are specified there, including:

- **Core Dependencies**: Required for production
- **Test Dependencies**: For running tests (pytest, coverage, etc.)
- **Dev Dependencies**: Development tools (black, isort, mypy, etc.)

To add a new dependency:

1. Add it to the appropriate section in `pyproject.toml`
2. Run `pip install -e ".[test,dev]"` to update your environment

## 📦 Project Structure

```
satoshi-ai/
├── backend/                # Backend services (FastAPI)
│   ├── api_gateway/        # API Gateway
│   └── services/           # Microservices
│       ├── ai/             # AI content generation
│       ├── core/           # Shared / core services
│       ├── discord/        # Discord integration
│       ├── meet/           # Google Meet integration
│       └── twitter/        # Twitter API integration
├── frontend/               # Next.js frontend app
├── infra/                  # Infrastructure as Code
│   ├── docker/             # Docker configurations
│   ├── k8s/                # Kubernetes manifests
│   ├── supabase/           # Supabase migrations
│   └── terraform/          # Terraform configurations
├── scripts                 # General utils/helpers
└── tests                   # Integration/Unit Tests
```

## 🛠 Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- pnpm

## 🧪 Running Tests

The project includes comprehensive tests including unit, integration, and end-to-end tests.

### Test Types

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interactions between components and services
- **E2E Tests**: Test complete user flows
- **Supabase Tests**: Test Supabase integration including authentication and database operations

### Running Tests

#### 1. Local Testing (Recommended for Development)

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test file
pytest tests/path/to/test_file.py

# Run tests with coverage report
pytest --cov=backend --cov-report=term-missing
```

#### 2. Docker-based Testing (For Integration Tests)

For tests requiring external services (like databases or other microservices), use Docker Compose:

```bash
# Run all tests with Docker
./scripts/run_tests.sh --docker

# Keep containers running after tests (for debugging)
./scripts/run_tests.sh --docker --keep-containers

# Stop and remove test containers manually (if needed)
docker-compose -f infra/docker-compose.yml -f tests/docker-compose.test.yml down
```

#### 3. Supabase Integration Tests

```bash
# Run all Supabase tests
pytest tests/supabase

# Run specific test categories
pytest tests/supabase/test_auth.py       # Authentication tests
pytest tests/supabase/test_database.py   # Database operation tests
pytest tests/supabase/test_security.py   # RLS policy tests
pytest tests/supabase/test_edge_cases.py # Edge case tests

# Run with coverage
pytest --cov=backend.supabase tests/supabase/
```

### Test Configuration

- Test database: `satoshi_test` (runs on port 5433 to avoid conflicts)
- Test services run on different ports to avoid conflicts with development services
- Test coverage reports are generated in the `htmlcov` directory

# Run with verbose output

python -m pytest -v tests/supabase

````

#### Test Database Setup

The tests automatically set up the required database tables and RLS policies. You can also manually set up the test database using:

```bash
# Apply the SQL setup script to your Supabase project
psql -h <your-supabase-host> -U postgres -d postgres -f scripts/setup_test_db.sql
````

## 🔐 Authentication

This project uses Supabase for authentication and security features:

### Setup

1. Make sure your `.env.local` file contains the necessary Supabase credentials:

   ```
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   ```

2. The authentication system includes:

   - User signup with email verification
   - Login/logout functionality
   - Password reset flow
   - Protected routes via middleware
   - Role-based access control
   - Audit logging for security events

3. Security features:
   - Row Level Security (RLS) policies
   - Email verification requirements
   - Password strength validation
   - Secure HTTP headers

### Installation

1. **Python Dependencies**

   ```bash
   # Using python3 (Linux/macOS) or python (Windows)
   python3 -m pip install -r requirements-dev.txt
   ```

2. **Node.js Dependencies**

   ```bash
   # Install all dependencies (root + frontend)
   pnpm install:all

   # Or install separately
   pnpm install              # Root dependencies
   pnpm install:frontend     # Frontend dependencies
   ```

3. **Environment Variables**

   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Git Hooks**
   ```bash
   pnpm prepare  # Sets up Husky git hooks
   ```

## 🛠 Development Workflow

### Available Scripts

```bash
# Install all dependencies
pnpm install:all

# Start development servers
docker-compose up -d

# Start frontend development server
pnpm dev

# Or run frontend commands directly
pnpm --prefix frontend [command]
```

### Code Quality

- **Formatting**:

  - JavaScript/TypeScript: Prettier
  - Python: Black

- **Linting**:

  - JavaScript/TypeScript: ESLint
  - Python: Ruff

- **Type Checking**:
  - TypeScript: Built-in
  - Python: mypy (optional)

### Git Hooks

Automatically runs on commit:

- Code formatting with Prettier and Black
- Linting with ESLint and Ruff
- Type checking for TypeScript files

## 🔧 IDE Setup

### VS Code (Recommended)

**Extensions:**

- [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [EditorConfig](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig)
- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter)
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

**Settings (`settings.json`):**

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

## 🚨 Troubleshooting

### Common Issues

**Pre-commit hooks failing**
pnpm run format

````

### Manual Commands

- Format all files: `pnpm format:all` (root)
- Format Python files: `pnpm format:python` (root)
- Run frontend validation: `pnpm frontend:validate` (root)
- Run pre-commit checks manually: `pre-commit run --all-files`

## Deployment

### Local Development

```bash
docker-compose up -d
````

### Production

For production deployment, use the provided Kubernetes manifests or Terraform configurations in the `infra/` directory.

## IDE Setup

### VS Code

Recommended extensions:

- Prettier
- ESLint
- Python
- EditorConfig
- Black Formatter
- Ruff

### PyCharm/IntelliJ

- Enable Black as the default formatter for Python
- Install the Prettier plugin
- Enable ESLint integration

## Troubleshooting

- If pre-commit hooks fail, you can skip them with `git commit --no-verify` (use with caution)
- To update pre-commit hooks: `pre-commit autoupdate`
- To run hooks on all files: `pre-commit run --all-files`
- If you get "command not found" errors, ensure you've run `pnpm install` in both root and frontend directories

## License

GNU General Public License v3.0
