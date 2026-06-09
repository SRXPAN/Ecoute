import { useEffect, useState, useMemo } from 'react';
import { Pause, Play, X, Snowflake, EyeOff, Eye, Clock, MessageSquare, Sparkles } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import ReactMarkdown from 'react-markdown';
import { InterviewSession } from '../App';

interface InterviewViewProps {
  onEndSession: () => void;
  onFreeze: () => void;
  onUnfreeze: () => void;
  isFrozen: boolean;
  sessions: InterviewSession[];
  currentSessionId: string | null;
  isSpeakingTooFast: boolean;
  sendMessage?: (message: any) => void;
  initialPersona?: string;
}

export const InterviewView = ({
  onEndSession,
  onFreeze,
  onUnfreeze,
  isFrozen,
  sessions,
  currentSessionId,
  isSpeakingTooFast,
  sendMessage,
  initialPersona = 'Short Bullets',
}: InterviewViewProps) => {
  const [isStealthEnabled, setIsStealthEnabled] = useState(false);
  const [stealthStatus, setStealthStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [showSpeakSlower, setShowSpeakSlower] = useState(false);
  const [activePersona, setActivePersona] = useState(initialPersona);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  // Automatically select the latest session when it changes
  useEffect(() => {
    if (sessions.length > 0 && (!selectedSessionId || selectedSessionId === sessions[1]?.id)) {
      setSelectedSessionId(sessions[0].id);
    }
  }, [sessions, selectedSessionId]);

  const selectedSession = useMemo(() => {
    return sessions.find(s => s.id === selectedSessionId) || sessions[0];
  }, [sessions, selectedSessionId]);

  useEffect(() => {
    if (!isSpeakingTooFast) {
      return;
    }

    setShowSpeakSlower(true);
    const timeout = window.setTimeout(() => {
      setShowSpeakSlower(false);
    }, 3000);

    return () => window.clearTimeout(timeout);
  }, [isSpeakingTooFast]);

  const handleFreezeToggle = () => {
    if (isFrozen) {
      onUnfreeze();
    } else {
      onFreeze();
    }
  };

  const handleStealthToggle = async () => {
    const newStealthState = !isStealthEnabled;

    try {
      const result = await invoke<string>('toggle_stealth', { enable: newStealthState });
      console.log('[InterviewView] Stealth toggle result:', result);

      setIsStealthEnabled(newStealthState);
      setStealthStatus('success');

      // Reset status after 2 seconds
      setTimeout(() => setStealthStatus('idle'), 2000);
    } catch (error) {
      console.error('[InterviewView] Stealth toggle failed:', error);
      setStealthStatus('error');

      // Reset status after 3 seconds
      setTimeout(() => setStealthStatus('idle'), 3000);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100 overflow-hidden">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="font-semibold">Copilot Active</span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-blue-400 font-medium">{activePersona}</span>
        </div>

        <div className="flex items-center gap-4">
          {isFrozen && (
            <div className="flex items-center gap-2 text-blue-400">
              <Snowflake size={16} />
              <span className="text-sm">Frozen</span>
            </div>
          )}

          {/* Stealth Mode Toggle */}
          <button
            onClick={handleStealthToggle}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
              isStealthEnabled
                ? 'bg-purple-600 hover:bg-purple-700 text-white'
                : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
            } ${stealthStatus === 'error' ? 'ring-2 ring-red-500' : ''}`}
            title={isStealthEnabled ? 'Stealth Mode: ON (Hidden from screen capture)' : 'Stealth Mode: OFF'}
          >
            {isStealthEnabled ? <EyeOff size={16} /> : <Eye size={16} />}
            <span>Stealth</span>
          </button>
        </div>
      </div>

      {showSpeakSlower && (
        <div className="mx-6 mt-4 rounded-2xl border border-amber-400/40 bg-amber-400/15 px-4 py-3 text-amber-100 shadow-[0_0_40px_rgba(251,191,36,0.12)] backdrop-blur-sm shrink-0">
          <div className="flex items-center justify-center gap-2 font-semibold tracking-wide">
            <span className="text-lg">⏳</span>
            <span>Speak Slower!</span>
          </div>
          <p className="mt-1 text-center text-xs text-amber-50/80">
            You’re talking quickly enough that the system may miss detail. Pause between thoughts.
          </p>
        </div>
      )}

      {/* Main Content Area: Sidebar + Active View */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar: Session History */}
        <div className="w-64 bg-slate-800/50 border-r border-slate-700 flex flex-col shrink-0">
          <div className="p-4 border-b border-slate-700">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Clock size={14} /> History
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {sessions.length === 0 ? (
              <p className="text-slate-600 text-xs text-center mt-8 italic">No entries yet</p>
            ) : (
              sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => setSelectedSessionId(session.id)}
                  className={`w-full text-left p-3 rounded-xl transition-all border ${
                    selectedSessionId === session.id
                      ? 'bg-indigo-600/20 border-indigo-500/50 text-indigo-100'
                      : 'border-transparent hover:bg-slate-700/50 text-slate-400'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-mono opacity-60">
                      {new Date(session.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                    {session.id === currentSessionId && (
                      <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></span>
                    )}
                  </div>
                  <p className="text-xs font-medium truncate leading-relaxed">
                    {session.transcript.replace(/^(Interviewer|Me): /, '')}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Active Session Content */}
        <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/50 p-6 gap-6">
          {selectedSession ? (
            <>
              {/* Transcript Section */}
              <div className="flex-1 flex flex-col min-h-0">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare size={16} className="text-slate-400" />
                  <h3 className="font-bold text-slate-400 text-xs uppercase tracking-widest">
                    Transcript
                  </h3>
                </div>
                <div className="flex-1 bg-slate-800/80 rounded-2xl border border-slate-700 p-5 overflow-y-auto shadow-inner">
                  <p className="text-slate-100 leading-relaxed whitespace-pre-wrap text-sm">
                    {selectedSession.transcript}
                  </p>
                </div>
              </div>

              {/* AI Hint Section */}
              <div className="flex-1 flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles size={16} className="text-indigo-400" />
                    <h3 className="font-bold text-indigo-400 text-xs uppercase tracking-widest">
                      AI Suggestion
                    </h3>
                  </div>
                  {selectedSession.id === currentSessionId && !selectedSession.isComplete && (
                    <span className="text-[10px] text-indigo-400 animate-pulse font-bold tracking-tighter">GENERATING...</span>
                  )}
                </div>
                <div className="flex-1 rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-5 shadow-lg shadow-indigo-950/20 overflow-y-auto">
                  <div className="text-slate-100 leading-relaxed">
                    {selectedSession.aiResponse ? (
                      <ReactMarkdown className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-li:my-1">
                        {selectedSession.aiResponse}
                      </ReactMarkdown>
                    ) : (
                      <p className="text-slate-600 italic text-sm">Waiting for response...</p>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 gap-4 opacity-50">
              <MessageSquare size={48} strokeWidth={1} />
              <p className="text-sm font-medium">Waiting for conversation to start...</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions Bottom Bar */}
      <div className="bg-slate-800/80 backdrop-blur-md border-t border-slate-700 px-6 py-4 flex items-center justify-center gap-4 shrink-0">
        <button
          onClick={handleFreezeToggle}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all ${
            isFrozen
              ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-900/20'
              : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
          }`}
        >
          {isFrozen ? <Play size={20} /> : <Pause size={20} />}
          {isFrozen ? 'Resume' : 'Freeze'}
        </button>

        <button
          onClick={onEndSession}
          className="flex items-center gap-2 px-6 py-3 bg-red-600/90 hover:bg-red-600 text-white rounded-xl font-bold transition-all shadow-lg shadow-red-900/20"
        >
          <X size={20} />
          End Session
        </button>
      </div>

      {/* Stealth Status Notification */}
      {stealthStatus !== 'idle' && (
        <div className={`fixed bottom-24 right-8 px-5 py-2.5 rounded-xl text-sm font-bold shadow-2xl transition-all animate-in slide-in-from-bottom-4 duration-300 ${
          stealthStatus === 'success'
            ? 'bg-green-600 text-white border border-green-500/50'
            : 'bg-red-600 text-white border border-red-500/50'
        }`}>
          {stealthStatus === 'success'
            ? (isStealthEnabled ? 'Stealth Mode Enabled' : 'Stealth Mode Disabled')
            : 'Stealth Mode Not Supported'}
        </div>
      )}
    </div>
  );
};
