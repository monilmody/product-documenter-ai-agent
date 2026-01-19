"""
Complete Document Generator with Real OpenAI Integration
"""

import openai
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EnhancedDocumentGenerator:
    """Generates documents using real OpenAI API with cost tracking"""
    
    def __init__(self):
        # Initialize OpenAI with your API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
            print("⚠️  OpenAI API key not found. Using simulated mode.")
        
        # OpenAI pricing per 1K tokens (as of Dec 2023)
        self.pricing = {
            'gpt-3.5-turbo': 0.002,      # $0.002 per 1K tokens
            'gpt-3.5-turbo-instruct': 0.0015,
            'gpt-4': 0.03,               # $0.03 per 1K tokens
            'gpt-4-turbo-preview': 0.01,
        }
        
        # Document templates for licensing
        self.templates = {
            "technical_spec": {
                "system": """You are a technical documentation expert creating specifications for software licensing.
                Create detailed, professional technical specifications that can be used for:
                1. Licensing agreements
                2. Enterprise sales
                3. Technical due diligence
                4. Integration guides""",
                "prompt": """Create a comprehensive technical specification document for licensing purposes.

PRODUCT CONTEXT: {context}

KEY FEATURES:
{features}

REQUIRED SECTIONS:
1. **Product Overview** - What it does, target users, key benefits
2. **Technical Architecture** - Components, data flow, diagrams
3. **System Requirements** - Hardware, software, dependencies
4. **API Specifications** - Endpoints, authentication, rate limits
5. **Security Features** - Encryption, compliance, audit logging
6. **Performance Metrics** - Response times, throughput, scalability
7. **Integration Points** - How it connects with other systems
8. **Support & Maintenance** - SLAs, update cycles, support channels

Make this document professional, detailed, and ready for enterprise licensing discussions."""
            },
            "api_documentation": {
                "system": "You create API documentation for licensing and integration.",
                "prompt": """Generate complete API documentation for software licensing.

API CONTEXT: {context}

MUST INCLUDE:
1. **Authentication** - All auth methods, token management
2. **Rate Limiting** - Limits, quotas, throttling
3. **All Endpoints** - URL, methods, parameters, examples
4. **Request/Response Formats** - JSON schemas, examples
5. **Error Handling** - Error codes, messages, resolution
6. **SDK Availability** - Language support, examples
7. **Webhook Support** - Events, payloads, security
8. **Performance SLAs** - Response time guarantees

This documentation will be used by technical teams for integration planning."""
            },
            "user_manual": {
                "system": "You create user manuals for enterprise software licensing.",
                "prompt": """Create a user manual section suitable for licensing documentation.

TOPIC: {context}

INCLUDE:
1. **Getting Started** - Prerequisites, installation steps
2. **Key Features** - Detailed feature descriptions
3. **Step-by-Step Guides** - Practical examples
4. **Configuration Options** - Customization possibilities
5. **Troubleshooting** - Common issues and solutions
6. **Best Practices** - Recommended usage patterns
7. **FAQs** - Frequently asked questions
8. **Support Contacts** - How to get help

Format for enterprise system administrators evaluating the software."""
            },
            "license_readiness": {
                "system": "You prepare software documentation for legal and licensing review.",
                "prompt": """Prepare documentation sections needed for software licensing.

SOFTWARE DETAILS: {context}

CREATE THESE SECTIONS:
1. **Software Description** - Clear, non-technical overview
2. **Usage Rights** - What the license permits
3. **Restrictions** - What the license prohibits
4. **Technical Boundaries** - User limits, data restrictions
5. **Compliance Requirements** - Security, privacy, regulations
6. **Audit Provisions** - Usage tracking, verification methods
7. **Support Obligations** - What support is included
8. **Documentation Requirements** - What docs must be provided

Make this suitable for inclusion in legal contracts."""
            }
        }
    
    def calculate_cost(self, tokens):
        """Calculate actual cost based on tokens used"""
        cost_per_1k = self.pricing.get(self.model, 0.002)
        return (tokens / 1000) * cost_per_1k
    
    def generate_document(self, doc_type, context, features=None):
        """Generate document using real OpenAI API"""
        
        if doc_type not in self.templates:
            doc_type = "technical_spec"
        
        template = self.templates[doc_type]
        
        # Prepare prompt
        prompt = template["prompt"].format(
            context=context,
            features=features or "Key features will be detailed in the specification."
        )
        
        # Use real OpenAI if available
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": template["system"]},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                cost = self.calculate_cost(tokens_used)
                
                result = {
                    "content": content,
                    "tokens": tokens_used,
                    "cost": cost,
                    "model": self.model,
                    "provider": "openai",
                    "success": True,
                    "generated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                # Fallback to simulated response
                result = self._generate_simulated(doc_type, context)
        else:
            # No OpenAI key, use simulated
            result = self._generate_simulated(doc_type, context)
        
        return result
    
    def _generate_simulated(self, doc_type, context):
        """Generate simulated document when OpenAI is not available"""
        simulated_tokens = 800
        simulated_cost = self.calculate_cost(simulated_tokens)
        
        content = f"""# {doc_type.replace('_', ' ').title()}
        
## Based on: {context}

### Document Type: {doc_type}
### Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
### Status: Simulated (OpenAI not configured)

This is a simulated document. To get AI-generated content:

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Add to .env file: OPENAI_API_KEY=sk-your-key-here
3. Restart the API server

**Example Content Structure:**
- Overview
- Technical specifications
- Requirements
- Integration points
- Security considerations
- Licensing recommendations

*Enable OpenAI for real AI-generated documentation.*
"""
        
        return {
            "content": content,
            "tokens": simulated_tokens,
            "cost": simulated_cost,
            "model": "simulated",
            "provider": "simulated",
            "success": False,
            "generated_at": datetime.now().isoformat()
        }
    
    def log_cost_to_db(self, activity_id, result):
        """Log cost to SQLite database"""
        import sqlite3
        
        try:
            conn = sqlite3.connect('documenter.db')
            cursor = conn.cursor()
            
            # Log to ai_costs table
            cursor.execute('''
                INSERT INTO ai_costs 
                (provider, model, tokens_used, cost, activity_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                result['provider'],
                result['model'],
                result['tokens'],
                result['cost'],
                activity_id
            ))
            
            # Update activities table
            cursor.execute('''
                UPDATE activities 
                SET ai_tokens_used = ?, ai_cost = ?, status = 'generated'
                WHERE id = ?
            ''', (result['tokens'], result['cost'], activity_id))
            
            conn.commit()
            conn.close()
            
            print(f"💰 Cost logged to DB: ${result['cost']:.6f}")
            
        except Exception as e:
            print(f"❌ Failed to log cost to DB: {e}")

# Test the generator
if __name__ == "__main__":
    print("🔧 Testing Enhanced Document Generator...")
    
    generator = EnhancedDocumentGenerator()
    
    # Check OpenAI status
    if generator.client:
        print("✅ OpenAI configured")
        print(f"   Model: {generator.model}")
        print(f"   Pricing: ${generator.pricing.get(generator.model, 0.002):.4f} per 1K tokens")
    else:
        print("⚠️  OpenAI not configured (simulated mode)")
        print("   Add OPENAI_API_KEY to .env file")
    
    # Test generation
    test_context = "Almond Milk Homogenization Control System"
    result = generator.generate_document("technical_spec", test_context)
    
    print(f"\n📄 Document Generated:")
    print(f"   Provider: {result['provider']}")
    print(f"   Tokens: {result['tokens']}")
    print(f"   Cost: ${result['cost']:.6f}")
    print(f"   Success: {result['success']}")
    
    # Show preview
    preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
    print(f"\nPreview:\n{preview}")