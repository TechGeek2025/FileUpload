async def bedrock_stream_generator(
    file_data: bytes, 
    file_name: str, 
    file_type: str, 
    prompt: str,
    session_id: str
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events from Bedrock streaming response
    """
    try:
        # Mark stream as active
        active_streams[session_id] = True
        
        # Send initial status
        yield f"event: status\ndata: {json.dumps({'message': 'Starting analysis...', 'session_id': session_id})}\n\n"
        
        # Determine use case
        use_case = determine_use_case(file_name, file_type, prompt)
        
        # Prepare Bedrock request
        kwargs = {
            "agentId": agent_id,
            "agentAliasId": agent_alias_id,
            "sessionId": session_id,
            "inputText": prompt,
            "sessionState": {
                "files": [
                    {
                        "name": file_name,
                        "source": {
                            "sourceType": "BYTE_CONTENT",
                            "byteContent": {
                                "data": file_data,
                                "mediaType": file_type
                            }
                        },
                        "useCase": use_case
                    }
                ]
            },
            "streamingConfigurations": {
                "streamFinalResponse": True,
                "applyGuardrailInterval": 20,
            }
        }
        
        # Invoke Bedrock agent
        response = client.invoke_agent(**kwargs)
        
        file_counter = 0
        text_buffer = ""
        
        # Process Bedrock response
        for event in response.get('completion', []):
            # Check if stream is still active
            if not active_streams.get(session_id, False):
                break
                
            if 'chunk' in event:
                chunk = event['chunk']
                
                # Handle streaming text
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    text_buffer += chunk_text
                    
                    # Send text chunk as SSE
                    yield f"event: text\ndata: {json.dumps({'content': chunk_text, 'session_id': session_id})}\n\n"
                
                # Handle generated files (charts/graphs)
                if 'files' in chunk:
                    for file_info in chunk['files']:
                        if 'data' in file_info:
                            file_counter += 1
                            filename = file_info.get('name', f'chart_{file_counter}.png')
                            file_data_bytes = file_info['data']
                            
                            # Convert to base64 for frontend
                            file_base64 = base64.b64encode(file_data_bytes).decode('utf-8')
                            
                            # Determine file type
                            file_mime_type = get_file_type(filename)
                            
                            # Send chart as SSE
                            chart_data = {
                                'filename': filename,
                                'data': file_base64,
                                'type': file_mime_type,
                                'size': len(file_data_bytes),
                                'session_id': session_id
                            }
                            
                            yield f"event: chart\ndata: {json.dumps(chart_data)}\n\n"
            
            # Handle trace events (progress updates)
            if 'trace' in event:
                trace = event['trace']
                if 'trace' in trace:
                    trace_data = trace['trace']
                    
                    # Send progress updates
                    if 'codeInterpreterInvocationInput' in str(trace_data):
                        yield f"event: status\ndata: {json.dumps({'message': 'Generating charts...', 'session_id': session_id})}\n\n"
                    
                    if 'codeInterpreterInvocationOutput' in str(trace_data):
                        yield f"event: status\ndata: {json.dumps({'message': 'Code execution completed', 'session_id': session_id})}\n\n"
        
        # Send completion event
        completion_data = {
            'session_id': session_id,
            'total_files': file_counter,
            'total_text_length': len(text_buffer),
            'message': f'Analysis complete! Generated {file_counter} files.'
        }
        yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
        
    except Exception as e:
        error_data = {
            'error': str(e),
            'session_id': session_id
        }
        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    finally:
        # Clean up
        active_streams.pop(session_id, None)

def get_file_type(filename: str) -> str:
    """Determine MIME type from filename"""
    ext = filename.lower().split('.')[-1]
    type_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'svg': 'image/svg+xml',
        'html': 'text/html',
        'csv': 'text/csv',
        'json': 'application/json',
        'pdf': 'application/pdf'
    }
    return type_map.get(ext, 'application/octet-stream')

def determine_use_case(file_name: str, file_type: str, prompt: str) -> str:
    """Determine whether to use CHAT or CODE_INTERPRETER"""
    if any(keyword in prompt.lower() for keyword in ['chart', 'graph', 'visualize', 'analyze']):
        return "CODE_INTERPRETER"
    elif file_name.lower().endswith(('.csv', '.xlsx', '.xls')):
        return "CODE_INTERPRETER"
    else:
        return "CHAT"
