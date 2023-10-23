# Charm Library Interface for Tokens

This library provides an interface for handling the `tokens` integration for Charmed Kubernetes charms.

## Installation

Install from the current Git repository:

1. Add the repository to the `requirements.txt` file.
```
charm-lib-interface-tokens @ git+https://github.com/charmed-kubernetes/charm-lib-interface-tokens
```
## Features

1. **Token Management**: Facilitates sending tokens to related units and aggregates token data.
2. **Token Requests**: Enables charms to send, receive, and manage authentication token requests.

## Usage

### TokensProvider

This class implements the "Provides" side of the tokens interface. Using this class, a charm can listen for token requests and send tokens to related units.

**Example**:

```python
from charms.interface_tokens import TokensProvider
...
# Initialize the provider.
self.tokens_provider = TokensProvider(charm, "tokens")
...
# Check for token requests.
requests = self.tokens_provider.token_requests

# Process and send tokens to requesting units.
for request in requests:
    token = "SOME_GENERATED_TOKEN"  # Token generation logic
    self.tokens_provider.send_token(request, token)
```

### TokensRequirer

Handles the "Requirer" side of the tokens relation, enabling charms to request tokens and retrieve them once they are available.

**Example**:

```python
from charms.interface_tokens import TokensRequirer
...
# Initialize the requirer.
self.tokens_requirer = TokensRequirer(charm)
...
# Request a token.
self.tokens_requirer.request_token(user="someuser", group="somegroup")
...
# Retrieve a token for a specific user.
token = self.tokens_requirer.get_token(user="someuser")
```
## License

This project is licensed under the Apache Software License.
