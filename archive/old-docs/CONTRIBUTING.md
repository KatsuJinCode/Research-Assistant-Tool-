# Contributing to Research Assistant Tool

Thank you for your interest in contributing to the Research Assistant Tool! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Assume good intentions

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- Git

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Research-Assistant-Tool-.git
   cd Research-Assistant-Tool-
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Environment** (Coming soon)
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Check if the bug has already been reported
- Include detailed steps to reproduce
- Provide system information (OS, Python version, etc.)
- Include error messages and logs

### Suggesting Features

- Use the GitHub issue tracker
- Clearly describe the feature and its benefits
- Explain use cases
- Consider implementation complexity

### Submitting Changes

1. **Write Good Commit Messages**
   - Use conventional commits format
   - Examples:
     - `feat: add document summarization`
     - `fix: resolve PDF parsing error`
     - `docs: update installation guide`
     - `refactor: improve search algorithm`

2. **Follow Code Style**
   - Python: Follow PEP 8, use Black formatter
   - JavaScript/TypeScript: Use ESLint and Prettier
   - Write docstrings for functions and classes
   - Add comments for complex logic

3. **Write Tests**
   - Add unit tests for new features
   - Ensure all tests pass before submitting
   - Aim for >80% code coverage

4. **Update Documentation**
   - Update README if needed
   - Add docstrings to new functions
   - Update API documentation
   - Add examples for new features

5. **Create Pull Request**
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers
   - Address review comments promptly

## Development Guidelines

### Python Code Style

```python
# Good
def process_document(file_path: str, chunk_size: int = 1000) -> list[str]:
    """
    Process a document and split it into chunks.

    Args:
        file_path: Path to the document file
        chunk_size: Maximum size of each chunk in characters

    Returns:
        List of text chunks
    """
    # Implementation here
    pass
```

### TypeScript Code Style

```typescript
// Good
interface DocumentProps {
  id: string;
  title: string;
  content: string;
}

export function DocumentViewer({ id, title, content }: DocumentProps) {
  // Implementation here
}
```

### Testing

```python
# Python tests with pytest
def test_document_chunking():
    """Test that documents are chunked correctly."""
    text = "Sample text " * 1000
    chunks = chunk_document(text, chunk_size=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
```

```typescript
// TypeScript tests with Jest
describe('DocumentViewer', () => {
  it('renders document title', () => {
    render(<DocumentViewer id="1" title="Test" content="Content" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

## Project Structure

```
Research-Assistant-Tool-/
├── backend/                 # Python backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/           # Utilities
│   ├── public/            # Static assets
│   └── package.json
├── docs/                  # Documentation
├── docker/                # Docker configurations
└── scripts/               # Utility scripts
```

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation with any new features
3. The PR will be merged once you have approval from maintainers
4. Ensure all CI checks pass

## Questions?

- Open an issue for questions about contributing
- Reach out to maintainers
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
