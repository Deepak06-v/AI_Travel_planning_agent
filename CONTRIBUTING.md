# Contributing to AI Travel Planner Agent

Thank you for your interest in contributing! We welcome all forms of contributions, from bug reports to feature requests to code improvements.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions. We're here to help each other build great software.

## How to Contribute

### 1. Report Bugs

If you find a bug:
1. Check existing [Issues](../../issues) to avoid duplicates
2. Create a new issue with the **Bug Report** template
3. Include steps to reproduce, expected behavior, and actual behavior
4. Mention your Python version and OS

### 2. Suggest Features

To suggest a feature:
1. Check existing [Discussions](../../discussions) or [Issues](../../issues)
2. Create a new issue with the **Feature Request** template
3. Explain the use case and motivation
4. Consider alternative approaches

### 3. Submit Code Changes

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/travel.git
cd travel

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install development tools
pip install flake8 black pytest
```

#### Make Your Changes

1. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Write clean, documented code**:
   - Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
   - Add docstrings to all public functions and classes
   - Use type hints where possible
   - Keep lines under 100 characters when practical

3. **Test your changes locally**:
   ```bash
   # Set required environment variables
   export GCP_PROJECT_ID="your-test-project-id"
   
   # Run the application
   python main.py
   
   # Or test the weather service
   python weather_test_cli.py
   ```

4. **Verify no credentials are hardcoded**:
   - Use environment variables for API keys
   - Never commit `.env` with real keys (use `.env.example` instead)
   - Check your code with `grep` for hardcoded secrets before committing

#### Commit and Push

```bash
# Commit with a clear, descriptive message
git commit -m "feat: add feature description" -m "Detailed explanation of changes"

# Push to your fork
git push origin feature/your-feature-name
```

#### Create a Pull Request

1. Go to the original repository
2. Click **New Pull Request**
3. Select your branch and fill out the PR template:
   - Clear description of changes
   - Link any related issues (#123)
   - Check off your testing checklist

## Code Style

### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use 4 spaces for indentation
- Line length max 100 characters
- Docstring format:
  ```python
  def my_function(param: str) -> str:
      """
      Brief description.
      
      Longer description if needed.
      
      Args:
          param: Description of param.
      
      Returns:
          Description of return value.
      
      Raises:
          ValueError: When invalid input is provided.
      """
  ```

### Commit Messages
- Use [conventional commits](https://www.conventionalcommits.org/):
  - `feat:` for features
  - `fix:` for bug fixes
  - `docs:` for documentation
  - `refactor:` for code improvements
  - `test:` for tests
  - `chore:` for maintenance

Example:
```
feat: add weather cache to reduce API calls

- Cache weather data for 1 hour per destination
- Implement cache invalidation on location change
- Log cache hits/misses for debugging

Closes #42
```

## Architecture Guidelines

The project is organized into layers:

```
CLI (cli_planner.py)
    ↓
Agent (travel_agent.py) — orchestrates everything
    ↓
Services (weather_service.py, gemini_service.py, etc.)
    ↓
Models (UserInput, PlanningContext, etc.)
    ↓
Utils (formatter.py, route_optimizer.py)
```

When adding features:
- **New data types?** → Add to `project/models/`
- **New external API?** → Add to `project/services/`
- **New business logic?** → Add to `project/agent/`
- **New CLI interaction?** → Modify `project/agent/cli_planner.py`
- **UI formatting?** → Use/enhance `project/utils/formatter.py`

## Testing

Before submitting a PR:

1. **Test locally** with various inputs
2. **Check environment variables** are properly handled
3. **Verify error messages** are helpful
4. **Test with minimal config** (only `GCP_PROJECT_ID`)
5. **Test with full config** (all optional APIs enabled)

## Documentation

- Update the **README** if you add features or change setup
- Add docstrings to all public APIs
- Update the **CHANGELOG** for notable changes
- Include examples in docstrings when helpful

## Questions?

- Check the **README** and existing code
- Search **Issues** and **Discussions** for similar questions
- Open an issue with the `question` label

Thank you for contributing! 🚀
