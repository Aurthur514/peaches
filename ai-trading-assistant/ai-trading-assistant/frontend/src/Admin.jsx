import React, { useState } from 'react';
import { BACKEND_URL } from './config';

export default function Admin(){
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [modelInfo, setModelInfo] = useState(null);
  const [token, setToken] = useState('');

  const onSelect = (e) => {
    setFile(e.target.files[0]);
  };

  const upload = async () => {
    if(!file) return setStatus('Select a file first');
    const fd = new FormData();
    fd.append('file', file, file.name);
    setStatus('Uploading...');
    try{
      const res = await fetch(`${BACKEND_URL}/upload-model`, { method: 'POST', body: fd, headers: { 'x-admin-token': token } });
      const j = await res.json();
      setStatus(JSON.stringify(j));
      if(res.ok) fetchInfo();
    }catch(e){
      setStatus('Upload error: '+String(e));
    }
  };

  const fetchInfo = async () => {
    setStatus('Fetching model info...');
    try{
      const res = await fetch(`${BACKEND_URL}/model-info`, { headers: { 'x-admin-token': token } });
      const j = await res.json();
      setModelInfo(j);
      setStatus('Fetched');
    }catch(e){
      setStatus('Error fetching model info: '+String(e));
    }
  };

  return (
    <div style={{marginTop:20}}>
      <h2>Admin — Model Upload</h2>
      <div style={{marginBottom:8}}>
        <input type="password" placeholder="Admin token" value={token} onChange={e=>setToken(e.target.value)} />
      </div>
      <input type="file" accept=".onnx" onChange={onSelect} />
      <button onClick={upload}>Upload model</button>
      <button onClick={fetchInfo}>Refresh model info</button>
      <div style={{marginTop:8}}><b>Status:</b> {status}</div>
      {modelInfo && modelInfo.inputs && <div style={{marginTop:12}}>
        <h3>Model: {modelInfo.model}</h3>
        <div><b>Inputs</b></div>
        <ul>{modelInfo.inputs.map((i,idx)=>(<li key={idx}>{i.name} — shape: {JSON.stringify(i.shape)}</li>))}</ul>
        <div><b>Outputs</b></div>
        <ul>{modelInfo.outputs.map((o,idx)=>(<li key={idx}>{o.name} — shape: {JSON.stringify(o.shape)}</li>))}</ul>
      </div>}
    </div>
  );
}
