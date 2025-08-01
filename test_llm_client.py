#!/usr/bin/env python3
"""
Test script for the comprehensive LLM client utility
"""

import os
import sys
from utils.call_llm import create_llm_client_from_env, LLMProvider, LLMConfig, LLMClient

def test_llm_client():
    """Test the LLM client with different providers"""
    print("🧪 Testing Comprehensive LLM Client...")
    print("=" * 50)
    
    # Test 1: Create client from environment
    print("1. Testing client creation from environment variables...")
    client = create_llm_client_from_env()
    
    if client:
        print(f"✅ Successfully created {client.config.provider.value} client")
        print(f"   Model: {client.config.model}")
        print(f"   Available: {client.is_available()}")
        
        # Test 2: Simple LLM call
        print("\n2. Testing simple LLM call...")
        try:
            response = client.call_llm("Hello! Please respond with 'LLM test successful!'")
            print(f"✅ Test response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    else:
        print("❌ No LLM client could be created from environment")
        print("\nAvailable environment variables:")
        env_vars = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
            "OLLAMA_HOST", "LOCAL_LLM_URL", "ENTERPRISE_LLM_URL",
            "APIGEE_NONPROD_LOGIN_URL"
        ]
        for var in env_vars:
            value = os.getenv(var)
            status = "✅ Set" if value else "❌ Not set"
            print(f"   {var}: {status}")
        return False
    
    # Test 3: Test different providers (if configured)
    print("\n3. Testing provider-specific configurations...")
    providers_to_test = [
        (LLMProvider.OPENAI, "OPENAI_API_KEY"),
        (LLMProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (LLMProvider.GEMINI, "GEMINI_API_KEY"),
        (LLMProvider.OLLAMA, "OLLAMA_HOST"),
        (LLMProvider.LOCAL, "LOCAL_LLM_URL"),
        (LLMProvider.ENTERPRISE, "ENTERPRISE_LLM_URL"),
        (LLMProvider.APIGEE, "APIGEE_NONPROD_LOGIN_URL")
    ]
    
    for provider, env_var in providers_to_test:
        if os.getenv(env_var):
            try:
                from utils.call_llm import _create_config_for_provider
                config = _create_config_for_provider(provider)
                test_client = LLMClient(config)
                print(f"   {provider.value}: ✅ Configured (Available: {test_client.is_available()})")
            except Exception as e:
                print(f"   {provider.value}: ❌ Configuration failed - {e}")
        else:
            print(f"   {provider.value}: ⚪ Not configured")
    
    print("\n✅ LLM Client test completed successfully!")
    return True

def test_backward_compatibility():
    """Test backward compatibility with the old call_llm function"""
    print("\n🔄 Testing backward compatibility...")
    print("=" * 50)
    
    try:
        from utils.call_llm import call_llm
        
        # Test the old function signature
        response = call_llm("Hello! This is a backward compatibility test.")
        print(f"✅ Backward compatibility test passed: {response[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting LLM Client Tests")
    print("=" * 50)
    
    success = True
    
    # Test the new client
    if not test_llm_client():
        success = False
    
    # Test backward compatibility
    if not test_backward_compatibility():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The LLM client is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check your configuration.")
        sys.exit(1) 