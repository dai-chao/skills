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

let tracks = [];
let currentIndex = -1;
let isPlaying = false;

function formatTime(seconds) {
  if (isNaN(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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
  
  audio.src = track.path;
  audio.play().then(() => {
    isPlaying = true;
    updatePlayButton();
    updatePlaylistUI();
    currentTrackName.textContent = track.name;
  }).catch(err => {
    console.error('播放失败:', err);
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
  } else {
    audio.play();
    isPlaying = true;
  }
  updatePlayButton();
}

function updatePlayButton() {
  const visualizer = document.getElementById('visualizer');
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

// 事件监听
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

// 键盘快捷键
document.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
    e.preventDefault();
    togglePlay();
  }
});

// 初始化: 加载内置音乐并自动播放
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
