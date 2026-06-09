import { useState, useCallback, useEffect, useRef } from 'react';
import { getCurrentWindow, LogicalSize } from '@tauri-apps/api/window';
import { register, unregisterAll } from '@tauri-apps/plugin-global-shortcut';
import { useWebSocket } from './hooks/useWebSocket';
import { SetupView } from './components/SetupView';
import { InterviewView } from './components/InterviewView';

export interface InterviewHistoryEntry {
  id: number;
  timestamp: string;
  question: string;
  answer: string;
  isComplete: boolean;
}

function App() {
  const [isInterviewActive, setIsInterviewActive] = useState(false);
  const [isFrozen, setIsFrozen] = useState(false);
  const [historyEntries, setHistoryEntries] = useState<InterviewHistoryEntry[]>([]);
  const [activeHistoryId, setActiveHistoryId] = useState<number | null>(null);
  const [isSpeakingTooFast, setIsSpeakingTooFast] = useState(false);
  const fastSpeechTimeoutRef = useRef<number | null>(null);
  const processedMessagesRef = useRef<Set<string>>(new Set());
  const activeHistoryIdRef = useRef<number | null>(null);

  // Global Shortcut for Push-to-Talk
  useEffect(() => {
    const setupShortcut = async () => {
      try {
        await unregisterAll();
        await register('CommandOrControl+Alt', (event) => {
          if (event.state === 'Pressed') {
            console.log('[Shortcut] PTT Pressed');
            sendMessage({ action: 'toggle_mic', state: true });
          } else if (event.state === 'Released') {
            console.log('[Shortcut] PTT Released');
            sendMessage({ action: 'toggle_mic', state: false });
          }
        });
        console.log('[Shortcut] CommandOrControl+Alt registered');
      } catch (error) {
        console.error('[Shortcut] Registration failed:', error);
      }
    };

    if (isInterviewActive) {
      setupShortcut();
    } else {
      unregisterAll();
    }

    return () => {
      unregisterAll();
    };
  }, [isInterviewActive, sendMessage]);

  useEffect(() => {
    activeHistoryIdRef.current = activeHistoryId;
  }, [activeHistoryId]);

  // Handle window resizing based on mode
  useEffect(() => {
    const resizeWindow = async () => {
      try {
        const appWindow = getCurrentWindow();
        if (isInterviewActive) {
          // Compact mode for interview
          await appWindow.setSize(new LogicalSize(1000, 800));
        } else {
          // Large mode for setup
          await appWindow.setSize(new LogicalSize(1000, 800));
        }
      } catch (error) {
        console.error('Failed to resize window:', error);
      }
    };

    resizeWindow();
  }, [isInterviewActive]);

  const handleWebSocketMessage = useCallback((message: any) => {
    console.log('[App] Received message:', message);

    switch (message.type) {
      case 'transcript':
        // Deduplication logic to prevent double-appending
        const messageId = `${message.timestamp}-${message.text}`;
        if (processedMessagesRef.current.has(messageId)) {
          console.log('[App] Skipping duplicate transcript message:', messageId);
          return;
        }
        processedMessagesRef.current.add(messageId);

        const historyId = Number(message.history_id ?? Date.parse(message.timestamp));
        setActiveHistoryId(historyId);

        setHistoryEntries((prev) => {
          const nextEntry: InterviewHistoryEntry = {
            id: historyId,
            timestamp: message.timestamp,
            question: message.text,
            answer: '',
            isComplete: false,
          };

          const next = [...prev.filter((entry) => entry.id !== historyId), nextEntry];
          return next.sort((left, right) => left.id - right.id);
        });

        if (message.is_speaking_too_fast) {
          setIsSpeakingTooFast(true);

          if (fastSpeechTimeoutRef.current) {
            window.clearTimeout(fastSpeechTimeoutRef.current);
          }

          fastSpeechTimeoutRef.current = window.setTimeout(() => {
            setIsSpeakingTooFast(false);
            fastSpeechTimeoutRef.current = null;
          }, 3000);
        }
        break;

      case 'llm_hint':
        setHistoryEntries((prev) => {
          if (prev.length === 0) return prev;

          const targetHistoryId = Number(message.history_id ?? activeHistoryIdRef.current ?? prev[prev.length - 1]?.id);
          const activeIndex = prev.findIndex((entry) => entry.id === targetHistoryId);

          if (activeIndex < 0) return prev;

          const next = [...prev];

          if (message.clear) {
            next[activeIndex] = { ...next[activeIndex], answer: '', isComplete: false };
          } else if (message.is_streaming) {
            next[activeIndex] = { 
              ...next[activeIndex], 
              answer: next[activeIndex].answer + message.text 
            };
          } else if (message.complete) {
            next[activeIndex] = { ...next[activeIndex], isComplete: true };
          }
          
          return next;
        });
        break;

      case 'response':
        if (message.action === 'start_interview' && message.status === 'started') {
          console.log('[App] Interview started successfully');
          setIsSpeakingTooFast(false);
        } else if (message.action === 'stop_interview' && message.status === 'stopped') {
          console.log('[App] Interview stopped successfully');
          setIsSpeakingTooFast(false);
        } else if (message.action === 'freeze' && message.status === 'frozen') {
          setIsFrozen(true);
        } else if (message.action === 'unfreeze' && message.status === 'unfrozen') {
          setIsFrozen(false);
        }
        break;

      case 'connection':
        console.log('[App] Connection status:', message.status);
        break;

      case 'error':
        console.error('[App] Error:', message.message);
        break;

      default:
        console.log('[App] Unknown message type:', message.type);
    }
  }, []);

  const { connectionStatus, sendMessage } = useWebSocket(handleWebSocketMessage);

  const [initialPersona, setInitialPersona] = useState('Short Bullets');

  const handleStartInterview = (config: any) => {
    console.log('[App] Starting interview with config:', config);
    setInitialPersona(config.persona || 'Short Bullets');
    
    // Reset session state
    processedMessagesRef.current.clear();
    setHistoryEntries([]);
    setActiveHistoryId(null);
    setIsSpeakingTooFast(false);

    sendMessage({
      action: 'start_interview',
      mic_index: config.mic_index,
      speaker_index: config.speaker_index,
      persona: config.persona,
      context: config.context
    });
    setIsInterviewActive(true);
  };

  const handleEndSession = () => {
    console.log('[App] Ending session...');
    sendMessage({ action: 'stop_interview' });
    setIsInterviewActive(false);
    setIsFrozen(false);
    setHistoryEntries([]);
    setActiveHistoryId(null);
    setIsSpeakingTooFast(false);

    if (fastSpeechTimeoutRef.current) {
      window.clearTimeout(fastSpeechTimeoutRef.current);
      fastSpeechTimeoutRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (fastSpeechTimeoutRef.current) {
        window.clearTimeout(fastSpeechTimeoutRef.current);
      }
    };
  }, []);

  const handleFreeze = () => {
    console.log('[App] Freezing...');
    sendMessage({ action: 'freeze' });
  };

  const handleUnfreeze = () => {
    console.log('[App] Unfreezing...');
    sendMessage({ action: 'unfreeze' });
  };

  return (
    <div className="w-screen h-screen overflow-hidden">
      {/* Connection Status Indicator */}
      <div className="fixed top-2 right-2 z-50">
        <div
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            connectionStatus === 'connected'
              ? 'bg-green-500/20 text-green-400 border border-green-500'
              : connectionStatus === 'connecting'
              ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500'
              : 'bg-red-500/20 text-red-400 border border-red-500'
          }`}
        >
          {connectionStatus === 'connected' && '● Connected'}
          {connectionStatus === 'connecting' && '○ Connecting...'}
          {connectionStatus === 'disconnected' && '○ Disconnected'}
          {connectionStatus === 'error' && '✕ Error'}
        </div>
      </div>

      {/* Main View Switcher */}
      {!isInterviewActive ? (
        <SetupView onStartInterview={handleStartInterview} />
      ) : (
        <InterviewView
          onEndSession={handleEndSession}
          onFreeze={handleFreeze}
          onUnfreeze={handleUnfreeze}
          isFrozen={isFrozen}
          historyEntries={historyEntries}
          activeHistoryId={activeHistoryId}
          isSpeakingTooFast={isSpeakingTooFast}
          initialPersona={initialPersona}
        />
      )}
    </div>
  );
}

export default App;
