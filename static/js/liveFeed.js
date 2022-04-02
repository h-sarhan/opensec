function loadVideo(video, source) {
  const hls = new Hls();
  hls.attachMedia(video);
  hls.on(Hls.Events.MEDIA_ATTACHED, function () {
    hls.loadSource(source);
  });
}
let STREAM_URL = JSON.parse(document.getElementById('liveFeedUrl').textContent);
const video = document.getElementById('video');
const playBtn = document.getElementById('play-btn');
loadVideo(video, STREAM_URL);

video.play();

setInterval(() => {
  video.currentTime = video.duration - 10;
}, 10000);
