# Contributing

Thank you for considering a contribution to this project!  We welcome bug
reports, feature requests and pull requests.  The following guidelines help
ensure a smooth collaboration.

## How to report bugs

If you encounter unexpected behaviour or a defect:

1. **Check the existing issues** to see if your problem has already been
   reported or fixed.
2. **Open a new issue** with a clear and descriptive title.  Explain what
   happens, what you expected to happen and how to reproduce the issue.  If
   applicable, include logs, screenshots or relevant environment details.
3. **Label the issue** appropriately (e.g. bug, enhancement).  We will
   triage the issue and provide feedback.

## How to request a feature

1. Describe the feature you would like to see.  Explain the use case and
   why it would benefit other users.
2. If possible, provide examples or reference implementations.
3. We will discuss the proposal and, if accepted, help refine the design.

## Development workflow

1. **Fork** this repository and create a new branch for your work:

   ```bash
   git checkout -b feature/your‑feature
   ```

2. **Set up the tooling** by installing the development dependencies and
   pre-commit hooks:

   ```bash
   make dev
   make env-validate  # optional: confirm your .env satisfies the schema
   ```

   This installs the packages listed in `requirements-dev.txt` and registers
   the repository’s pre-commit hooks locally.

3. **Write code** that adheres to the following standards:

   * Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style.
   * Document new functions, classes and modules with docstrings.
   * Add error handling for edge cases.
   * Write tests where possible; although this project currently lacks a full
     test suite, contributions that include tests are appreciated.

4. **Run the automated checks** before submitting your changes:

   ```bash
   make lint
   make type
   make test
   make env-validate
   ```

   The lint target runs `ruff check`, the type target executes `mypy` with
   `mypy.ini`, and the test target runs the `pytest` suite.

5. **Commit your changes** with clear messages:

   ```bash
   git commit -m "feat: add support for XYZ"
   ```

6. **Push** your branch to GitHub and open a pull request (PR).  In the PR
   description, describe what you’ve done and reference any issues the PR
   resolves.

7. **Address review feedback**.  We may request changes or clarifications.
   Please be patient and respond to review comments.

## Code of Conduct

Be kind and respectful.  Harassment or abusive behaviour will not be
tolerated.  We follow the [Contributor Covenant](https://www.contributor-covenant.org/)
Code of Conduct.

---

Thank you for helping improve this project!
