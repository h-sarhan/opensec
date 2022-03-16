const snapshots = document.querySelectorAll('.snapshot');
const baseUrls = [];
snapshots.forEach(snapshot => {
  baseUrls.push(snapshot.src);
});

function refreshSnapshots() {
  snapshots.forEach((snapshot, index) => {
    snapshot.src = `${baseUrls[index]}?t=${new Date().getTime()}`;
  });
}

setInterval(refreshSnapshots, 10000);
