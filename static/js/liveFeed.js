function loadVideo(video, source) {
  const hls = new Hls();
  hls.attachMedia(video);
  hls.on(Hls.Events.MEDIA_ATTACHED, function () {
    hls.loadSource(source);
  });
}
const STREAM_URL = JSON.parse(document.getElementById('liveFeedUrl').textContent);
const video = document.getElementById('video');
const playBtn = document.getElementById('play-btn');

loadVideo(video, STREAM_URL)


playBtn.addEventListener('click', () => {
  video.play();
  video.currentTime = video.duration - 3;
});

setTimeout(() => {
  video.currentTime = video.duration - 3;
}, 10000);