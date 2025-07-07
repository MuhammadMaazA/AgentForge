#!/usr/bin/env python3
"""
Test script for AgentForge API endpoints
Run this after starting the FastAPI server to test the code generation functionality
Supports both OpenAI and Gemini APIs
"""

import requests
import json
import time
import os

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed!")
            print(f"   AI Provider: {data.get('ai_provider', 'unknown')}")
            print(f"   API configured: {data.get('api_configured')}")
            print(f"   Model: {data.get('model')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_code_generation():
    """Test the main code generation endpoint"""
    print("\n🚀 Testing code generation endpoint...")
    
    # Sample request data
    test_data = {
        "app_name": "TaskManager",
        "features": [
            "Add and delete tasks",
            "Mark tasks as complete",
            "Filter tasks by status",
            "Save tasks to local storage"
        ],
        "app_type": "streamlit",
        "description": "A simple but elegant task management application with a clean interface"
    }
    
    print(f"📝 Generating app: {test_data['app_name']}")
    print(f"   Features: {', '.join(test_data['features'])}")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/generate", json=test_data)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Code generation successful! ({end_time - start_time:.1f}s)")
                print(f"   AI Provider: {data.get('ai_provider', 'unknown')}")
                print(f"   Generated {len(data['generated_code'])} characters of code")
                
                # Generate filename in the proper directory structure
                provider = data.get('ai_provider', 'unknown')
                app_type = test_data.get('app_type', 'streamlit')
                
                # Create the directory structure
                import datetime
                base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_apps")
                app_type_dir = os.path.join(base_dir, app_type)
                os.makedirs(app_type_dir, exist_ok=True)
                
                # Save with timestamp for uniqueness
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{test_data['app_name']}_{provider}_{timestamp}.py"
                filepath = os.path.join(app_type_dir, filename)
                
                # Save the generated code
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(data["generated_code"])
                    
                print(f"   💾 Code saved to 'generated_apps/{app_type}/{filename}'")
                print(f"   📁 Full path: {filepath}")
                
                return True
            else:
                print(f"❌ Code generation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Code generation error: {e}")
        return False

def test_simple_generation():
    """Test the simple generation endpoint"""
    print("\n💡 Testing simple generation endpoint...")
    
    test_prompt = {
        "text": "Create a simple Python function that calculates the factorial of a number"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate-simple", json=test_prompt)
        
        if response.status_code == 200:
            data = response.json()
            provider = data.get('provider', 'unknown')
            print(f"✅ Simple generation successful!")
            print(f"   AI Provider: {provider}")
            print(f"   Response: {data.get('message', '')[:100]}...")
            return True
        else:
            print(f"❌ Simple generation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Simple generation error: {e}")
        return False

def test_api_switching():
    """Test information about API switching"""
    print("\n🔄 API Provider Information...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            provider = data.get('ai_provider', 'unknown')
            print(f"✅ Current AI Provider: {provider}")
            print(f"   💡 To switch providers, edit the AI_PROVIDER in your .env file")
            print(f"   📝 Available options: 'openai' or 'gemini'")
            return True
    except Exception as e:
        print(f"❌ API info error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 AgentForge API Test Suite (Multi-Provider)")
    print("=" * 55)
    
    # Test health first
    if not test_health():
        print("\n❌ Health check failed. Make sure:")
        print("   1. FastAPI server is running (uvicorn main:app --reload)")
        print("   2. Correct API key is set in your .env file")
        print("   3. AI_PROVIDER is set to either 'openai' or 'gemini'")
        return
    
    # Show API switching info
    test_api_switching()
    
    # Test main functionality
    success_count = 0
    total_tests = 2
    
    if test_code_generation():
        success_count += 1
    
    if test_simple_generation():
        success_count += 1
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Your AgentForge API is working correctly.")
        print("\n📝 Next Steps:")
        print("   1. Get a free Gemini API key at: https://aistudio.google.com/app/apikey")
        print("   2. Add it to your .env file as GEMINI_API_KEY")
        print("   3. Set AI_PROVIDER=gemini for free testing")
        print("   4. Switch to AI_PROVIDER=openai for deployment")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main() 