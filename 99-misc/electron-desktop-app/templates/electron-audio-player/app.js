const audio = document.getElementById('audio-player');
const trackList = document.getElementById('track-list');
const emptyState = document.getElementById('empty-state');
const trackCount = document.getElementById('track-count');
const currentTrackName = document.getElementById('current-track-name');
const currentTimeEl = document.getElementById('current-time');
const totalTimeEl = document.getElementById('total-time');
const progressBar = document.getElementById('progress-bar');
const progressFill = document.getElementById('progress-fill');
const btnPlay = document.getElementById('btn-play');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const iconPlay = document.getElementById('icon-play');
const iconPause = document.getElementById('icon-pause');
const visualizer = document.getElementById('visualizer');
const visualizerBars = visualizer.querySelectorAll('.bar');

let tracks = [];
let currentIndex = -1;
let isPlaying = false;

// Web Audio API 可视化
let audioCtx = null;
let analyser = null;
let source = null;
let dataArray = null;
let animationId = null;

function initAudioContext() {
  if (audioCtx) return;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 64;
  analyser.smoothingTimeConstant = 0.8;
  source = audioCtx.createMediaElementSource(audio);
  source.connect(analyser);
  analyser.connect(audioCtx.destination);
  dataArray = new Uint8Array(analyser.frequencyBinCount);
}

function updateVisualizer() {
  if (!analyser || !isPlaying) return;
  analyser.getByteFrequencyData(dataArray);

  const barCount = visualizerBars.length;
  const halfBars = barCount / 2;

  const heights = [];
  for (let i = 0; i < halfBars; i++) {
    const freqIndex = Math.floor((i / halfBars) * dataArray.length);
    const val = dataArray[Math.min(freqIndex, dataArray.length - 1)];
    const height = 4 + (val / 255) * 196;
    heights.push(height);
  }

  for (let i = 0; i < barCount; i++) {
    const distFromCenter = Math.abs(i - halfBars + 0.5);
    const heightIndex = Math.floor(distFromCenter);
    const height = heights[Math.min(heightIndex, heights.length - 1)];
    visualizerBars[i].style.height = height + 'px';
  }

  animationId = requestAnimationFrame(updateVisualizer);
}

function stopVisualizer() {
  if (animationId) {
    cancelAnimationFrame(animationId);
    animationId = null;
  }
  visualizerBars.forEach(bar => {
    bar.style.height = '4px';
  });
}

function formatTime(seconds) {
  if (isNaN(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updatePlaylistUI() {
  trackList.innerHTML = '';

  if (tracks.length === 0) {
    emptyState.style.display = 'flex';
    trackCount.textContent = '0 首';
    btnPlay.disabled = true;
    btnPrev.disabled = true;
    btnNext.disabled = true;
    return;
  }

  emptyState.style.display = 'none';
  trackCount.textContent = `${tracks.length} 首`;
  btnPlay.disabled = false;
  btnPrev.disabled = tracks.length <= 1;
  btnNext.disabled = tracks.length <= 1;

  tracks.forEach((track, index) => {
    const li = document.createElement('li');
    li.className = 'track-item';
    if (index === currentIndex) {
      li.classList.add('active', 'playing');
    }

    li.innerHTML = `
      <span class="track-number">${index + 1}</span>
      <div class="track-info">
        <span class="track-name-text">${track.name}</span>
      </div>
      <span class="track-duration" id="duration-${index}">--:--</span>
    `;

    li.addEventListener('click', () => playTrack(index));
    trackList.appendChild(li);

    const tempAudio = new Audio(track.path);
    tempAudio.addEventListener('loadedmetadata', () => {
      const durationEl = document.getElementById(`duration-${index}`);
      if (durationEl) durationEl.textContent = formatTime(tempAudio.duration);
      track.duration = tempAudio.duration;
    });
  });
}

function playTrack(index) {
  if (index < 0 || index >= tracks.length) return;

  currentIndex = index;
  const track = tracks[index];

  initAudioContext();

  audio.src = track.path;

  const onPlaying = () => {
    audio.removeEventListener('playing', onPlaying);
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    isPlaying = true;
    updatePlayButton();
    updatePlaylistUI();
    currentTrackName.textContent = track.name;
    updateVisualizer();
  };

  audio.addEventListener('playing', onPlaying);

  audio.play().catch(err => {
    console.error('播放失败:', err);
    audio.removeEventListener('playing', onPlaying);
  });
}

function togglePlay() {
  if (tracks.length === 0) return;

  if (currentIndex === -1) {
    playTrack(0);
    return;
  }

  if (isPlaying) {
    audio.pause();
    isPlaying = false;
    stopVisualizer();
  } else {
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    audio.play();
    isPlaying = true;
    updateVisualizer();
  }
  updatePlayButton();
}

function updatePlayButton() {
  if (isPlaying) {
    iconPlay.style.display = 'none';
    iconPause.style.display = 'block';
    btnPlay.classList.add('playing');
    visualizer.classList.add('playing');
  } else {
    iconPlay.style.display = 'block';
    iconPause.style.display = 'none';
    btnPlay.classList.remove('playing');
    visualizer.classList.remove('playing');
  }
}

function playPrev() {
  if (tracks.length === 0) return;
  const newIndex = currentIndex <= 0 ? tracks.length - 1 : currentIndex - 1;
  playTrack(newIndex);
}

function playNext() {
  if (tracks.length === 0) return;
  const newIndex = currentIndex >= tracks.length - 1 ? 0 : currentIndex + 1;
  playTrack(newIndex);
}

btnPlay.addEventListener('click', togglePlay);
btnPrev.addEventListener('click', playPrev);
btnNext.addEventListener('click', playNext);

audio.addEventListener('timeupdate', () => {
  currentTimeEl.textContent = formatTime(audio.currentTime);
  totalTimeEl.textContent = formatTime(audio.duration || 0);
  const percent = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
  progressFill.style.width = percent + '%';
});

audio.addEventListener('ended', playNext);

audio.addEventListener('loadedmetadata', () => {
  totalTimeEl.textContent = formatTime(audio.duration);
});

progressBar.addEventListener('click', (e) => {
  if (!audio.duration) return;
  const rect = progressBar.getBoundingClientRect();
  const percent = (e.clientX - rect.left) / rect.width;
  audio.currentTime = percent * audio.duration;
});

document.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
    e.preventDefault();
    togglePlay();
  }
});

async function init() {
  try {
    tracks = await window.electronAPI.getBuiltInMusic();
    updatePlaylistUI();
    if (tracks.length > 0) {
      playTrack(0);
    }
  } catch (err) {
    console.error('加载音乐失败:', err);
  }
}

init();
