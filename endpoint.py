@app.post("/analyze-file-stream")
async def analyze_file_stream(request: FileAnalysisRequest):
    """
    Stream file analysis results using Server-Sent Events
    """
    try:
        # Generate session ID
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # Decode file content
        try:
            file_data = base64.b64decode(request.file_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 file data: {str(e)}")
        
        # Return streaming response
        return StreamingResponse(
            bedrock_stream_generator(
                file_data=file_data,
                file_name=request.file_name,
                file_type=request.file_type,
                prompt=request.prompt,
                session_id=session_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logging.error(f"Stream analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_streams": len(active_streams)}

# Optional: Endpoint to stop a specific stream
@app.post("/stop-stream/{session_id}")
async def stop_stream(session_id: str):
    active_streams[session_id] = False
    return {"message": f"Stream {session_id} stopped"}
