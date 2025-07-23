from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import boto3
import base64
import json
import os
import uuid
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Bedrock Data Visualization API",
    description="API for data visualization using AWS Bedrock Agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
AGENT_ID = os.getenv("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID")
CROSS_ACCOUNT_ROLE = os.getenv("CROSS_ACCOUNT_ROLE")

# Global variables for clients
bedrock_client = None
sts_client = None
credentials = None

# Supported file types for data visualization
SUPPORTED_DATA_FILES = {
    '.csv': 'text/csv',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.json': 'application/json',
    '.yaml': 'application/x-yaml',
    '.yml': 'application/x-yaml'
}

SUPPORTED_DOCUMENT_FILES = {
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.html': 'text/html',
    '.md': 'text/markdown'
}

# Request/Response models
class FileVisualizationRequest(BaseModel):
    prompt: str
    file_name: str
    file_content: str  # base64 encoded
    file_type: str  # MIME type from frontend
    session_id: Optional[str] = None
    analysis_type: Optional[str] = "comprehensive"  # basic, comprehensive, custom
    use_case: Optional[str] = "auto"  # auto, chat, code_interpreter, both
    chart_types: Optional[List[str]] = None  # specific chart types requested

class VisualizationResponse(BaseModel):
    session_id: str
    response_text: str
    generated_files: List[dict]
    analysis_summary: dict
    execution_time: float
    success: bool

class GeneratedFile(BaseModel):
    name: str
    download_url: str
    file_type: str  # image, data, document
    size_bytes: int

# Utility functions
def refresh_credentials():
    """Refresh AWS credentials and recreate clients"""
    global sts_client, bedrock_client, credentials
    
    try:
        logger.info("Refreshing AWS credentials...")
        sts_client = boto3.client("sts")
        
        if CROSS_ACCOUNT_ROLE:
            assumed_role = sts_client.assume_role(
                RoleArn=CROSS_ACCOUNT_ROLE,
                RoleSessionName="BedrockVisualizationSession"
            )
            credentials = assumed_role["Credentials"]
            
            bedrock_client = boto3.client(
                "bedrock-agent-runtime",
                region_name=BEDROCK_REGION,
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"]
            )
        else:
            bedrock_client = boto3.client(
                "bedrock-agent-runtime",
                region_name=BEDROCK_REGION
            )
        
        logger.info("Credentials refreshed successfully")
        
    except Exception as e:
        logger.error(f"Error refreshing credentials: {e}")
        raise

def determine_use_case(file_name: str, file_type: str, prompt: str) -> List[str]:
    """Determine appropriate use case based on file and prompt"""
    file_ext = os.path.splitext(file_name.lower())[1] if file_name else ""
    prompt_lower = prompt.lower()
    
    # Keywords that suggest visualization/analysis
    viz_keywords = [
        'chart', 'graph', 'plot', 'visualize', 'analyze', 'dashboard',
        'trend', 'correlation', 'statistics', 'metrics', 'distribution'
    ]
    
    # Keywords that suggest text processing
    text_keywords = [
        'summarize', 'explain', 'extract', 'find', 'search', 'read'
    ]
    
    wants_viz = any(keyword in prompt_lower for keyword in viz_keywords)
    wants_text = any(keyword in prompt_lower for keyword in text_keywords)
    
    # Data files default to CODE_INTERPRETER for visualization
    if file_ext in SUPPORTED_DATA_FILES:
        if wants_text and not wants_viz:
            return ["CHAT"]
        elif wants_viz or not wants_text:
            return ["CODE_INTERPRETER"]
        else:
            return ["CHAT", "CODE_INTERPRETER"]
    
    # Document files default to CHAT
    elif file_ext in SUPPORTED_DOCUMENT_FILES:
        if wants_viz:
            return ["CHAT", "CODE_INTERPRETER"]
        else:
            return ["CHAT"]
    
    return ["CHAT"]

def validate_file_size(file_data: bytes) -> tuple[bool, str]:
    """Validate file size for BYTE_CONTENT upload"""
    file_size_mb = len(file_data) / (1024 * 1024)
    if file_size_mb > 10:
        return False, f"File too large: {file_size_mb:.2f}MB (max 10MB)"
    return True, f"File size OK: {file_size_mb:.2f}MB"

def get_mime_type(filename: str, provided_type: str = None) -> str:
    """Get MIME type for file"""
    if provided_type:
        return provided_type
    
    file_ext = os.path.splitext(filename.lower())[1]
    
    # Check supported types
    if file_ext in SUPPORTED_DATA_FILES:
        return SUPPORTED_DATA_FILES[file_ext]
    elif file_ext in SUPPORTED_DOCUMENT_FILES:
        return SUPPORTED_DOCUMENT_FILES[file_ext]
    
    # Fallback to mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"

def create_visualization_prompt(user_prompt: str, analysis_type: str, chart_types: List[str] = None, file_name: str = None) -> str:
    """Create enhanced prompt for data visualization based on file type and user request"""
    
    file_ext = os.path.splitext(file_name.lower())[1] if file_name else ""
    
    # Determine if it's a data file that can be visualized
    is_data_file = file_ext in SUPPORTED_DATA_FILES
    
    if analysis_type == "basic" and is_data_file:
        base_prompt = f"""
Analyze the uploaded file '{file_name}' and create basic visualizations:
1. Read and understand the data structure
2. Create 2-3 key charts showing main trends and patterns
3. Provide a brief summary of insights

User request: {user_prompt}
"""
    elif analysis_type == "comprehensive" and is_data_file:
        base_prompt = f"""
Perform comprehensive data analysis and visualization of '{file_name}':

1. **Data Overview**: 
   - Display first few rows and data structure
   - Show data types and basic statistics
   - Identify any data quality issues

2. **Statistical Analysis**:
   - Summary statistics for all numeric columns
   - Distribution analysis
   - Identify outliers and missing values

3. **Visualizations** (save as high-quality PNG files):
   - Trend analysis (line charts for time series data)
   - Distribution charts (histograms, box plots)
   - Comparison charts (bar charts, grouped comparisons)
   - Correlation analysis (heatmap if multiple numeric columns)
   - Any domain-specific charts based on data content

4. **Insights & Recommendations**:
   - Key findings and patterns
   - Actionable insights
   - Recommendations for further analysis

User request: {user_prompt}

Please use Python code to create professional, well-labeled charts with appropriate titles and legends.
"""
    elif analysis_type == "custom":
        base_prompt = f"""
Analyze the uploaded file '{file_name}' based on this specific request:

{user_prompt}

Please read the file first, then fulfill the user's specific requirements.
"""
    else:
        # For non-data files or general analysis
        base_prompt = f"""
Analyze the uploaded file '{file_name}':

{user_prompt}

Please read and process the file content appropriately.
"""
    
    # Add specific chart types if requested
    if chart_types and is_data_file:
        chart_list = ", ".join(chart_types)
        base_prompt += f"\n\nAdditionally, make sure to create these specific chart types: {chart_list}"
    
    return base_prompt

async def process_bedrock_response(response) -> dict:
    """Process streaming response from Bedrock"""
    completion_text = ""
    generated_files = []
    
    def process_stream():
        nonlocal completion_text, generated_files
        
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                
                # Handle text response
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    completion_text += chunk_text
                
                # Handle generated files
                if 'files' in chunk:
                    for file_info in chunk['files']:
                        if 'data' in file_info:
                            filename = file_info.get('name', f'generated_{uuid.uuid4().hex[:8]}.png')
                            file_data = file_info['data']
                            
                            # Save file to temp directory
                            temp_dir = "temp_files"
                            os.makedirs(temp_dir, exist_ok=True)
                            file_path = os.path.join(temp_dir, filename)
                            
                            with open(file_path, 'wb') as f:
                                f.write(file_data)
                            
                            generated_files.append({
                                'name': filename,
                                'path': file_path,
                                'size': len(file_data),
                                'type': 'image' if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')) else 'file'
                            })
    
    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, process_stream)
    
    return {
        'text': completion_text,
        'files': generated_files
    }

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize AWS clients on startup"""
    refresh_credentials()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Bedrock Data Visualization API",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Bedrock client
        if not bedrock_client:
            refresh_credentials()
        
        return {
            "status": "healthy",
            "bedrock_region": BEDROCK_REGION,
            "agent_configured": bool(AGENT_ID and AGENT_ALIAS_ID),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.post("/visualize", response_model=VisualizationResponse)
async def visualize_data(request: FileVisualizationRequest):
    """Main endpoint: Create visualizations from base64 file data"""
    start_time = datetime.now()
    
    try:
        if not bedrock_client:
            refresh_credentials()
        
        logger.info(f"Processing visualization request for file: {request.file_name}")
        
        # Decode file content
        try:
            file_data = base64.b64decode(request.file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 file content: {str(e)}")
        
        # Validate file size
        is_valid, size_message = validate_file_size(file_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=size_message)
        
        logger.info(f"File size validation passed: {size_message}")
        
        # Determine use case
        if request.use_case == "auto":
            use_cases = determine_use_case(request.file_name, request.file_type, request.prompt)
        elif request.use_case == "both":
            use_cases = ["CHAT", "CODE_INTERPRETER"]
        else:
            use_cases = [request.use_case.upper().replace("CODE_INTERPRETER", "CODE_INTERPRETER")]
        
        logger.info(f"Determined use cases: {use_cases}")
        
        # Validate file type
        file_ext = os.path.splitext(request.file_name.lower())[1]
        if file_ext not in {**SUPPORTED_DATA_FILES, **SUPPORTED_DOCUMENT_FILES}:
            logger.warning(f"Potentially unsupported file type: {file_ext}")
        
        # Create enhanced prompt for visualization
        viz_prompt = create_visualization_prompt(
            request.prompt, 
            request.analysis_type, 
            request.chart_types,
            request.file_name
        )
        
        # Build session state with files
        files_config = []
        for use_case in use_cases:
            files_config.append({
                "name": request.file_name,
                "source": {
                    "sourceType": "BYTE_CONTENT",
                    "byteContent": {
                        "data": file_data,
                        "mediaType": request.file_type
                    }
                },
                "useCase": use_case
            })
        
        session_id = request.session_id or str(uuid.uuid4())
        
        # Prepare Bedrock agent request
        kwargs = {
            "agentId": AGENT_ID,
            "agentAliasId": AGENT_ALIAS_ID,
            "sessionId": session_id,
            "inputText": viz_prompt,
            "sessionState": {"files": files_config},
            "streamingConfigurations": {
                "streamFinalResponse": True,
                "applyGuardrailInterval": 20
            }
        }
        
        logger.info(f"Invoking Bedrock agent with session: {session_id}")
        
        # Invoke Bedrock agent
        response = bedrock_client.invoke_agent(**kwargs)
        
        # Process streaming response
        result = await process_bedrock_response(response)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare file information for frontend
        generated_files = []
        for file_info in result['files']:
            generated_files.append({
                "name": file_info['name'],
                "download_url": f"/files/{file_info['name']}",
                "file_type": file_info['type'],
                "size_bytes": file_info['size']
            })
        
        logger.info(f"Analysis completed successfully in {execution_time:.2f}s. Generated {len(generated_files)} files.")
        
        return VisualizationResponse(
            session_id=session_id,
            response_text=result['text'],
            generated_files=generated_files,
            analysis_summary={
                "file_name": request.file_name,
                "file_size_mb": round(len(file_data) / (1024 * 1024), 2),
                "mime_type": request.file_type,
                "use_cases": use_cases,
                "charts_generated": len([f for f in result['files'] if f['type'] == 'image']),
                "analysis_type": request.analysis_type,
                "prompt_length": len(viz_prompt)
            },
            execution_time=execution_time,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in visualize_data: {str(e)}")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return VisualizationResponse(
            session_id=request.session_id or "error",
            response_text=f"Error occurred during analysis: {str(e)}",
            generated_files=[],
            analysis_summary={"error": str(e)},
            execution_time=execution_time,
            success=False
        )

@app.post("/visualize/upload")
async def visualize_upload_fallback(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    analysis_type: str = Form(default="comprehensive"),
    session_id: str = Form(default="")
):
    """Fallback endpoint for multipart form uploads (converts to main endpoint)"""
    
    try:
        # Read file content and convert to base64
        file_content = await file.read()
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        # Create request for main endpoint
        request = FileVisualizationRequest(
            prompt=prompt,
            file_name=file.filename,
            file_content=file_content_b64,
            file_type=file.content_type or "application/octet-stream",
            session_id=session_id or str(uuid.uuid4()),
            analysis_type=analysis_type,
            use_case="auto"
        )
        
        # Process through main endpoint
        return await visualize_data(request)
        
    except Exception as e:
        logger.error(f"Error in visualize_upload_fallback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def get_generated_file(filename: str):
    """Download generated visualization files"""
    file_path = os.path.join("temp_files", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.delete("/files/{filename}")
async def delete_generated_file(filename: str):
    """Delete generated file"""
    file_path = os.path.join("temp_files", filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": f"File {filename} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "data_files": SUPPORTED_DATA_FILES,
        "document_files": SUPPORTED_DOCUMENT_FILES,
        "limits": {
            "max_file_size_mb": 10,
            "supported_use_cases": ["CHAT", "CODE_INTERPRETER"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
