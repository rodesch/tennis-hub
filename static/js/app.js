/* Tennis Hub - SPA navigation + API fetch */

const API = 'api';

// ---- Navigation ----

function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(a => a.classList.remove('active'));
  const sec = document.getElementById(name);
  if (sec) sec.classList.add('active');
  const link = document.querySelector(`.nav-link[data-section="${name}"]`);
  if (link) link.classList.add('active');
}

function getSection() {
  const hash = location.hash.replace('#', '') || 'rankings';
  return hash;
}

window.addEventListener('hashchange', () => {
  const sec = getSection();
  showSection(sec);
  autoLoad(sec);
});

// ---- Helpers ----

function setContent(id, html) {
  document.getElementById(id).innerHTML = html;
}

function loading(id) {
  setContent(id, '<div class="loading">Loading…</div>');
}

function errorMsg(id, msg) {
  setContent(id, `<div class="error-msg">⚠️ ${msg}</div>`);
}

async function apiFetch(path) {
  const res = await fetch(API + path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function jsonFallback(data) {
  return `<pre class="json-view">${JSON.stringify(data, null, 2)}</pre>`;
}

// ---- Rankings ----

let rankingsTour = 'atp';

async function loadRankings() {
  loading('rankings-content');
  try {
    const resp = await apiFetch(`/rankings?type=${rankingsTour}`);
    setContent('rankings-content', renderRankings(resp));
  } catch (e) {
    errorMsg('rankings-content', e.message);
  }
}

function renderRankings(resp) {
  const data = resp.data;
  // TennisApi1 may return different shapes; try common paths
  const rows = data?.rankings || data?.data || data?.players || (Array.isArray(data) ? data : null);
  if (!rows) return jsonFallback(data);

  const rowsHtml = rows.slice(0, 100).map(r => {
    const rank = r.ranking || r.rank || r.position || '—';
    const name = r.player?.name || r.name || r.playerName || '—';
    const pts = (r.point ?? r.points ?? r.rankingPoints)?.toLocaleString() || '—';
    const country = r.player?.countryAcr || r.player?.country?.alpha2 || r.player?.country?.acronym || r.country || '';
    return `
      <tr>
        <td class="rank-num">${rank}</td>
        <td class="player-name">${name} ${country ? `<small>(${country})</small>` : ''}</td>
        <td><span class="points-badge">${pts}</span></td>
      </tr>`;
  }).join('');

  return `
    <table class="rankings-table">
      <thead><tr><th>#</th><th>Player</th><th>Points</th></tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>`;
}

document.querySelectorAll('.tab[data-tour]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab[data-tour]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    rankingsTour = btn.dataset.tour;
    loadRankings();
  });
});

// ---- Results ----

const resultsDateInput = document.getElementById('results-date');
resultsDateInput.value = new Date().toISOString().split('T')[0];
resultsDateInput.addEventListener('change', loadResults);

async function loadResults() {
  const date = resultsDateInput.value;
  loading('results-content');
  try {
    const resp = await apiFetch(`/results?date=${date}`);
    setContent('results-content', renderResults(resp));
  } catch (e) {
    errorMsg('results-content', e.message);
  }
}

function renderResults(resp) {
  const data = resp.data;
  const matches = data?.events || data?.results || data?.matches || data?.data || (Array.isArray(data) ? data : null);
  if (!matches || matches.length === 0) return '<div class="placeholder">No results found for this date.</div>';

  return matches.map(m => {
    const tournament = m.tournament?.name || m.competition?.name || (m.tournamentId ? 'Tournament #' + m.tournamentId : 'Unknown');
    const round = m.roundInfo?.name || m.round?.name || m.round || '';
    const homeTeam = m.homeTeam?.name || m.player1?.name || '—';
    const awayTeam = m.awayTeam?.name || m.player2?.name || '—';
    const homeScore = m.homeScore?.current ?? m.score?.home ?? '';
    const awayScore = m.awayScore?.current ?? m.score?.away ?? '';
    const winnerCode = m.winnerCode ?? (homeScore > awayScore ? 1 : homeScore < awayScore ? 2 : 0);

    return `
      <div class="match-card">
        <div class="match-meta">${tournament}${round ? ' · ' + round : ''}</div>
        <div class="match-players">
          <div class="match-player ${winnerCode === 1 ? 'winner' : ''}">
            <span class="player-name">${homeTeam}</span>
            <span class="score">${homeScore}</span>
          </div>
          <div class="match-player ${winnerCode === 2 ? 'winner' : ''}">
            <span class="player-name">${awayTeam}</span>
            <span class="score">${awayScore}</span>
          </div>
        </div>
      </div>`;
  }).join('');
}

// ---- Calendar ----

async function loadCalendar() {
  loading('calendar-content');
  try {
    const resp = await apiFetch('/calendar');
    setContent('calendar-content', renderCalendar(resp));
  } catch (e) {
    errorMsg('calendar-content', e.message);
  }
}

function renderCalendar(resp) {
  const data = resp.data;
  const items = data?.competitions || data?.tournaments || data?.events || data?.data || (Array.isArray(data) ? data : null);
  if (!items || items.length === 0) return '<div class="placeholder">No upcoming tournaments found.</div>';

  const cards = items.map(t => {
    const name = t.name || t.tournament?.name || 'Unknown';
    const cat = t.category?.name || t.circuit || '';
    const surface = t.groundType || t.surface || t.court?.name || '';
    const start = t.startDate || (t.date ? new Date(t.date).toLocaleDateString() : '') || (t.startTimestamp ? new Date(t.startTimestamp * 1000).toLocaleDateString() : '');
    const end = t.endDate || (t.endTimestamp ? new Date(t.endTimestamp * 1000).toLocaleDateString() : '');
    const tagClass = cat.toLowerCase().includes('wta') ? 'tag-wta' : cat.toLowerCase().includes('itf') ? 'tag-itf' : 'tag-atp';

    return `
      <div class="card">
        <h3>${name}</h3>
        ${cat ? `<span class="tag ${tagClass}">${cat}</span>` : ''}
        ${surface ? `<span class="tag" style="background:#fef3c7;color:#92400e;">${surface}</span>` : ''}
        ${start ? `<p style="margin-top:.5rem">📅 ${start}${end ? ' – ' + end : ''}</p>` : ''}
      </div>`;
  }).join('');

  return `<div class="card-grid">${cards}</div>`;
}

// ---- H2H ----

document.getElementById('h2h-btn').addEventListener('click', loadH2H);

async function loadH2H() {
  const p1 = document.getElementById('h2h-p1').value;
  const p2 = document.getElementById('h2h-p2').value;
  if (!p1 || !p2) { errorMsg('h2h-content', 'Enter both player IDs.'); return; }
  loading('h2h-content');
  try {
    const resp = await apiFetch(`/h2h?p1=${p1}&p2=${p2}`);
    setContent('h2h-content', renderH2H(resp));
  } catch (e) {
    errorMsg('h2h-content', e.message);
  }
}

function renderH2H(resp) {
  const data = resp.data;
  if (!data) return jsonFallback(data);

  // New API returns court-based stats: [{court, player1wins, player2wins}]
  const courtStats = data?.data || data?.h2h || (Array.isArray(data) ? data : null);
  if (courtStats && Array.isArray(courtStats) && courtStats[0]?.court) {
    let p1Total = 0, p2Total = 0;
    courtStats.forEach(s => {
      p1Total += parseInt(s.player1wins || 0);
      p2Total += parseInt(s.player2wins || 0);
    });
    const surfaceRows = courtStats.map(s => `
      <tr>
        <td>${s.court}</td>
        <td style="text-align:center;font-weight:700;color:var(--green)">${s.player1wins}</td>
        <td style="text-align:center;font-weight:700;color:var(--accent)">${s.player2wins}</td>
      </tr>`).join('');
    return `
      <div class="h2h-summary">
        <div class="h2h-player"><div class="name">Player 1</div><div class="wins">${p1Total}</div></div>
        <div class="h2h-vs">VS</div>
        <div class="h2h-player"><div class="name">Player 2</div><div class="wins">${p2Total}</div></div>
      </div>
      <table class="rankings-table" style="margin-top:1rem">
        <thead><tr><th>Surface</th><th style="text-align:center">P1 Wins</th><th style="text-align:center">P2 Wins</th></tr></thead>
        <tbody>${surfaceRows}</tbody>
      </table>`;
  }

  // Legacy shape fallback
  const p1Name = data.player1?.name || data.homeTeam?.name || 'Player 1';
  const p2Name = data.player2?.name || data.awayTeam?.name || 'Player 2';
  const p1Wins = data.player1Wins ?? data.player1?.wins ?? data.homeWins ?? null;
  const p2Wins = data.player2Wins ?? data.player2?.wins ?? data.awayWins ?? null;
  const events = data.events || data.matches || data.results || null;
  if (p1Wins === null && p2Wins === null && !events) return jsonFallback(data);

  return `
    <div class="h2h-summary">
      <div class="h2h-player"><div class="name">${p1Name}</div><div class="wins">${p1Wins ?? '—'}</div></div>
      <div class="h2h-vs">VS</div>
      <div class="h2h-player"><div class="name">${p2Name}</div><div class="wins">${p2Wins ?? '—'}</div></div>
    </div>
    ${events?.length ? events.map(m => `<div class="match-card"><div class="match-meta">${m.tournament?.name || ''}</div></div>`).join('') : '<div class="placeholder">No match history.</div>'}`;
}

// ---- Draws ----

document.getElementById('draws-btn').addEventListener('click', loadDraws);

async function loadDraws() {
  const tid = document.getElementById('draws-tid').value;
  if (!tid) { errorMsg('draws-content', 'Enter a tournament ID.'); return; }
  loading('draws-content');
  try {
    const resp = await apiFetch(`/draws?tournament=${tid}`);
    setContent('draws-content', renderDraws(resp));
  } catch (e) {
    errorMsg('draws-content', e.message);
  }
}

function renderDraws(resp) {
  const data = resp.data;
  if (!data) return jsonFallback(data);

  const rounds = data.rounds || data.draw || data.bracket || (Array.isArray(data) ? data : null);
  if (!rounds || !Array.isArray(rounds) || rounds.length === 0) return jsonFallback(data);

  const roundsHtml = rounds.map(round => {
    const roundName = round.description || round.name || round.round || 'Round';

    const matches = [];
    if (Array.isArray(round.blocks)) {
      round.blocks.forEach(block => {
        (block.events || block.matches || []).forEach(m => matches.push(m));
      });
    } else if (Array.isArray(round.events)) {
      round.events.forEach(m => matches.push(m));
    } else if (Array.isArray(round.matches)) {
      round.matches.forEach(m => matches.push(m));
    }

    if (matches.length === 0) return '';

    const matchCardsHtml = matches.map(m => {
      const homeTeam = m.homeTeam?.name || m.player1?.name || 'TBD';
      const awayTeam = m.awayTeam?.name || m.player2?.name || 'TBD';
      const homeScore = m.homeScore?.current ?? m.score?.home ?? '';
      const awayScore = m.awayScore?.current ?? m.score?.away ?? '';
      const winnerCode = m.winnerCode ?? (homeScore !== '' && awayScore !== ''
        ? (homeScore > awayScore ? 1 : homeScore < awayScore ? 2 : 0)
        : 0);
      return `
        <div class="match-card">
          <div class="match-players">
            <div class="match-player ${winnerCode === 1 ? 'winner' : ''}">
              <span class="player-name">${homeTeam}</span>
              <span class="score">${homeScore}</span>
            </div>
            <div class="match-player ${winnerCode === 2 ? 'winner' : ''}">
              <span class="player-name">${awayTeam}</span>
              <span class="score">${awayScore}</span>
            </div>
          </div>
        </div>`;
    }).join('');

    return `
      <div class="draw-round">
        <div class="draw-round-title">${roundName}</div>
        <div class="draw-matches">${matchCardsHtml}</div>
      </div>`;
  }).join('');

  return roundsHtml || jsonFallback(data);
}

// ---- Player ----

document.getElementById('player-btn').addEventListener('click', loadPlayer);

async function loadPlayer() {
  const id = document.getElementById('player-id').value;
  if (!id) { errorMsg('player-content', 'Enter a player ID.'); return; }
  loading('player-content');
  try {
    const resp = await apiFetch(`/player?id=${id}`);
    setContent('player-content', renderPlayer(resp));
  } catch (e) {
    errorMsg('player-content', e.message);
  }
}

function renderPlayer(resp) {
  const d = resp.data?.data || resp.data?.player || resp.data;
  if (!d) return jsonFallback(resp.data);

  const name = d.name || '—';
  const country = d.country?.name || d.nationality || d.countryAcr || '—';
  const ranking = d.ranking || d.currentRanking || '—';
  const birthDate = d.dateOfBirthTimestamp
    ? new Date(d.dateOfBirthTimestamp * 1000).toLocaleDateString()
    : d.birthDate || '—';
  const hand = d.information?.plays || d.plays || d.hand || '—';
  const turned = d.information?.turnedPro || d.turnedProYear || '—';

  return `
    <div class="player-profile">
      <div class="player-avatar">🎾</div>
      <div class="player-info">
        <h2>${name}</h2>
        <div class="player-meta">
          <div class="player-meta-item"><span>Country: </span>${country}</div>
          <div class="player-meta-item"><span>Ranking: </span>#${ranking}</div>
          <div class="player-meta-item"><span>Born: </span>${birthDate}</div>
          <div class="player-meta-item"><span>Plays: </span>${hand}</div>
          <div class="player-meta-item"><span>Turned Pro: </span>${turned}</div>
        </div>
      </div>
    </div>`;
}

// ---- Search ----

document.getElementById('search-btn').addEventListener('click', doSearch);
document.getElementById('search-q').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

async function doSearch() {
  const q = document.getElementById('search-q').value.trim();
  if (!q) return;
  loading('search-content');
  try {
    const resp = await apiFetch(`/search?q=${encodeURIComponent(q)}`);
    setContent('search-content', renderSearch(resp));
  } catch (e) {
    errorMsg('search-content', e.message);
  }
}

function renderSearch(resp) {
  const data = resp.data;
  const results = data?.results || data?.players || data?.data || (Array.isArray(data) ? data : null);
  if (!results || results.length === 0) return '<div class="placeholder">No results. Search uses ranked players only (Basic plan).</div>';

  const items = results.map(r => {
    const name = r.name || r.player?.name || '—';
    const country = r.country?.name || r.nationality || r.countryAcr || r.player?.country?.name || '';
    const type = r.type || (r.sport ? 'Tournament' : 'Player');
    return `
      <div class="search-item">
        <div class="si-icon">${type === 'Tournament' ? '🏆' : '🎾'}</div>
        <div>
          <div class="si-name">${name}</div>
          <div class="si-meta">${country}${country && type ? ' · ' : ''}${type}</div>
        </div>
      </div>`;
  }).join('');

  return `<div class="search-list">${items}</div>`;
}

// ---- Auto-load ----

function autoLoad(sec) {
  if (sec === 'rankings') loadRankings();
  else if (sec === 'calendar') loadCalendar();
}

// ---- Init ----

(function init() {
  const sec = getSection();
  showSection(sec);
  autoLoad(sec);
})();
