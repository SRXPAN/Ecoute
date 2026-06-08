import { useState, useCallback, useEffect, useRef } from 'react';
import { getCurrentWindow, LogicalSize } from '@tauri-apps/api/window';
import { useWebSocket } from './hooks/useWebSocket';
import { SetupView } from './components/SetupView';
import { InterviewView } from './components/InterviewView';

function App() {
  const [isInterviewActive, setIsInterviewActive] = useState(false);
  const [isFrozen, setIsFrozen] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [llmHint, setLlmHint] = useState('');
  const [isSpeakingTooFast, setIsSpeakingTooFast] = useState(false);
  const fastSpeechTimeoutRef = useRef<number | null>(null);

  // Handle window resizing based on mode
  useEffect(() => {
    const resizeWindow = async () => {
      try {
        const appWindow = getCurrentWindow();
        if (isInterviewActive) {
          // Compact mode for interview
          await appWindow.setSize(new LogicalSize(450, 800));
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
        setTranscript((prev) => {
          const newText = `${message.speaker}: ${message.text}\n\n`;
          return newText + prev;
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
        if (message.is_streaming) {
          setLlmHint((prev) => prev + message.text);
        } else if (message.complete) {
          // Optionally clear or mark completion
        }
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
    sendMessage({
      action: 'start_interview',
      mic_index: config.mic_index,
      speaker_index: config.speaker_index,
      persona: config.persona,
      context: config.context
    });
    setIsInterviewActive(true);
    setTranscript('');
    setLlmHint('');
    setIsSpeakingTooFast(false);
  };

  const handleEndSession = () => {
    console.log('[App] Ending session...');
    sendMessage({ action: 'stop_interview' });
    setIsInterviewActive(false);
    setIsFrozen(false);
    setTranscript('');
    setLlmHint('');
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
          transcript={transcript}
          llmHint={llmHint}
          isSpeakingTooFast={isSpeakingTooFast}
          sendMessage={sendMessage}
          initialPersona={initialPersona}
        />
      )}
    </div>
  );
}

export default App;
