import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

function App() {
  const [isStarted, setIsStarted] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [displayItems, setDisplayItems] = useState([]);
  const [orderConfirmed, setOrderConfirmed] = useState(null);
  const [status, setStatus] = useState('Click to start');

  const wsRef = useRef(null);
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingStartTimeRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const hasSpokenRef = useRef(false);
  const isListeningRef = useRef(false);
  const isConversationActiveRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isProcessingRef = useRef(false);
  
  const MIN_RECORDING_DURATION = 600; // Minimum 600ms recording
  const MIN_AUDIO_SIZE = 5000; // Minimum 5KB audio data
  const SILENCE_THRESHOLD = 27; // Audio level threshold for voice detection (filters out fans/ambient noise)
  const SILENCE_DURATION = 1500; // 1.5 seconds of silence to stop
  const MAX_RECORDING_DURATION = 15000; // Maximum 15 seconds recording (safety net)
  const SPEECH_CONFIRM_FRAMES = 5; // Require audio above threshold for 5 consecutive frames to confirm speech
  
  // Keep refs in sync with state
  useEffect(() => { isListeningRef.current = isListening; }, [isListening]);
  useEffect(() => { isConversationActiveRef.current = isConversationActive; }, [isConversationActive]);
  useEffect(() => { isSpeakingRef.current = isSpeaking; }, [isSpeaking]);
  useEffect(() => { isProcessingRef.current = isProcessing; }, [isProcessing]);

  // Auto-start listening (can be called during agent speech for interruption)
  const startAutoListening = useCallback((duringAgentSpeech = false) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.log('WebSocket not ready for auto-listen');
      return;
    }
    
    // Small delay before starting to listen
    setTimeout(() => {
      startListeningWithSilenceDetection(duringAgentSpeech);
    }, duringAgentSpeech ? 100 : 300);
  }, []);

  // Play MP3 audio from base64
  const playAudio = useCallback((base64Audio, autoListenAfter = true) => {
    console.log('Playing audio, length:', base64Audio.length);

    try {
      // Decode base64 to binary
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // Create blob and URL
      const blob = new Blob([bytes], { type: 'audio/mp3' });
      const url = URL.createObjectURL(blob);

      // Stop any current audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      // Create and play new audio
      const audio = new Audio(url);
      audioRef.current = audio;

      setIsSpeaking(true);
      setStatus('Agent speaking... (speak to interrupt)');

      audio.onended = () => {
        console.log('Audio playback ended');
        setIsSpeaking(false);
        URL.revokeObjectURL(url);
        
        // Auto-start listening if conversation is active and not already listening
        if (autoListenAfter && isConversationActiveRef.current && !isListeningRef.current) {
          setStatus('Your turn - speak now...');
          startAutoListening();
        } else if (!isListeningRef.current) {
          setStatus('Click mic to speak');
        }
      };

      audio.onerror = (e) => {
        console.error('Audio error:', e);
        setIsSpeaking(false);
        setStatus('Audio error');
        URL.revokeObjectURL(url);
      };

      audio.play().then(() => {
        console.log('Audio playing');
        // Start listening for interruption while agent speaks
        if (autoListenAfter && isConversationActiveRef.current) {
          startAutoListening(true); // true = listening during agent speech
        }
      }).catch(err => {
        console.error('Play error:', err);
        setIsSpeaking(false);
        setStatus('Could not play audio');
      });

    } catch (err) {
      console.error('Audio decode error:', err);
      setIsSpeaking(false);
    }
  }, [startAutoListening]);

  // Connect WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    console.log('Connecting to WebSocket...');
    wsRef.current = new WebSocket(`${WS_URL}/ws/voice`);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setStatus('Connected! Starting...');

      // Send start session
      wsRef.current.send(JSON.stringify({ type: 'start_session' }));
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data.type);

      switch (data.type) {
        case 'audio':
          setIsProcessing(false);
          playAudio(data.audio);
          break;

        case 'show_items':
          setDisplayItems(data.items);
          // Auto-hide after 10 seconds
          setTimeout(() => setDisplayItems([]), 10000);
          break;

        case 'cart_update':
          setCart(data.cart);
          break;

        case 'order_confirmed':
          setOrderConfirmed(data.order);
          setCart({ items: [], total: 0 });
          // Stop the conversation when order is finalized
          setIsConversationActive(false);
          isConversationActiveRef.current = false;
          // Stop any ongoing listening
          if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
            setIsListening(false);
            isListeningRef.current = false;
          }
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
          setStatus('Order complete!');
          break;

        case 'error':
          console.error('Server error:', data.message);
          setStatus('Error: ' + data.message);
          setIsProcessing(false);
          break;

        default:
          break;
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket closed');
      setIsConnected(false);
      setStatus('Disconnected');
    };

    wsRef.current.onerror = (err) => {
      console.error('WebSocket error:', err);
      setStatus('Connection error');
    };
  }, [playAudio]);

  // Start listening with automatic silence detection
  // interruptMode: if true, we're listening while agent is speaking for potential interruption
  const startListeningWithSilenceDetection = async (interruptMode = false) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.log('WebSocket not ready');
      return;
    }

    // Don't start if already listening
    if (isListeningRef.current) {
      console.log('Already listening');
      return;
    }

    try {
      console.log(`Starting auto-listening with silence detection... (interrupt mode: ${interruptMode})`);
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      streamRef.current = stream;
      recordingStartTimeRef.current = Date.now();
      hasSpokenRef.current = false;

      // Setup audio analysis for silence detection
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 512;

      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      // Higher threshold for interruption to avoid false positives from speaker feedback and ambient noise
      const effectiveThreshold = interruptMode ? SILENCE_THRESHOLD * 2 : SILENCE_THRESHOLD;

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Clear silence timer
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }

        // Close audio context
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }

        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        console.log(`Recording stopped after ${recordingDuration}ms, hasSpoken: ${hasSpokenRef.current}`);

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Audio blob size:', audioBlob.size);

        // Check if user actually spoke
        if (!hasSpokenRef.current || recordingDuration < MIN_RECORDING_DURATION || audioBlob.size < MIN_AUDIO_SIZE) {
          console.log('No meaningful audio detected, restarting listener...');
          if (isConversationActiveRef.current && !isSpeakingRef.current) {
            setStatus('I didn\'t hear anything, speak now...');
            setTimeout(() => {
              if (isConversationActiveRef.current && !isSpeakingRef.current && !isProcessingRef.current) {
                startListeningWithSilenceDetection();
              }
            }, 1000);
          }
          return;
        }

        // Convert to base64 and send
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result.split(',')[1];
          console.log('Sending audio, base64 length:', base64.length);

          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'audio',
              audio: base64
            }));
            setIsProcessing(true);
            setStatus('Processing...');
          }
        };
        reader.readAsDataURL(audioBlob);
      };

      // Monitor audio levels for silence detection and interruption
      let frameCount = 0;
      let speechConfirmCount = 0; // Count consecutive frames above threshold
      
      const checkAudioLevel = () => {
        if (!analyserRef.current || !isListeningRef.current) return;

        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
        
        // Log audio level every ~3 seconds for debugging
        frameCount++;
        if (frameCount % 180 === 0) {
          console.log(`Audio level: ${average.toFixed(1)}, threshold: ${effectiveThreshold}, hasSpoken: ${hasSpokenRef.current}`);
        }
        
        // Check for max recording duration (safety net)
        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        if (recordingDuration > MAX_RECORDING_DURATION && hasSpokenRef.current) {
          console.log('Max recording duration reached, stopping...');
          stopListening();
          return;
        }

        if (average > effectiveThreshold) {
          // Potential speech detected - need consecutive frames to confirm
          speechConfirmCount++;
          
          if (speechConfirmCount >= SPEECH_CONFIRM_FRAMES && !hasSpokenRef.current) {
            // Confirmed user is speaking (sustained audio above threshold)
            hasSpokenRef.current = true;
            console.log('User speaking confirmed, audio level:', average.toFixed(1));
            
            // If agent is speaking and user starts talking, interrupt the agent
            if (isSpeakingRef.current && audioRef.current) {
              console.log('User interrupted agent, stopping agent audio...');
              audioRef.current.pause();
              audioRef.current = null;
              setIsSpeaking(false);
              isSpeakingRef.current = false;
              setStatus('Listening...');
            }
          }
          
          // Clear any pending silence timer while audio is above threshold
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else {
          // Audio below threshold
          speechConfirmCount = 0; // Reset speech confirmation counter
          
          if (hasSpokenRef.current && !silenceTimerRef.current) {
            // User stopped speaking, start silence timer
            silenceTimerRef.current = setTimeout(() => {
              console.log('Silence confirmed, stopping recording...');
              stopListening();
            }, SILENCE_DURATION);
          }
        }

        if (isListeningRef.current) {
          requestAnimationFrame(checkAudioLevel);
        }
      };

      mediaRecorderRef.current.start(100);
      setIsListening(true);
      isListeningRef.current = true; // Update ref immediately for checkAudioLevel
      
      if (interruptMode) {
        // Don't change status text during interrupt mode, keep showing "Agent speaking..."
        console.log('Listening in interrupt mode (agent is speaking)');
      } else {
        setStatus('Listening... (speak now)');
        console.log('Listening in normal mode');
      }

      // Start monitoring audio levels
      requestAnimationFrame(checkAudioLevel);

    } catch (err) {
      console.error('Recording error:', err);
      setStatus('Microphone access denied');
    }
  };

  // Stop listening (used by silence detection)
  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log('Stopping listening...');
      mediaRecorderRef.current.stop();
      setIsListening(false);
      isListeningRef.current = false; // Update ref immediately
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    }
  };

  // Manual click to start/stop conversation
  const toggleConversation = () => {
    if (isConversationActive) {
      // Stop conversation
      setIsConversationActive(false);
      stopListening();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setIsSpeaking(false);
      setIsProcessing(false);
      setStatus('Click to start conversation');
    } else {
      // Start conversation
      setIsConversationActive(true);
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'start_session' }));
      }
    }
  };

  // Legacy manual recording (kept for fallback but not used in main UI)
  const startRecording = async () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.log('WebSocket not ready');
      return;
    }

    if (isSpeaking) {
      // Stop current audio if speaking
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
        setIsSpeaking(false);
      }
    }

    try {
      console.log('Starting recording...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      streamRef.current = stream;
      recordingStartTimeRef.current = Date.now();

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const recordingDuration = Date.now() - recordingStartTimeRef.current;
        console.log(`Recording stopped after ${recordingDuration}ms`);

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Audio blob size:', audioBlob.size);

        // Check minimum duration and size
        if (recordingDuration < MIN_RECORDING_DURATION) {
          console.log(`Recording too short (${recordingDuration}ms < ${MIN_RECORDING_DURATION}ms), ignoring`);
          setStatus('Hold button longer to speak');
          setTimeout(() => setStatus('Hold button to speak'), 2000);
          return;
        }
        
        if (audioBlob.size < MIN_AUDIO_SIZE) {
          console.log(`Audio too small (${audioBlob.size} < ${MIN_AUDIO_SIZE}), ignoring`);
          setStatus('No audio detected, try again');
          setTimeout(() => setStatus('Hold button to speak'), 2000);
          return;
        }

        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result.split(',')[1];
          console.log('Sending audio, base64 length:', base64.length);

          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'audio',
              audio: base64
            }));
            setIsProcessing(true);
            setStatus('Processing...');
          }
        };
        reader.readAsDataURL(audioBlob);
      };

      // Request data every 100ms for smoother recording
      mediaRecorderRef.current.start(100);
      setIsListening(true);
      setStatus('Listening...');

    } catch (err) {
      console.error('Recording error:', err);
      setStatus('Microphone access denied');
    }
  };

  // Stop recording (legacy - for manual mode)
  const stopRecording = () => {
    stopListening();
  };

  // Start session
  const startSession = () => {
    console.log('Starting session...');
    setIsStarted(true);
    setIsConversationActive(true);
    connect();
  };

  // New order
  const newOrder = () => {
    setOrderConfirmed(null);
    setDisplayItems([]);
    setCart({ items: [], total: 0 });
    setIsConversationActive(true);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'start_session' }));
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (audioRef.current) audioRef.current.pause();
      if (audioContextRef.current) audioContextRef.current.close();
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Landing page
  if (!isStarted) {
    return (
      <div className="app landing">
        <div className="landing-content">
          <div className="logo-big">🍔</div>
          <h1>Burger Spot</h1>
          <p>Voice-Powered Ordering</p>
          <button className="start-btn" onClick={startSession}>
            🎤 Start Ordering
          </button>
          <p className="hint">Click to begin your order with our voice assistant</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <span>🍔</span>
          <h1>Burger Spot</h1>
        </div>
        <div className={`connection ${isConnected ? 'online' : ''}`}>
          <span className="dot"></span>
          {isConnected ? 'Connected' : 'Connecting...'}
        </div>
      </header>

      <main className="main">
        {/* Voice Control */}
        <section className="voice-section">
          <div className={`mic-container ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''} ${isProcessing ? 'processing' : ''} ${isConversationActive ? 'active' : ''}`}>
            <button
              className="mic-btn"
              onClick={toggleConversation}
              disabled={!isConnected}
            >
              {isProcessing ? (
                <div className="spinner"></div>
              ) : isSpeaking ? (
                <div className="waves">
                  <span></span><span></span><span></span><span></span><span></span>
                </div>
              ) : isListening ? (
                <div className="listening-waves">
                  <span></span><span></span><span></span>
                </div>
              ) : isConversationActive ? (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 6h12v12H6z"/>
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
              )}
            </button>
          </div>
          <p className="status-text">{status}</p>
          {isConnected && !isConversationActive && (
            <p className="hint-text">Click to start conversation</p>
          )}
          {isConversationActive && !isSpeaking && !isProcessing && !isListening && (
            <p className="hint-text">Click to end conversation</p>
          )}
        </section>

        {/* Product Display */}
        <section className="display-section">
          {displayItems.length > 0 ? (
            <div className="products">
              {displayItems.map((item, i) => (
                <div key={i} className="product">
                  <img src={`${API_URL}${item.image}`} alt={item.name} />
                  <div className="product-details">
                    <h3>{item.name}</h3>
                    <p>{item.description}</p>
                    <p className="price">${item.price.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-products">
              <p>🎤</p>
              <p>Ask about our menu!</p>
            </div>
          )}
        </section>

        {/* Order Panel */}
        <aside className="order-section">
          <h2>Your Order</h2>

          {cart.items.length === 0 ? (
            <p className="empty">No items yet</p>
          ) : (
            <>
              <div className="order-list">
                {cart.items.map((item, i) => (
                  <div key={i} className="order-row">
                    <img src={`${API_URL}${item.image}`} alt={item.name} />
                    <div className="order-info">
                      <span className="name">{item.name}</span>
                      <span className="qty">x{item.quantity}</span>
                    </div>
                    <span className="price">${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="order-total">
                <span>Total</span>
                <span>${cart.total.toFixed(2)}</span>
              </div>
              <p className="order-hint">Say "that's all" to checkout</p>
            </>
          )}
        </aside>
      </main>

      {/* Receipt Modal */}
      {orderConfirmed && (
        <div className="modal-bg">
          <div className="receipt">
            <div className="receipt-top">
              <span>🍔</span>
              <h2>Burger Spot</h2>
              <p>Order Confirmed!</p>
            </div>
            <div className="receipt-body">
              <p className="order-num">Order #{orderConfirmed.id}</p>
              <div className="receipt-items">
                {orderConfirmed.items.map((item, i) => (
                  <div key={i} className="receipt-row">
                    <span>{item.quantity}x {item.name}</span>
                    <span>${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="receipt-sum">
                <span>Total</span>
                <span>${orderConfirmed.total.toFixed(2)}</span>
              </div>
            </div>
            <div className="receipt-bottom">
              <p>Thank you for your order!</p>
              <button onClick={newOrder}>New Order</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
