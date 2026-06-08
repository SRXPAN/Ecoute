import { useState, useEffect } from 'react';
import { Settings, Mic, User, Rocket, Upload, CheckCircle, AlertCircle, Speaker, History, Clock3, Download, FileText, RefreshCw, ChevronRight, Sparkles } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

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

type TabType = 'audio' | 'context' | 'personas' | 'history';

interface SessionSummary {
  filename: string;
  date: string;
  duration_seconds: number;
  talk_ratio: number;
}

interface SessionLogEvent {
  type: string;
  speaker?: string;
  text?: string;
  timestamp?: string;
  duration_seconds?: number;
  wpm?: number;
  is_speaking_too_fast?: boolean;
  is_streaming?: boolean;
  complete?: boolean;
}

interface SessionDetail extends SessionSummary {
  session_id?: string;
  created_at?: string;
  ended_at?: string;
  talk_time_seconds?: number;
  persona?: string;
  context?: string;
  history_log: SessionLogEvent[];
}

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

  // History state
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState('');
  const [selectedSessionFilename, setSelectedSessionFilename] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null);
  const [selectedSessionLoading, setSelectedSessionLoading] = useState(false);

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
        const response = await fetch(`${API_BASE}/api/audio-devices`);
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
  }, []);

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

      const response = await fetch(`${API_BASE}/api/upload_context`, {
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

  useEffect(() => {
    if (activeTab !== 'history') {
      return;
    }

    const fetchSessions = async () => {
      setSessionsLoading(true);
      setSessionsError('');

      try {
        const response = await fetch(`${API_BASE}/api/sessions`);
        const data = await response.json();

        if (!response.ok || data.success === false) {
          throw new Error(data.detail || data.message || 'Failed to load sessions');
        }

        setSessions(data.sessions || []);
        if (data.sessions?.length) {
          setSelectedSessionFilename((current) => current || data.sessions[0].filename);
        }
      } catch (error) {
        console.error('[SetupView] Failed to load sessions:', error);
        setSessions([]);
        setSessionsError('Unable to load history right now. Check that the backend is running.');
      } finally {
        setSessionsLoading(false);
      }
    };

    fetchSessions();
  }, [activeTab]);

  useEffect(() => {
    if (activeTab !== 'history' || !selectedSessionFilename) {
      return;
    }

    const fetchSessionDetail = async () => {
      setSelectedSessionLoading(true);

      try {
        const response = await fetch(`${API_BASE}/api/sessions/${encodeURIComponent(selectedSessionFilename)}`);
        const data = await response.json();

        if (!response.ok || data.success === false) {
          throw new Error(data.detail || data.message || 'Failed to load session');
        }

        setSelectedSession(data.session);
      } catch (error) {
        console.error('[SetupView] Failed to load session detail:', error);
        setSelectedSession(null);
      } finally {
        setSelectedSessionLoading(false);
      }
    };

    fetchSessionDetail();
  }, [activeTab, selectedSessionFilename]);

  const formatDuration = (totalSeconds?: number) => {
    const seconds = Math.max(0, Math.round(totalSeconds || 0));
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toString().padStart(2, '0')}s`;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Unknown time';
    return new Date(timestamp).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const buildMarkdownExport = (session: SessionDetail) => {
    const lines = [
      `# Interview Session`,
      '',
      `- Date: ${session.created_at || session.date}`,
      `- Duration: ${formatDuration(session.duration_seconds)}`,
      `- Talk Time Ratio: ${(Math.max(0, Math.min(1, session.talk_ratio || 0)) * 100).toFixed(1)}%`,
      `- Persona: ${session.persona || 'N/A'}`,
      '',
      '## Timeline',
      ''
    ];

    session.history_log.forEach((event) => {
      const timestamp = formatTimestamp(event.timestamp);
      if (event.type === 'transcript') {
        lines.push(`- [${timestamp}] ${event.speaker || 'Speaker'}: ${event.text || ''}`);
      } else if (event.type === 'llm_hint') {
        lines.push(`- [${timestamp}] LLM Hint: ${event.text || ''}`);
      } else {
        lines.push(`- [${timestamp}] ${event.type}`);
      }
    });

    return lines.join('\n');
  };

  const handleExportMarkdown = () => {
    if (!selectedSession) return;

    const markdown = buildMarkdownExport(selectedSession);
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = selectedSession.filename.replace(/\.json$/i, '.md');
    anchor.click();
    URL.revokeObjectURL(url);
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

  const renderHistoryTab = () => {
    const ratio = Math.max(0, Math.min(1, selectedSession?.talk_ratio ?? 0));

    return (
      <div className="grid grid-cols-1 xl:grid-cols-[0.95fr_1.15fr] gap-6 animate-in fade-in duration-300">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <History size={20} className="text-cyan-400" />
              Session Archive
            </h3>
            <button
              onClick={() => setActiveTab('history')}
              className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-300 transition-colors hover:border-cyan-400/40 hover:text-cyan-300"
            >
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>

          {sessionsLoading ? (
            <div className="rounded-2xl border border-slate-700/60 bg-slate-800/50 p-8 text-center text-slate-400 animate-pulse">
              Loading past sessions...
            </div>
          ) : sessionsError ? (
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-5 text-rose-200">
              {sessionsError}
            </div>
          ) : sessions.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-700 bg-slate-800/30 p-8 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-700/70 text-cyan-300">
                <FileText size={28} />
              </div>
              <h4 className="text-lg font-semibold text-slate-100">No past sessions found</h4>
              <p className="mt-2 text-sm text-slate-400">
                Complete an interview and return here to review transcripts, AI hints, and performance metrics.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {sessions.map((sessionItem) => {
                const isSelected = selectedSessionFilename === sessionItem.filename;
                const talkPercent = Math.max(0, Math.min(100, (sessionItem.talk_ratio || 0) * 100));

                return (
                  <button
                    key={sessionItem.filename}
                    onClick={() => setSelectedSessionFilename(sessionItem.filename)}
                    className={`group rounded-3xl border p-5 text-left transition-all duration-200 hover:-translate-y-0.5 ${
                      isSelected
                        ? 'border-cyan-400/50 bg-cyan-400/10 shadow-[0_0_0_1px_rgba(34,211,238,0.15)]'
                        : 'border-slate-700/80 bg-slate-800/70 hover:border-slate-600 hover:bg-slate-700/70'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.24em] text-slate-500">
                          <Sparkles size={12} />
                          {formatTimestamp(sessionItem.date)}
                        </div>
                        <h4 className="mt-2 text-base font-semibold text-slate-100">{sessionItem.filename}</h4>
                      </div>
                      <ChevronRight className={`mt-1 transition-transform ${isSelected ? 'translate-x-1 text-cyan-300' : 'text-slate-500 group-hover:translate-x-1 group-hover:text-slate-300'}`} size={18} />
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-2xl bg-slate-900/60 px-3 py-3">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Duration</p>
                        <p className="mt-1 font-semibold text-slate-100">{formatDuration(sessionItem.duration_seconds)}</p>
                      </div>
                      <div className="rounded-2xl bg-slate-900/60 px-3 py-3">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Talk Ratio</p>
                        <p className="mt-1 font-semibold text-slate-100">{talkPercent.toFixed(1)}%</p>
                      </div>
                    </div>

                    <div className="mt-4">
                      <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-slate-500">
                        <span>Talk Time</span>
                        <span>Interview flow</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-900/70">
                        <div
                          className="h-full rounded-full bg-linear-to-r from-cyan-400 via-blue-400 to-emerald-400"
                          style={{ width: `${talkPercent}%` }}
                        />
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="rounded-4xl border border-slate-700/70 bg-slate-800/55 p-6 shadow-2xl shadow-slate-950/30">
          {selectedSessionLoading ? (
            <div className="flex h-full min-h-135 items-center justify-center text-slate-400 animate-pulse">
              Loading session details...
            </div>
          ) : selectedSession ? (
            <div className="flex h-full min-h-135 flex-col gap-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200">
                    <Clock3 size={12} />
                    Session Detail
                  </div>
                  <h3 className="mt-3 text-2xl font-black text-white">{selectedSession.filename}</h3>
                  <p className="mt-1 text-sm text-slate-400">{formatTimestamp(selectedSession.created_at || selectedSession.date)}</p>
                </div>

                <button
                  onClick={handleExportMarkdown}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-500 px-4 py-3 text-sm font-bold text-slate-950 transition-colors hover:bg-cyan-400"
                >
                  <Download size={16} />
                  Export to Markdown
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-500">Total Duration</p>
                  <p className="mt-2 text-2xl font-black text-white">{formatDuration(selectedSession.duration_seconds)}</p>
                </div>
                <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-500">Talk Time Ratio</p>
                  <p className="mt-2 text-2xl font-black text-white">{(ratio * 100).toFixed(1)}%</p>
                </div>
                <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
                  <p className="text-[10px] uppercase tracking-[0.24em] text-slate-500">Transcript Entries</p>
                  <p className="mt-2 text-2xl font-black text-white">{selectedSession.history_log.length}</p>
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-[0.24em] text-slate-500">
                  <span>Talk Ratio</span>
                  <span>{(ratio * 100).toFixed(1)}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-slate-900/80">
                  <div className="h-full rounded-full bg-linear-to-r from-cyan-400 to-emerald-400" style={{ width: `${ratio * 100}%` }} />
                </div>
              </div>

              <div className="flex-1 overflow-hidden rounded-3xl border border-slate-700/70 bg-slate-950/40">
                <div className="border-b border-slate-700/60 px-5 py-4">
                  <h4 className="text-sm font-bold uppercase tracking-[0.24em] text-slate-400">Timeline</h4>
                </div>
                <div className="max-h-80 overflow-y-auto p-5 space-y-3">
                  {selectedSession.history_log.length === 0 ? (
                    <p className="text-sm italic text-slate-500">No timeline events were captured for this session.</p>
                  ) : (
                    selectedSession.history_log.map((event, index) => {
                      const isHint = event.type === 'llm_hint';
                      const isFast = Boolean(event.is_speaking_too_fast);
                      const badgeClass = isHint ? 'bg-fuchsia-400/15 text-fuchsia-200 border-fuchsia-400/20' : 'bg-cyan-400/15 text-cyan-200 border-cyan-400/20';

                      return (
                        <div key={`${event.timestamp || 'event'}-${index}`} className={`rounded-2xl border p-4 ${isHint ? 'border-fuchsia-400/15 bg-fuchsia-400/5' : 'border-slate-700/80 bg-slate-900/60'}`}>
                          <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-slate-500">
                            <span className={`rounded-full border px-2 py-1 ${badgeClass}`}>{isHint ? 'LLM Hint' : event.speaker || event.type}</span>
                            <span>{formatTimestamp(event.timestamp)}</span>
                            {event.wpm ? <span>{event.wpm.toFixed(1)} WPM</span> : null}
                            {isFast ? <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-2 py-1 text-amber-200">Fast speech</span> : null}
                          </div>
                          <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-100">
                            {event.text || <span className="italic text-slate-500">No text captured.</span>}
                          </p>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex min-h-135 items-center justify-center rounded-3xl border border-dashed border-slate-700 bg-slate-900/20 text-center text-slate-400">
              <div>
                <FileText size={32} className="mx-auto mb-3 text-slate-500" />
                <p>Select a session to inspect its transcript and hints.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

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

          <button
            onClick={() => setActiveTab('history')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl font-bold transition-all ${
              activeTab === 'history'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/40'
                : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
            }`}
          >
            <History size={20} />
            <span>History</span>
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
      <div className="flex-1 flex flex-col p-12 overflow-y-auto bg-linear-to-br from-slate-900 to-slate-800">
        <div className="max-w-4xl mx-auto w-full">
          <div className="mb-10">
            <h2 className="text-4xl font-black text-white mb-3">
              {activeTab === 'audio' && 'Audio Configuration'}
              {activeTab === 'context' && 'Knowledge Base'}
              {activeTab === 'personas' && 'AI Intelligence'}
              {activeTab === 'history' && 'Interview History'}
            </h2>
            <p className="text-slate-400 text-lg">
              {activeTab === 'audio' && 'Select your input and output devices for real-time capture.'}
              {activeTab === 'context' && 'Provide context about yourself to get personalized answers.'}
              {activeTab === 'personas' && 'Select the response style that best fits your interview type.'}
              {activeTab === 'history' && 'Review previous sessions, compare metrics, and export the full timeline.'}
            </p>
          </div>

          {/* Configuration Card */}
          <div className="bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 rounded-4xl p-10 shadow-2xl mb-10 min-h-125">
            {activeTab === 'audio' && renderAudioTab()}
            {activeTab === 'context' && renderContextTab()}
            {activeTab === 'personas' && renderPersonasTab()}
            {activeTab === 'history' && renderHistoryTab()}
          </div>

          {/* Action Bar */}
          <div className="flex flex-col items-center">
            <button
              onClick={handleStartInterview}
              disabled={selectedSpeakerIndex === null}
              className="group relative w-full max-w-md px-10 py-6 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed text-white font-black text-xl rounded-3xl transition-all duration-300 shadow-2xl shadow-blue-600/20 hover:shadow-blue-600/40 hover:-translate-y-1"
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
