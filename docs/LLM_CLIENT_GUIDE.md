# LLM Client Utility Guide

This guide explains how to use the comprehensive LLM client utility that supports multiple providers including OpenAI, Anthropic, Google Gemini, Ollama, local, enterprise, and Apigee.

## Overview

The LLM client utility provides a unified interface for calling different LLM providers. It automatically selects the best available provider based on your environment variables and maintains backward compatibility with the existing `call_llm` function.

## Supported Providers

### 1. OpenAI
- **Models**: GPT-4, GPT-4o, o1, GPT-3.5-turbo
- **Environment Variables**:
  - `OPENAI_API_KEY` (required)
  - `OPENAI_MODEL` (default: "gpt-4")
  - `OPENAI_BASE_URL` (optional, for custom endpoints)
  - `OPENAI_TEMPERATURE` (default: 0.1)
  - `OPENAI_MAX_TOKENS` (default: 4000)

### 2. Anthropic Claude
- **Models**: Claude 3 Sonnet, Claude 3.5 Sonnet, Claude 3 Haiku
- **Environment Variables**:
  - `ANTHROPIC_API_KEY` (required)
  - `ANTHROPIC_MODEL` (default: "claude-3-sonnet-20240229")
  - `ANTHROPIC_BASE_URL` (optional, for custom endpoints)
  - `ANTHROPIC_TEMPERATURE` (default: 0.1)
  - `ANTHROPIC_MAX_TOKENS` (default: 4000)

### 3. Google Gemini
- **Models**: Gemini Pro, Gemini 2.0 Flash, Gemini 1.5 Pro
- **Environment Variables**:
  - `GEMINI_API_KEY` (required)
  - `GEMINI_MODEL` (default: "gemini-pro")
  - `GEMINI_BASE_URL` (optional, for custom endpoints)
  - `GEMINI_TEMPERATURE` (default: 0.1)
  - `GEMINI_MAX_TOKENS` (default: 4000)

### 4. Ollama (Local)
- **Models**: Any model available in Ollama
- **Environment Variables**:
  - `OLLAMA_HOST` (default: "http://localhost:11434")
  - `OLLAMA_MODEL` (default: "llama-3.2-3b-instruct")
  - `OLLAMA_TEMPERATURE` (default: 0.1)
  - `OLLAMA_NUM_PREDICT` (default: 4000)

### 5. Local LLM API
- **Models**: Any model with OpenAI-compatible API
- **Environment Variables**:
  - `LOCAL_LLM_URL` (required, e.g., "http://localhost:11434/v1")
  - `LOCAL_LLM_MODEL` (default: "llama-3.2-3b-instruct")
  - `LOCAL_LLM_API_KEY` (optional)
  - `LOCAL_LLM_TEMPERATURE` (default: 0.1)
  - `LOCAL_LLM_MAX_TOKENS` (default: 4000)

### 6. Enterprise LLM
- **Models**: Enterprise-specific models
- **Environment Variables**:
  - `ENTERPRISE_LLM_URL` (required)
  - `ENTERPRISE_LLM_TOKEN` (required)
  - `ENTERPRISE_LLM_MODEL` (default: "llama-3.2-3b-instruct")
  - `ENTERPRISE_LLM_TEMPERATURE` (default: 0.1)
  - `ENTERPRISE_LLM_MAX_TOKENS` (default: 4000)
  - `ENTERPRISE_LLM_REFRESH_URL` (optional, for token refresh)
  - `ENTERPRISE_LLM_CLIENT_ID` (optional, for token refresh)
  - `ENTERPRISE_LLM_CLIENT_SECRET` (optional, for token refresh)
  - `ENTERPRISE_LLM_REFRESH_TOKEN` (optional, for token refresh)
  - `ENTERPRISE_LLM_HEADERS` (optional, JSON string for additional headers)

### 7. Apigee Enterprise
- **Models**: Enterprise models through Apigee gateway
- **Environment Variables**:
  - `APIGEE_NONPROD_LOGIN_URL` (required)
  - `APIGEE_CONSUMER_KEY` (required)
  - `APIGEE_CONSUMER_SECRET` (required)
  - `ENTERPRISE_BASE_URL` (required)
  - `WF_USE_CASE_ID` (required)
  - `WF_CLIENT_ID` (required)
  - `WF_API_KEY` (required)
  - `APIGEE_MODEL` (default: "gpt-4")
  - `APIGEE_TEMPERATURE` (default: 0.1)
  - `APIGEE_MAX_TOKENS` (default: 4000)

## Usage

### Basic Usage

The simplest way to use the LLM client is through the `call_llm` function:

```python
from utils.call_llm import call_llm

# The function automatically selects the best available provider
response = call_llm("Hello, how are you?")
print(response)
```

### Advanced Usage

For more control, you can create and configure clients directly:

```python
from utils.call_llm import LLMClient, LLMConfig, LLMProvider

# Create a specific configuration
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    api_key="your-api-key",
    temperature=0.1,
    max_tokens=4000
)

# Create the client
client = LLMClient(config)

# Make a call
response = client.call_llm("Hello, how are you?")
print(response)
```

### Environment-based Configuration

The client can automatically create itself from environment variables:

```python
from utils.call_llm import create_llm_client_from_env

# This will automatically select the best available provider
client = create_llm_client_from_env()

if client:
    response = client.call_llm("Hello, how are you?")
    print(response)
else:
    print("No LLM provider configured")
```

## Provider Priority

When multiple providers are configured, the client selects them in this order:

1. OpenAI
2. Anthropic
3. Gemini
4. Apigee
5. Enterprise
6. Local
7. Ollama

## Token Management

### Enterprise Token Refresh

The enterprise client supports automatic token refresh:

```python
# Set up environment variables for token refresh
os.environ["ENTERPRISE_LLM_REFRESH_URL"] = "https://your-auth-server/token"
os.environ["ENTERPRISE_LLM_CLIENT_ID"] = "your-client-id"
os.environ["ENTERPRISE_LLM_CLIENT_SECRET"] = "your-client-secret"

# Or use refresh tokens
os.environ["ENTERPRISE_LLM_REFRESH_TOKEN"] = "your-refresh-token"
```

### Apigee Token Management

The Apigee client automatically manages bearer tokens:

```python
# Set up Apigee environment variables
os.environ["APIGEE_NONPROD_LOGIN_URL"] = "https://your-apigee-login-url"
os.environ["APIGEE_CONSUMER_KEY"] = "your-consumer-key"
os.environ["APIGEE_CONSUMER_SECRET"] = "your-consumer-secret"
```

## Error Handling

The client provides comprehensive error handling:

```python
try:
    response = call_llm("Hello, how are you?")
    print(response)
except ImportError as e:
    print(f"Required library not installed: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"LLM call failed: {e}")
```

## Testing

You can test the LLM client using the provided test script:

```bash
python test_llm_client.py
```

This will:
1. Test client creation from environment variables
2. Test a simple LLM call
3. Check configuration for all providers
4. Test backward compatibility

## Migration from Old Implementation

The new client maintains backward compatibility with the old `call_llm` function. However, note that:

1. The `use_cache` parameter is ignored (caching is not supported in the new implementation)
2. The function signature remains the same: `call_llm(prompt: str, use_cache: bool = True) -> str`
3. All existing code should continue to work without changes

## Dependencies

The client uses optional dependencies. Install only what you need:

```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For Google Gemini
pip install google-generativeai

# For Ollama
pip install ollama

# For HTTP client (used by local/enterprise)
pip install httpx
```

## Best Practices

1. **Environment Variables**: Use environment variables for API keys and configuration
2. **Error Handling**: Always wrap LLM calls in try-catch blocks
3. **Provider Selection**: Let the client automatically select the best available provider
4. **Testing**: Use the test script to verify your configuration
5. **Security**: Never hardcode API keys in your code

## Troubleshooting

### Common Issues

1. **"No LLM provider configured"**: Set appropriate environment variables
2. **Import errors**: Install required dependencies
3. **Authentication errors**: Check API keys and tokens
4. **Network errors**: Check internet connection and firewall settings

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show token refresh attempts, API calls, and error details. 