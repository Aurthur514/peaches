export async function startCapture(callback){
  const stream = await navigator.mediaDevices.getDisplayMedia({
    video: { frameRate: 2 }
  });

  const video = document.createElement('video');
  video.srcObject = stream;
  await video.play();

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  setInterval(async () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    canvas.toBlob(blob => {
      if(blob) callback(blob);
    }, 'image/jpeg', 0.7);
  }, 1000); // 1 FPS for demo
}
