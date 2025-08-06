# example_agent_integration.py
"""
Example of integrating the base64 image analyzer with your existing agent code
"""

# Import the single analysis function
from image_analyzer import analyze_image, MODELS

# Your existing agent imports
import boto3
import json

class YourExistingAgent:
    def __init__(self):
        # Your existing agent setup
        self.bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Your agent configuration
        self.agent_id = "your-agent-id"
        self.agent_alias_id = "TSTALIASID"
    
    def handle_image_question(self, image_base64: str, user_message: str, session_id: str):
        """
        Handle user question about an image from frontend
        
        Args:
            image_base64: Base64 encoded image from frontend
            user_message: User's question about the image
            session_id: Session ID for conversation continuity
        """
        try:
            # Step 1: Analyze the image (one simple call)
            image_analysis = analyze_image(image_base64)
            
            # Step 2: Format for your agent
            agent_input = f"""I have analyzed an image and here's what I found:

IMAGE ANALYSIS:
{image_analysis}

USER QUESTION: {user_message}

Please respond to the user's question about this image using the analysis above as factual reference."""

            # Step 3: Send to your existing agent
            response = self.bedrock_agent_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=agent_input
            )
            
            # Extract agent response (your existing logic)
            agent_response = self._extract_agent_response(response)
            
            return {
                "image_analysis": image_analysis,
                "agent_response": agent_response,
                "session_id": session_id
            }
            
        except Exception as e:
            raise Exception(f"Error in image question handling: {str(e)}")
    
    def handle_image_question_fast(self, image_base64: str, user_message: str, session_id: str):
        """Same as above but using faster model for quicker responses"""
        try:
            # Use fast model
            image_analysis = analyze_image(image_base64, model_id=MODELS['fast'])
            
            agent_input = f"""IMAGE ANALYSIS: {image_analysis}
USER QUESTION: {user_message}
Please respond using the analysis as factual reference."""
            
            response = self.bedrock_agent_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=agent_input
            )
            
            return {
                "image_analysis": image_analysis,
                "agent_response": self._extract_agent_response(response),
                "session_id": session_id
            }
            
        except Exception as e:
            raise Exception(f"Error in image question handling: {str(e)}")
    
    def _extract_agent_response(self, response):
        """Extract response text from agent response"""
        agent_response = ""
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        return agent_response.strip()

# ========================
# SIMPLE USAGE EXAMPLES
# ========================

def example_in_your_agent():
    """How this looks in your actual agent code"""
    
    # In your existing agent method, just add one line:
    def process_user_message_with_image(self, base64_image, user_question, session_id):
        
        # One line to get analysis
        image_analysis = analyze_image(base64_image)
        
        # Use in your existing agent logic
        full_prompt = f"""
        Based on this image analysis: {image_analysis}
        
        User asks: {user_question}
        
        [Your existing agent instructions...]
        """
        
        # Your existing agent call
        response = self.call_your_agent(full_prompt, session_id)
        return response
        
    print("That's all you need to add!")

def example_api_endpoint():
    """Example FastAPI endpoint"""
    
    # If you want to add this to FastAPI:
    """
    from fastapi import FastAPI
    from image_analyzer import analyze_image
    
    app = FastAPI()
    
    @app.post("/chat-with-image")
    async def chat_with_image(
        image_base64: str,
        user_message: str,
        session_id: str
    ):
        # Get image analysis
        analysis = analyze_image(image_base64)
        
        # Send to your agent (your existing code)
        agent_response = your_agent.process_message(
            f"Image shows: {analysis}. User asks: {user_message}",
            session_id
        )
        
        return {"response": agent_response}
    """
    print("Simple FastAPI integration example above")

if __name__ == "__main__":
    print("Base64 Image Integration")
    print("=" * 30)
    
    print("Super simple usage:")
    print("from image_analyzer import analyze_image")
    print("analysis = analyze_image(base64_from_frontend)")
    print("# Use analysis in your agent")
    
    print("\nWith options:")
    print("analysis = analyze_image(base64_string, prompt='What do you see?')")
    print("analysis = analyze_image(base64_string, model_id=MODELS['fast'])")
    
    example_in_your_agent()
    example_api_endpoint()

# ========================
# USAGE EXAMPLES - SINGLE FUNCTION
# ========================

def example_usage():
    """Examples showing the simplicity of the single function"""
    
    # Basic usage - just pass any image input
    try:
        # From file path
        analysis1 = analyze_image("path/to/image.jpg")
        print("File analysis:", analysis1[:100] + "...")
        
        # From base64 string
        import base64
        with open("path/to/image.jpg", "rb") as f:
            base64_string = base64.b64encode(f.read()).decode('utf-8')
        analysis2 = analyze_image(base64_string)
        print("Base64 analysis:", analysis2[:100] + "...")
        
        # From bytes
        with open("path/to/image.jpg", "rb") as f:
            image_bytes = f.read()
        analysis3 = analyze_image(image_bytes)
        print("Bytes analysis:", analysis3[:100] + "...")
        
    except Exception as e:
        print(f"Error: {e}")

def example_with_options():
    """Examples using different models and prompts"""
    
    try:
        # Quick analysis with fast model
        fast_analysis = analyze_image(
            "image.jpg", 
            model_id=MODELS['fast'],
            prompt=PROMPTS['simple']
        )
        
        # Detailed analysis with powerful model
        detailed_analysis = analyze_image(
            "image.jpg",
            model_id=MODELS['powerful'],
            prompt=PROMPTS['detailed']
        )
        
        # Custom prompt
        custom_analysis = analyze_image(
            "image.jpg",
            prompt="Focus only on people and what they're wearing"
        )
        
        print("Generated multiple analyses successfully")
        
    except Exception as e:
        print(f"Error: {e}")

# ========================
# INTEGRATION WITH YOUR EXISTING AGENT (SIMPLIFIED)
# ========================

def integrate_with_your_agent():
    """Super simple integration example"""
    
    # Your existing agent instance
    agent = YourExistingAgent()
    
    # Example: User uploads image and asks question
    try:
        # Just call the single function, then use the result
        result = agent.handle_image_question(
            image_input="path/to/uploaded/image.jpg",  # Can be file, base64, or bytes
            user_message="What's happening in this picture?",
            session_id="user-session-123"
        )
        
        print("Analysis + Agent Response:")
        print(result["agent_response"])
        
        # The analysis is available if you need it
        if needed_for_logging := True:
            print(f"Raw analysis: {result['image_analysis']}")
        
    except Exception as e:
        print(f"Integration error: {e}")

# ========================
# REAL WORLD USAGE IN YOUR CODE
# ========================

def your_actual_agent_method_example():
    """How this would look in your actual agent code"""
    
    # In your existing agent code, you'd just add these lines:
    
    def process_user_message_with_image(self, image_data, user_question, session_id):
        # One line to get image analysis
        image_analysis = analyze_image(image_data)  # That's it!
        
        # Then use it in your existing agent logic
        full_prompt = f"""
        Based on this image analysis: {image_analysis}
        
        User asks: {user_question}
        
        [Your existing agent instructions here...]
        """
        
        # Your existing agent call
        response = self.call_your_agent(full_prompt, session_id)
        return response
        
    print("This is how simple it becomes in your code!")

if __name__ == "__main__":
    print("Single Function Integration Examples")
    print("=" * 40)
    
    print("Usage is now super simple:")
    print("from image_analyzer import analyze_image")
    print("analysis = analyze_image(any_image_input)")
    print("# Use analysis in your agent")
    
    # Run examples (uncomment to test)
    # example_usage()
    # example_with_options() 
    # integrate_with_your_agent()
