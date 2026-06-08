import { useState } from 'react';
import { Pause, Play, X, Snowflake, EyeOff, Eye } from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';

interface InterviewViewProps {
  onEndSession: () => void;
  onFreeze: () => void;
  onUnfreeze: () => void;
  isFrozen: boolean;
  transcript: string;
  llmHint: string;
}

export const InterviewView = ({
  onEndSession,
  onFreeze,
  onUnfreeze,
  isFrozen,
  transcript,
  llmHint,
}: InterviewViewProps) => {
  const [isStealthEnabled, setIsStealthEnabled] = useState(false);
  const [stealthStatus, setStealthStatus] = useState<'idle' | 'success' | 'error'>('idle');

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
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="font-semibold">Interview Active</span>
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

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex flex-col gap-4 p-6">
        {/* Transcript Section */}
        <div className="flex-1 bg-slate-800 rounded-lg border border-slate-700 p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-300 text-sm uppercase tracking-wide">
              Live Transcript
            </h3>
          </div>
          <div className="text-slate-100 leading-relaxed whitespace-pre-wrap">
            {transcript || (
              <p className="text-slate-500 italic">Waiting for audio input...</p>
            )}
          </div>
        </div>

        {/* AI Hints Section */}
        <div className="flex-1 bg-gradient-to-br from-blue-900/20 to-purple-900/20 rounded-lg border border-blue-700/30 p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-blue-300 text-sm uppercase tracking-wide">
              AI Suggestions
            </h3>
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          </div>
          <div className="text-slate-100 leading-relaxed whitespace-pre-wrap">
            {llmHint || (
              <p className="text-slate-500 italic">AI suggestions will appear here...</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions Bottom Bar */}
      <div className="bg-slate-800 border-t border-slate-700 px-6 py-4 flex items-center justify-center gap-4">
        <button
          onClick={handleFreezeToggle}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-colors ${
            isFrozen
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
          }`}
        >
          {isFrozen ? <Play size={20} /> : <Pause size={20} />}
          {isFrozen ? 'Resume' : 'Freeze'}
        </button>

        <button
          onClick={onEndSession}
          className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors"
        >
          <X size={20} />
          End Session
        </button>
      </div>

      {/* Stealth Status Notification */}
      {stealthStatus !== 'idle' && (
        <div className={`fixed bottom-20 right-6 px-4 py-2 rounded-lg text-sm font-semibold ${
          stealthStatus === 'success'
            ? 'bg-green-600 text-white'
            : 'bg-red-600 text-white'
        }`}>
          {stealthStatus === 'success'
            ? (isStealthEnabled ? 'Stealth Mode Enabled' : 'Stealth Mode Disabled')
            : 'Stealth Mode Not Supported (Windows only)'}
        </div>
      )}
    </div>
  );
};
