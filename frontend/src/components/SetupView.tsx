import { useState } from 'react';
import { Settings, Mic, User, Rocket, Upload, CheckCircle, AlertCircle } from 'lucide-react';

interface SetupViewProps {
  onStartInterview: () => void;
}

export const SetupView = ({ onStartInterview }: SetupViewProps) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setUploadStatus('idle');
    } else {
      setUploadMessage('Please select a valid PDF file');
      setUploadStatus('error');
    }
  };

  const handleUploadContext = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setUploadMessage('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://127.0.0.1:8000/api/upload_context', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setUploadStatus('success');
        setUploadMessage(`Context loaded: ${data.context_length} characters`);
      } else {
        setUploadStatus('error');
        setUploadMessage(data.message || 'Upload failed');
      }
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage('Failed to upload file. Is the backend running?');
      console.error('[SetupView] Upload error:', error);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="w-64 bg-slate-800 border-r border-slate-700 p-4">
        <div className="mb-8">
          <h1 className="text-xl font-bold text-slate-100">Interview Copilot</h1>
          <p className="text-xs text-slate-400 mt-1">AI Assistant</p>
        </div>

        <nav className="space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors">
            <Mic size={20} />
            <span>Audio Setup</span>
          </button>

          <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors">
            <User size={20} />
            <span>Context</span>
          </button>

          <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors">
            <Settings size={20} />
            <span>Personas</span>
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="max-w-2xl text-center">
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-blue-500/10 rounded-full mb-6">
              <Rocket size={48} className="text-blue-400" />
            </div>
            <h2 className="text-4xl font-bold text-slate-100 mb-4">
              Ready to Start Your Interview
            </h2>
            <p className="text-slate-400 text-lg">
              Click the button below to activate your AI copilot. Real-time transcription and suggestions will appear during your call.
            </p>
          </div>

          {/* PDF Upload Section */}
          <div className="mb-8 bg-slate-800 p-6 rounded-lg border border-slate-700">
            <h3 className="text-slate-100 font-semibold mb-4 flex items-center gap-2">
              <Upload size={20} />
              Upload Your Resume (Optional)
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Upload a PDF resume to provide context for AI suggestions
            </p>

            <div className="flex flex-col gap-3">
              <label className="cursor-pointer">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div className="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors text-center">
                  {selectedFile ? selectedFile.name : 'Choose PDF file'}
                </div>
              </label>

              {selectedFile && (
                <button
                  onClick={handleUploadContext}
                  disabled={uploadStatus === 'uploading'}
                  className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-semibold"
                >
                  {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload Context'}
                </button>
              )}

              {uploadStatus !== 'idle' && (
                <div className={`flex items-center gap-2 text-sm ${
                  uploadStatus === 'success' ? 'text-green-400' :
                  uploadStatus === 'error' ? 'text-red-400' :
                  'text-blue-400'
                }`}>
                  {uploadStatus === 'success' && <CheckCircle size={16} />}
                  {uploadStatus === 'error' && <AlertCircle size={16} />}
                  <span>{uploadMessage}</span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={onStartInterview}
            className="inline-flex items-center gap-3 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-lg rounded-xl transition-colors shadow-lg shadow-blue-500/20"
          >
            <Rocket size={24} />
            Start Copilot
          </button>

          <div className="mt-12 grid grid-cols-3 gap-6 text-left">
            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
              <h3 className="text-slate-100 font-semibold mb-2">Real-time Transcription</h3>
              <p className="text-slate-400 text-sm">Automatic speech-to-text from your interview</p>
            </div>

            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
              <h3 className="text-slate-100 font-semibold mb-2">AI Suggestions</h3>
              <p className="text-slate-400 text-sm">Smart hints based on context and questions</p>
            </div>

            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
              <h3 className="text-slate-100 font-semibold mb-2">Freeze Mode</h3>
              <p className="text-slate-400 text-sm">Pause processing when you need focus</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
