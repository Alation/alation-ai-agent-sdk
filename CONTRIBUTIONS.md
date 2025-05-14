# Contributing to Alation AI Agent SDK

Thanks for taking the time to contribute!

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable
behavior to ai_agent_sdk@alation.com.

The following is a set of guidelines for contributing to the Alation AI Agent SDK.
These are just guidelines, not rules, use your best judgment and feel free to
propose changes to this document in a pull request.

## Issues

Issues are created [here](https://github.com/Alation/alation-ai-agent-sdk/issues/new/choose).

### Issue Closure

Bug reports will be closed if the issue has been inactive and the latest affected version no longer receives support.

_If an issue has been closed and you still feel it's relevant, feel free to ping a maintainer or add a comment!_

## Pull Requests

Pull Requests are the way concrete changes are made to the code, documentation,
dependencies, and tools contained in the `Alation/alation-ai-agent-sdk` repository.

### The Pull Request Process
- **Forking:** Start by forking the project's repository to your own GitHub account.
- **Branching:** Create a branch in your forked repository to isolate your work.
- **Making Changes:** Make your code changes, bug fixes, or additions within your branch.
- **Pushing:** Push your changes to your forked repository's branch.
- **Creating the Pull Request:**
  - Navigate to your forked repository on GitHub.
  - Click the "Pull Request" button.
  - Choose the base branch (`main`) of the original repository and your branch as the head branch.
  - Provide a clear title and description for your pull request.
  - Reference any related issues or bug reports.
- **Review and Merge:** The project maintainers will review your pull request. You may need to make changes based on feedback. Once approved, they'll merge your changes into the main repository. 

### Dependencies Upgrades Policy

Dependencies in Alation AI Agent SDK's `pdm.lock` files should only be altered by maintainers. For security reasons, we will not accept PRs that alter our `pdm.lock` files. We invite contributors to make requests updating these files in our issue tracker. If the change is significantly complicated, draft PRs are welcome, with the understanding that these PRs will be closed in favor of a duplicate PR submitted by an Alation AI Agent SDK maintainer.
