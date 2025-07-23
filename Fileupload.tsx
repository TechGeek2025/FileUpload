import React, { useState, useRef, type DragEvent } from 'react';
import './FileUpload.css';

interface UploadedFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
}

interface FileUploadProps {
  onFilesChange: (files: UploadedFile[]) => void;
  currentFiles: UploadedFile[]; // Current files from parent
  maxSizePerFile?: number; // in bytes
  acceptedFileTypes?: string[];
  disabled?: boolean; // Disable upload when true
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  onFilesChange,
  currentFiles,
  maxSizePerFile = 10 * 1024 * 1024, // 10MB default
  acceptedFileTypes = [
    '.pdf',
    '.doc',
    '.docx', 
    '.xls',
    '.xlsx',
    '.ppt',
    '.pptx',
    '.txt',
    '.rtf',
    '.csv'
  ],
  disabled = false
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file: File): string | null => {
    if (file.size > maxSizePerFile) {
      return `File "${file.name}" exceeds the maximum size of ${formatFileSize(maxSizePerFile)}`;
    }
    
    // Check if file type is a supported document type
    const isValidDocument = acceptedFileTypes.some(type => 
      file.name.toLowerCase().endsWith(type.toLowerCase())
    );
    
    if (!isValidDocument) {
             return `File "${file.name}" is not a supported document type. Please upload a PDF, Word, Excel, PowerPoint, or text file.`;
    }
    
    return null;
  };

  const processFiles = (files: FileList | File[]) => {
    if (disabled) return; // Don't process files if disabled
    
    const file = files[0]; // Only take the first file
    if (!file) return;

    // Check if a file is already uploaded
    if (currentFiles.length > 0) {
      setError('Please send the current message before uploading another file');
      setTimeout(() => setError(''), 5000);
      return;
    }

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setTimeout(() => setError(''), 5000);
      return;
    }

    setError('');

    const uploadedFile: UploadedFile = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      size: file.size,
      type: file.type
    };

    // Add the single file
    onFilesChange([uploadedFile]);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
      // Clear the input value so the same file can be selected again
      e.target.value = '';
    }
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled || currentFiles.length > 0) return; // Don't handle drag if disabled or file already uploaded
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (disabled || currentFiles.length > 0) return; // Don't handle drop if disabled or file already uploaded
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const openFileDialog = () => {
    if (disabled || currentFiles.length > 0) return; // Don't open if disabled or file already uploaded
    fileInputRef.current?.click();
  };

  return (
    <div className="file-upload-container">
      {/* Compact paperclip button */}
      <button
        className={`file-upload-btn ${disabled || currentFiles.length > 0 ? 'disabled' : ''}`}
        onClick={openFileDialog}
        title={disabled || currentFiles.length > 0 ? "Send message before uploading another file" : "Attach document"}
        disabled={disabled || currentFiles.length > 0}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66L9.64 16.2a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
        </svg>
      </button>
      
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileInput}
        className="file-input-hidden"
        accept={acceptedFileTypes.join(',')}
        disabled={disabled || currentFiles.length > 0}
      />
      
      {error && (
        <div className="file-upload-error">
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUpload; 
