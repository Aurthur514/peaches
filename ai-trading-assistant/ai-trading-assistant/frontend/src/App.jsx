import React, { useState, useEffect } from 'react';
import { startCapture } from './screen-capture';
import { BACKEND_URL } from './config';
import './styles.css';
import Admin from './Admin';

export default function App(){
  const [running, setRunning] = useState(false);
  const [signal, setSignal] = useState(null);

  useEffect(() => {
    // Open WebSocket to receive real-time signals
    let ws;
    try{
      ws = new WebSocket('ws://127.0.0.1:8000/ws/signals');
      ws.onmessage = (ev) => {
        try{
          const data = JSON.parse(ev.data);
          setSignal(data);
        }catch(e){ console.error('ws parse', e); }
      };
      ws.onopen = () => console.log('WS connected');
      ws.onclose = () => console.log('WS closed');
    }catch(e){
      console.warn('WebSocket not available', e);
    }

    return () => {
      if(ws) ws.close();
    };
  }, []);

  const handleFrame = async (blob) => {
    try{
      const fd = new FormData();
      fd.append('frame', blob, 'frame.jpg');
      const res = await fetch(`${BACKEND_URL}/process-frame`, {
        method: 'POST',
        body: fd
      });
      const data = await res.json();
      // We still update UI from direct response if WS isn't connected.
      setSignal(data);
    }catch(e){
      console.error('frame send error', e);
    }
  };

  const toggle = async () => {
    if(!running){
      await startCapture(handleFrame);
      setRunning(true);
    } else {
      alert('Refresh page to stop capture (demo limitation)');
    }
  };

  return (
    <div className="app">
      <h1>AI Trading Assistant — Manual Mode</h1>
      <p>Click <b>Start Capture</b> and choose the chart/window you want the assistant to see.</p>
      <div style={{marginTop:8}}>
        <button onClick={()=>setShowAdmin(s=>!s)} style={{marginRight:8}}>Toggle Admin</button>
      </div>
      <button onClick={toggle}>{running ? 'Capturing...' : 'Start Capture'}</button>

      <div id="signalBox" className="signalBox" style={{display: signal ? 'block' : 'none'}}>
        {signal && <div>
          <h2>{signal.signal} — {(signal.confidence*100).toFixed(1)}%</h2>
          <p>Expect: {signal.expected_move_5min}</p>
          <p>Reason:</p>
          <ul>{signal.reason.map((r,i)=><li key={i}>{r}</li>)}</ul>
        </div>}
      </div>

      {/* Floating widget that stays on top-right of screen — shows latest signal */}
      <div className="floatingWidget" style={{display: signal ? 'flex' : 'none'}}>
        {signal && <div>
          <div className="fw-header">Signal</div>
          <div className="fw-body">
            <div className="fw-sig">{signal.signal}</div>
            <div className="fw-conf">{(signal.confidence*100).toFixed(0)}%</div>
          </div>
        </div>}
      </div>
      {showAdmin && <Admin />}
    </div>
  );
}
