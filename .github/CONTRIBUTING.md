# Contributing to Satoshi AI

Thank you for your interest in contributing to Satoshi AI! Here's how you can help:

## Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/NiftyLeague/satoshi-ai.git
   cd satoshi-ai
   ```
3. **Set up the development environment**
   ```bash
   cp .env.example .env
   make setup
   ```

## Development Workflow

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the project's code style
   - Write tests for new features
   - Update documentation as needed

3. **Run tests**
   ```bash
   make test
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Go to the original repository
   - Click on "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template
   - Submit the PR

## Code Style

- Python: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- JavaScript/TypeScript: Follow [Airbnb Style Guide](https://github.com/airbnb/javascript)
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages

## Reporting Issues

When opening an issue, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs. actual behavior
- Any relevant logs or screenshots

## License

By contributing to Satoshi AI, you agree that your contributions will be licensed under the project's [LICENSE](LICENSE) file.
