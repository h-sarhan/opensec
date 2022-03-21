function loadVideo(video, source) {
  const hls = new Hls();
  hls.attachMedia(video);
  hls.on(Hls.Events.MEDIA_ATTACHED, function () {
    hls.loadSource(source);
  });
}
// let STREAM_URL = JSON.parse(document.getElementById('liveFeedUrl').textContent);
let STREAM_URL = '/media/stream/Bedroom/index.m3u8';
console.log(STREAM_URL);
const video = document.getElementById('video');
const playBtn = document.getElementById('play-btn');

loadVideo(video, STREAM_URL);

// playBtn.addEventListener('click', () => {
// });

video.play();
setInterval(() => {
  video.currentTime = video.duration - 4;
}, 10000);
