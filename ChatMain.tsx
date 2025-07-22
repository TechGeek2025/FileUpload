import React, { useState } from 'react';
import './ChatMain.css';
import FileUpload from './FileUpload';

const samplePrompts = [
  'Request and view time off',
  'What is Amazon Simple Notification Service publisher?',
  'How do I install Visual Studio?',
  'Who is <name>?',
  'Can I provide professional references for an employee?',
  'Rules for an access person',
  'Can I change my open enrollment elections once I have submitted them?',
  'insider trading rules',
];

const agentOptions = [
  { value: 'default', label: 'Default helper', description: 'Crewmate will configure for you' },
  { value: 'external', label: 'Search externally', description: 'Look outside of Vanguard via ChatHub' },
  { value: 'crew', label: 'General info for crew', description: 'CrewNet' },
  { value: 'dev', label: 'IT developer resources', description: 'DevAssist' },
  { value: 'content', label: 'Content creation tool', description: 'Writer' },
  { value: 'ethics', label: 'Ethical code info', description: 'Code' },
];

interface ChatMainProps {
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
}

const ChatMain: React.FC<ChatMainProps> = ({ darkMode, onToggleDarkMode }) => {
  const [agent, setAgent] = useState(agentOptions[0].value);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [message, setMessage] = useState('');

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getDocumentIcon = (fileName: string, fileType: string): string => {
    const extension = fileName.toLowerCase().split('.').pop() || '';
    
    if (fileType.includes('pdf') || extension === 'pdf') return '📄';
    if (extension === 'doc' || extension === 'docx') return '📝';
    if (extension === 'xls' || extension === 'xlsx') return '📊';
    if (extension === 'ppt' || extension === 'pptx') return '📋';
    if (extension === 'txt' || extension === 'rtf') return '📃';
    if (extension === 'csv') return '📈';
    
    return '📄'; // Default document icon
  };

  const handleFilesChange = (files: UploadedFile[]) => {
    setUploadedFiles(files);
  };

  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          // Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to convert file to base64'));
        }
      };
      reader.onerror = error => reject(error);
    });
  };

  const handleSendMessage = async () => {
    if (!message.trim() && uploadedFiles.length === 0) return;
    
    try {
      // Convert files to base64 format for backend
      const filesForBackend = await Promise.all(
        uploadedFiles.map(async (uploadedFile) => {
          const base64Content = await convertFileToBase64(uploadedFile.file);
          return {
            name: uploadedFile.name,
            type: uploadedFile.type,
            size: uploadedFile.size,
            content: base64Content, // Base64 encoded file content
            mimeType: uploadedFile.file.type
          };
        })
      );

      // Prepare the payload for your backend
      const payload = {
        message: message.trim(),
        files: filesForBackend,
        timestamp: new Date().toISOString(),
        agent: agent // Include the selected agent
      };

      console.log('Sending to backend:', payload);
      
      // Here you would make your API call to the backend
      // Example:
      // const response = await fetch('/api/chat', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(payload)
      // });
      
      // Reset form after successful submission
      setMessage('');
      setUploadedFiles([]);
      
    } catch (error) {
      console.error('Error processing files:', error);
      // You might want to show an error message to the user here
    }
  };

  return (
    <main className="chat-main">
      <button className="dark-toggle-btn chat-toggle-btn-topright" onClick={onToggleDarkMode} title="Toggle dark mode">
        {darkMode ? '🌙' : '☀️'}
      </button>
      <div className="chat-greeting">
        <h1>Hi, Prabesh</h1>
        <p className="chat-intro">Get answers, take action & connect to agents.<br />Introductory sample prompts to get you started.</p>
        <div className="chat-prompts">
          {samplePrompts.map((prompt, idx) => (
            <button className="chat-prompt-btn" key={idx} onClick={() => setMessage(prompt)}>{prompt}</button>
          ))}
        </div>
      </div>
      {uploadedFiles.length > 0 && (
        <div className="uploaded-files-section">
          <div className="uploaded-files-container">
            <div className="uploaded-files-header">
              <span className="uploaded-files-title">Attached documents ({uploadedFiles.length})</span>
            </div>
            <div className="uploaded-files-list">
              {uploadedFiles.map(file => (
                <div key={file.id} className="uploaded-file-item">
                  <div className="uploaded-file-info">
                    <span className="file-icon">{getDocumentIcon(file.name, file.file.type)}</span>
                    <div className="file-details">
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{formatFileSize(file.size)}</div>
                    </div>
                  </div>
                  <button
                    className="remove-file-btn"
                    onClick={() => {
                      const updatedFiles = uploadedFiles.filter(f => f.id !== file.id);
                      setUploadedFiles(updatedFiles);
                    }}
                    title="Remove file"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      <div className="chat-box-container">
        <div className="chat-box chat-box-large">
          <div className="chat-input-wrapper">
            <FileUpload onFilesChange={handleFilesChange} currentFiles={uploadedFiles} />
            <textarea 
              className="chat-input-area" 
              placeholder="How can CrewMate help you today?" 
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          <div className="chat-box-actions chat-box-actions-split">
            <div className="chat-agent-selector">
              <div className="chat-agent-label-main">Focus your ask:</div>
              <div className="chat-agent-dropdown" onClick={() => setDropdownOpen((o) => !o)} tabIndex={0} onBlur={() => setDropdownOpen(false)}>
                <div className="chat-agent-dropdown-selected">
                  <span className="chat-agent-label-bold">{agentOptions.find(a => a.value === agent)?.label}</span>
                  <span className="chat-agent-description">{agentOptions.find(a => a.value === agent)?.description}</span>
                </div>
                <svg className="chat-agent-caret" width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="#757575" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 8 10 12 14 8" /></svg>
                {dropdownOpen && (
                  <div className="chat-agent-dropdown-list">
                    {agentOptions.map(opt => (
                      <div
                        key={opt.value}
                        className={`chat-agent-dropdown-item${opt.value === agent ? ' selected' : ''}`}
                        onMouseDown={() => { setAgent(opt.value); setDropdownOpen(false); }}
                      >
                        <span className="chat-agent-label-bold">{opt.label}</span>
                        <span className="chat-agent-description">{opt.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <span className="chat-settings">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#757575" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 8 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 5 15.4a1.65 1.65 0 0 0-1.51-1V12a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 8 8.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82c.09.31.14.65.14 1v.18c0 .35-.05.69-.14 1z"/></svg>
              <span className="chat-settings-label">Default</span>
            </span>
            <button className="chat-send-btn" title="Send" onClick={handleSendMessage}>
              <span className="chat-send-icon">↑</span>
            </button>
          </div>
        </div>
        <div className="chat-footer-note">
          Generated content may contain errors <a href="#">View more...</a>
        </div>
      </div>
    </main>
  );
};

export default ChatMain; 
