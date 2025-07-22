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
  ]
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
      return `File "${file.name}" is not a supported document type. Please upload PDF, Word, Excel, PowerPoint, or text files.`;
    }
    
    return null;
  };

  const processFiles = (files: FileList | File[]) => {
    const newFiles: UploadedFile[] = [];
    const errors: string[] = [];

    Array.from(files).forEach(file => {
      const validationError = validateFile(file);
      if (validationError) {
        errors.push(validationError);
        return;
      }

      // Check if file already exists
      const fileExists = currentFiles.some(f => f.name === file.name && f.size === file.size);
      if (fileExists) {
        errors.push(`File "${file.name}" is already uploaded`);
        return;
      }

      const uploadedFile: UploadedFile = {
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        file,
        name: file.name,
        size: file.size,
        type: file.type
      };
      newFiles.push(uploadedFile);
    });

    if (errors.length > 0) {
      setError(errors.join(', '));
      setTimeout(() => setError(''), 5000);
    } else {
      setError('');
    }

    if (newFiles.length > 0) {
      const updatedFiles = [...currentFiles, ...newFiles];
      onFilesChange(updatedFiles);
    }
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
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="file-upload-container">
      {/* Compact paperclip button */}
      <button
        className="file-upload-btn"
        onClick={openFileDialog}
        title="Attach documents"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66L9.64 16.2a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
        </svg>
      </button>
      
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileInput}
        className="file-input-hidden"
        accept={acceptedFileTypes.join(',')}
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
