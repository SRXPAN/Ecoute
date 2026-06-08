import { useState, useEffect } from 'react';
import { Settings, Mic, User, Rocket, Upload, CheckCircle, AlertCircle, Speaker } from 'lucide-react';

interface SetupViewProps {
  onStartInterview: (config: InterviewConfig) => void;
}

interface InterviewConfig {
  mic_index: number | null;
  speaker_index: number | null;
  persona: string;
  context: string;
}

interface AudioDevice {
  index: number;
  name: string;
  channels: number;
  sample_rate: number;
}

type TabType = 'audio' | 'context' | 'personas';

export const SetupView = ({ onStartInterview }: SetupViewProps) => {
  const [activeTab, setActiveTab] = useState<TabType>('audio');

  // Audio state
  const [microphones, setMicrophones] = useState<AudioDevice[]>([]);
  const [speakers, setSpeakers] = useState<AudioDevice[]>([]);
  const [selectedMicIndex, setSelectedMicIndex] = useState<number | null>(null);
  const [selectedSpeakerIndex, setSelectedSpeakerIndex] = useState<number | null>(null);
  const [audioDevicesLoading, setAudioDevicesLoading] = useState(true);

  // Context state
  const [contextText, setContextText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState('');

  // Persona state
  const [selectedPersona, setSelectedPersona] = useState('Short Bullets');

  const personas = [
    {
      id: 'Short Bullets',
      name: 'Short Bullets',
      description: 'Concise bullet points (max 3, 10 words each)',
      icon: '🎯'
    },
    {
      id: 'Technical Deep Dive',
      name: 'Technical Deep Dive',
      description: 'Architecture, tech stacks, SDLC focus',
      icon: '⚙️'
    },
    {
      id: 'STAR Method',
      name: 'STAR Method',
      description: 'Situation, Task, Action, Result format',
      icon: '⭐'
    },
    {
      id: 'Coach Advice',
      name: 'Coach Advice',
      description: 'Strategic coaching instructions',
      icon: '🎓'
    }
  ];

  // Fetch audio devices on mount
  useEffect(() => {
    const fetchAudioDevices = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/audio-devices');
        const data = await response.json();

        if (data.success) {
          setMicrophones(data.microphones);
          setSpeakers(data.speakers);

          // Auto-select first devices if available
          if (data.microphones.length > 0 && selectedMicIndex === null) {
            setSelectedMicIndex(data.microphones[0].index);
          }
          if (data.speakers.length > 0 && selectedSpeakerIndex === null) {
            setSelectedSpeakerIndex(data.speakers[0].index);
          }
        }
      } catch (error) {
        console.error('[SetupView] Failed to fetch audio devices:', error);
      } finally {
        setAudioDevicesLoading(false);
      }
    };

    fetchAudioDevices();
  }, [selectedMicIndex, selectedSpeakerIndex]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setUploadStatus('idle');
      setUploadMessage('');
    } else {
      setUploadMessage('Please select a valid PDF file');
      setUploadStatus('error');
    }
  };

  const handleUploadContext = async () => {
    if (!selectedFile) return;

    setUploadStatus('uploading');
    setUploadMessage('Uploading & Parsing PDF...');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://127.0.0.1:8000/api/upload_context', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setContextText(data.extracted_text);
        setUploadStatus('success');
        setUploadMessage(`Extracted ${data.extracted_text.length} characters successfully!`);
      } else {
        setUploadStatus('error');
        setUploadMessage(data.message || 'Upload failed');
      }
    } catch (error) {
      setUploadStatus('error');
      setUploadMessage('Failed to connect to backend. Is server.py running?');
      console.error('[SetupView] Upload error:', error);
    }
  };

  const handleStartInterview = () => {
    const config: InterviewConfig = {
      mic_index: selectedMicIndex,
      speaker_index: selectedSpeakerIndex,
      persona: selectedPersona,
      context: contextText
    };

    onStartInterview(config);
  };

  const renderAudioTab = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Mic size={20} className="text-blue-400" />
          Microphone Input
        </h3>
        {audioDevicesLoading ? (
          <div className="text-slate-400 text-sm animate-pulse">Scanning microphones...</div>
        ) : microphones.length > 0 ? (
          <select
            value={selectedMicIndex ?? ''}
            onChange={(e) => setSelectedMicIndex(Number(e.target.value))}
            className="w-full px-4 py-3 bg-slate-700 text-slate-100 rounded-lg border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-all cursor-pointer"
          >
            {microphones.map((mic) => (
              <option key={mic.index} value={mic.index}>
                {mic.name}
              </option>
            ))}
          </select>
        ) : (
          <div className="p-4 bg-red-900/20 border border-red-900/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
            <AlertCircle size={16} />
            No microphones detected. Please check permissions.
          </div>
        )}
      </div>

      <div>
        <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Speaker size={20} className="text-purple-400" />
          Speaker Loopback (System Audio)
        </h3>
        {audioDevicesLoading ? (
          <div className="text-slate-400 text-sm animate-pulse">Scanning output devices...</div>
        ) : speakers.length > 0 ? (
          <select
            value={selectedSpeakerIndex ?? ''}
            onChange={(e) => setSelectedSpeakerIndex(Number(e.target.value))}
            className="w-full px-4 py-3 bg-slate-700 text-slate-100 rounded-lg border border-slate-600 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-all cursor-pointer"
          >
            {speakers.map((speaker) => (
              <option key={speaker.index} value={speaker.index}>
                {speaker.name}
              </option>
            ))}
          </select>
        ) : (
          <div className="p-4 bg-red-900/20 border border-red-900/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
            <AlertCircle size={16} />
            No loopback devices detected. Is WASAPI supported?
          </div>
        )}
      </div>

      <div className="bg-slate-700/50 border border-slate-600/50 rounded-xl p-5">
        <h4 className="text-sm font-bold text-slate-300 mb-2 uppercase tracking-wider">How it works</h4>
        <p className="text-slate-400 text-sm leading-relaxed">
          The <span className="text-blue-400 font-medium">Microphone</span> captures your responses. 
          The <span className="text-purple-400 font-medium">Speaker Loopback</span> captures the interviewer's questions from apps like Zoom, Teams, or Google Meet.
          Both are processed in real-time to generate AI hints.
        </p>
      </div>
    </div>
  );

  const renderContextTab = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div>
        <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
          <Upload size={20} className="text-green-400" />
          Interview Context (PDF Resume/Job Desc)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="group relative cursor-pointer">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="flex flex-col items-center justify-center px-4 py-8 bg-slate-700 hover:bg-slate-600 border-2 border-dashed border-slate-600 group-hover:border-green-500/50 rounded-xl transition-all">
              <Upload className={`mb-3 ${selectedFile ? 'text-green-400' : 'text-slate-400'}`} size={32} />
              <span className="text-slate-300 font-medium text-center truncate w-full px-4">
                {selectedFile ? selectedFile.name : 'Select PDF File'}
              </span>
              <span className="text-slate-500 text-xs mt-1">Maximum size 10MB</span>
            </div>
          </label>

          <div className="flex flex-col justify-center gap-3">
            <button
              onClick={handleUploadContext}
              disabled={!selectedFile || uploadStatus === 'uploading'}
              className="w-full px-6 py-4 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed text-white rounded-xl transition-all font-bold shadow-lg shadow-green-900/20"
            >
              {uploadStatus === 'uploading' ? 'Processing...' : 'Auto-Extract Text'}
            </button>
            
            {uploadStatus !== 'idle' && (
              <div className={`flex items-center gap-2 text-sm p-3 rounded-lg ${
                uploadStatus === 'success' ? 'bg-green-500/10 text-green-400' :
                uploadStatus === 'error' ? 'bg-red-500/10 text-red-400' :
                'bg-blue-500/10 text-blue-400'
              }`}>
                {uploadStatus === 'success' && <CheckCircle size={18} />}
                {uploadStatus === 'error' && <AlertCircle size={18} />}
                <span className="font-medium">{uploadMessage}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="relative">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">
          Final Context (Editable)
        </h3>
        <textarea
          value={contextText}
          onChange={(e) => setContextText(e.target.value)}
          placeholder="Paste your resume or job description here. The AI uses this to tailor its answers to your experience..."
          className="w-full h-80 px-5 py-4 bg-slate-700 text-slate-100 rounded-xl border border-slate-600 focus:border-green-500 focus:ring-1 focus:ring-green-500 focus:outline-none transition-all resize-none font-mono text-sm leading-relaxed"
        />
        <div className="absolute bottom-4 right-4 px-3 py-1 bg-slate-800/80 rounded-full text-[10px] text-slate-500 font-bold uppercase tracking-widest border border-slate-700">
          {contextText.length} Chars
        </div>
      </div>
    </div>
  );

  const renderPersonasTab = () => (
    <div className="space-y-6 animate-in fade-in duration-300">
      <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
        <User size={20} className="text-amber-400" />
        Choose AI Persona
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {personas.map((persona) => (
          <button
            key={persona.id}
            onClick={() => setSelectedPersona(persona.id)}
            className={`group p-6 rounded-2xl border-2 transition-all text-left relative overflow-hidden ${
              selectedPersona === persona.id
                ? 'border-amber-500 bg-amber-500/10'
                : 'border-slate-700 bg-slate-800 hover:border-slate-600 hover:bg-slate-700/50'
            }`}
          >
            {selectedPersona === persona.id && (
              <div className="absolute top-0 right-0 p-2 text-amber-500">
                <CheckCircle size={20} />
              </div>
            )}
            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">{persona.icon}</div>
            <h4 className={`font-bold text-lg mb-1 ${selectedPersona === persona.id ? 'text-amber-400' : 'text-slate-100'}`}>
              {persona.name}
            </h4>
            <p className="text-slate-400 text-sm leading-relaxed">{persona.description}</p>
          </button>
        ))}
      </div>
      <div className="p-4 bg-amber-900/10 border border-amber-900/20 rounded-xl text-amber-200/70 text-xs italic">
        Tip: Switch to "STAR Method" for behavioral questions, and "Technical Deep Dive" for coding or system design interviews.
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <div className="w-72 bg-slate-800/50 border-r border-slate-800 p-8 flex flex-col">
        <div className="flex items-center gap-3 mb-12">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Rocket size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight">ECOUTE</h1>
            <p className="text-[10px] text-blue-400 font-bold uppercase tracking-[0.2em] -mt-1">Copilot</p>
          </div>
        </div>

        <nav className="space-y-3 flex-1">
          <button
            onClick={() => setActiveTab('audio')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl font-bold transition-all ${
              activeTab === 'audio'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
            }`}
          >
            <Mic size={20} />
            <span>Audio Setup</span>
          </button>

          <button
            onClick={() => setActiveTab('context')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl font-bold transition-all ${
              activeTab === 'context'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
            }`}
          >
            <User size={20} />
            <span>My Context</span>
          </button>

          <button
            onClick={() => setActiveTab('personas')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl font-bold transition-all ${
              activeTab === 'personas'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
            }`}
          >
            <Settings size={20} />
            <span>Persona</span>
          </button>
        </nav>

        <div className="pt-8 border-t border-slate-800">
          <div className="flex items-center gap-3 p-3 bg-slate-900/50 rounded-xl border border-slate-800/50">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">System Ready</span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col p-12 overflow-y-auto bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="max-w-4xl mx-auto w-full">
          <div className="mb-10">
            <h2 className="text-4xl font-black text-white mb-3">
              {activeTab === 'audio' && 'Audio Configuration'}
              {activeTab === 'context' && 'Knowledge Base'}
              {activeTab === 'personas' && 'AI Intelligence'}
            </h2>
            <p className="text-slate-400 text-lg">
              {activeTab === 'audio' && 'Select your input and output devices for real-time capture.'}
              {activeTab === 'context' && 'Provide context about yourself to get personalized answers.'}
              {activeTab === 'personas' && 'Select the response style that best fits your interview type.'}
            </p>
          </div>

          {/* Configuration Card */}
          <div className="bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 rounded-[2rem] p-10 shadow-2xl mb-10 min-h-[500px]">
            {activeTab === 'audio' && renderAudioTab()}
            {activeTab === 'context' && renderContextTab()}
            {activeTab === 'personas' && renderPersonasTab()}
          </div>

          {/* Action Bar */}
          <div className="flex flex-col items-center">
            <button
              onClick={handleStartInterview}
              disabled={selectedSpeakerIndex === null}
              className="group relative w-full max-w-md px-10 py-6 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed text-white font-black text-xl rounded-[1.5rem] transition-all duration-300 shadow-2xl shadow-blue-600/20 hover:shadow-blue-600/40 hover:-translate-y-1"
            >
              <div className="flex items-center justify-center gap-4">
                <Rocket size={28} className="group-hover:animate-bounce" />
                <span>LAUNCH COPILOT</span>
              </div>
            </button>
            
            {selectedSpeakerIndex === null && (
              <p className="flex items-center gap-2 text-red-400 text-xs font-bold mt-4 uppercase tracking-widest animate-pulse">
                <AlertCircle size={14} />
                Speaker device required to continue
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
