// Mini App JavaScript - UPPERCASE style

// Global state
let channels = [];
let settings = {};
let subscribersChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initSubTabs();
    loadChannels();
    loadSettings();
    loadUpcomingAnimes();
});

// Navigation between main tabs
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active class to clicked item
            item.classList.add('active');
            
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            const tabId = item.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            // Load data for specific tabs
            if (tabId === 'stats') loadChannels();
            if (tabId === 'animes') loadUpcomingAnimes();
            if (tabId === 'groupes') loadGroups();
            if (tabId === 'controle') loadChannelControl();
        });
    });
}

// Sub-tabs (for publication)
function initSubTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const parent = btn.closest('.tabs');
            parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const subtab = btn.getAttribute('data-subtab');
            parent.parentElement.querySelectorAll('.subtab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            document.getElementById(subtab + 'Pub').classList.add('active');
        });
    });
}

// Load channels from API
async function loadChannels() {
    try {
        const response = await fetch('/api/channels');
        channels = await response.json();
        
        renderChannels(channels);
        renderChannelCheckboxes();
    } catch (error) {
        console.error('Error loading channels:', error);
    }
}

// Render channels grid
function renderChannels(channelsToRender) {
    const grid = document.getElementById('channelsGrid');
    
    if (!channelsToRender || channelsToRender.length === 0) {
        grid.innerHTML = '<p style="text-align: center; color: #888;">AUCUN CANAL TROUVÉ</p>';
        return;
    }
    
    grid.innerHTML = channelsToRender.map(channel => `
        <div class="channel-card" onclick="showChannelDetail('${channel.telegram_id}')">
            <img src="${channel.photo_url || '/static/default-channel.png'}" alt="${channel.name}" class="channel-photo">
            <div class="channel-info">
                <div class="channel-name">${channel.name || 'CANAL SANS NOM'}</div>
                <div class="channel-username">@${channel.username || channel.telegram_id}</div>
                <div class="channel-stats">📊 ${channel.subscribers || 0} ABONNÉS</div>
            </div>
            <button class="channel-details-btn">DÉTAILS</button>
        </div>
    `).join('');
}

// Render channel checkboxes for publication forms
function renderChannelCheckboxes() {
    const checkboxContainers = [
        document.getElementById('channelCheckboxes'),
        document.getElementById('scheduleChannelCheckboxes')
    ];
    
    checkboxContainers.forEach(container => {
        if (!container) return;
        
        container.innerHTML = channels.map(channel => `
            <label class="checkbox-item">
                <input type="checkbox" value="${channel.telegram_id}" name="channels">
                ${channel.name || '@' + (channel.username || channel.telegram_id)}
            </label>
        `).join('');
    });
}

// Show channel detail modal
async function showChannelDetail(channelId) {
    const channel = channels.find(c => c.telegram_id === channelId);
    if (!channel) return;
    
    const modal = document.getElementById('channelModal');
    const modalName = document.getElementById('modalChannelName');
    
    modalName.textContent = channel.name || ('@' + (channel.username || channelId));
    
    // Load channel details
    try {
        const response = await fetch(`/api/channels/${channelId}/details`);
        const details = await response.json();
        
        // Update chart
        updateSubscribersChart(details.subscriber_history);
        
        // Load episodes
        renderEpisodes(details.episodes);
        
        modal.classList.add('active');
    } catch (error) {
        console.error('Error loading channel details:', error);
    }
}

// Close modal
document.querySelector('.close-btn').addEventListener('click', () => {
    document.getElementById('channelModal').classList.remove('active');
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('channelModal');
    if (e.target === modal) {
        modal.classList.remove('active');
    }
});

// Update subscribers chart
function updateSubscribersChart(history) {
    const ctx = document.getElementById('subscribersChart').getContext('2d');
    
    if (subscribersChart) {
        subscribersChart.destroy();
    }
    
    const labels = history.map(h => h.date);
    const data = history.map(h => h.count);
    
    subscribersChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'ABONNÉS',
                data: data,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#fff',
                        font: {
                            family: "'Arial Black', sans-serif",
                            size: 12
                        }
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        color: '#888'
                    },
                    grid: {
                        color: '#333'
                    }
                },
                x: {
                    ticks: {
                        color: '#888'
                    },
                    grid: {
                        color: '#333'
                    }
                }
            }
        }
    });
}

// Render episodes list
function renderEpisodes(episodes) {
    const episodeList = document.getElementById('episodeList');
    
    if (!episodes || episodes.length === 0) {
        episodeList.innerHTML = '<p style="color: #888;">AUCUN ÉPISODE TROUVÉ</p>';
        return;
    }
    
    episodeList.innerHTML = episodes.map(ep => `
        <div class="episode-item">
            <div class="episode-title">${ep.title || 'ÉPISODE SANS TITRE'}</div>
            <div class="episode-stats">
                <span>👁️ ${ep.views || 0}</span>
                <span>👍 ${ep.likes || 0}</span>
                <span>💬 ${ep.comments || 0}</span>
            </div>
        </div>
    `).join('');
}

// Load upcoming animes
async function loadUpcomingAnimes() {
    try {
        const response = await fetch('/api/animes/upcoming');
        const animes = await response.json();
        
        const container = document.getElementById('upcomingAnimes');
        
        if (!animes || animes.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #888;">AUCUN ANIME À VENIR TROUVÉ</p>';
            return;
        }
        
        container.innerHTML = animes.map(anime => `
            <div class="anime-card">
                <img src="${anime.cover_image || '/static/default-anime.png'}" alt="${anime.title}" class="anime-cover">
                <div class="anime-info">
                    <div class="anime-title">${anime.title}</div>
                    <div class="anime-genres">${(anime.genres || []).join(', ')}</div>
                    <div class="anime-date">📅 ${anime.release_date || 'DATE INCONNUE'}</div>
                    <button class="anime-program-btn" onclick="programAnimePublication('${anime.title}', '${anime.cover_image || ''}')">PROGRAMMER PUBLICATION</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading upcoming animes:', error);
    }
}

// Program anime publication (prefill form)
function programAnimePublication(title, coverUrl) {
    // Switch to publication tab
    document.querySelector('[data-tab="publication"]').click();
    
    // Switch to scheduled publication
    document.querySelector('[data-subtab="schedule"]').click();
    
    // Prefill content
    const contentField = document.getElementById('scheduleContent');
    contentField.value = `🎬 NOUVEAU ANIME À VENIR\n\n${title}\n\nRESTEZ CONNECTÉS POUR PLUS D'INFOS!`;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Load groups
async function loadGroups() {
    try {
        const response = await fetch('/api/groups');
        const groups = await response.json();
        
        const container = document.getElementById('groupsList');
        
        if (!groups || groups.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #888;">AUCUN GROUPE TROUVÉ</p>';
            return;
        }
        
        container.innerHTML = groups.map(group => `
            <div class="group-card">
                <div class="group-info">
                    <h3>${group.name || 'GROUPE SANS NOM'}</h3>
                    <div class="group-stats">${group.members || 0} MEMBRES</div>
                </div>
                <div class="group-activity">
                    <div class="activity-indicator">${getActivityIndicator(group.activity_level)}</div>
                    <div class="activity-level">${group.messages_per_day || 0} MSG/JOUR</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading groups:', error);
    }
}

// Get activity indicator emoji
function getActivityIndicator(level) {
    if (level >= 100) return '🔥';
    if (level >= 50) return '📈';
    if (level >= 20) return '📊';
    return '📉';
}

// Load channel control
async function loadChannelControl() {
    try {
        const response = await fetch('/api/channels');
        const channels = await response.json();
        
        const container = document.getElementById('channelControl');
        
        if (!channels || channels.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #888;">AUCUN CANAL TROUVÉ</p>';
            return;
        }
        
        container.innerHTML = channels.map(channel => `
            <div class="channel-control-item">
                <div class="channel-status">
                    <span class="status-indicator ${getStatusClass(channel.status)}"></span>
                    <span class="status-text">${channel.status || 'ACTIVE'}</span>
                </div>
                <div>
                    <strong>${channel.name || '@' + (channel.username || channel.telegram_id)}</strong>
                </div>
                <div class="control-buttons">
                    <button class="btn-small btn-activate" onclick="updateChannelStatus('${channel.telegram_id}', 'ACTIVE')">ACTIF</button>
                    <button class="btn-small btn-test" onclick="updateChannelStatus('${channel.telegram_id}', 'TESTING')">TEST</button>
                    <button class="btn-small btn-deactivate" onclick="updateChannelStatus('${channel.telegram_id}', 'INACTIVE')">INACTIF</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading channel control:', error);
    }
}

// Get status class
function getStatusClass(status) {
    switch (status) {
        case 'ACTIVE': return 'active';
        case 'TESTING': return 'testing';
        case 'INACTIVE': return 'inactive';
        default: return 'active';
    }
}

// Update channel status
async function updateChannelStatus(channelId, status) {
    try {
        await fetch(`/api/channels/${channelId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        
        // Reload channel control
        loadChannelControl();
        
        alert(`STATUT DU CANAL MIS À JOUR: ${status}`);
    } catch (error) {
        console.error('Error updating channel status:', error);
        alert('ERREUR LORS DE LA MISE À JOUR DU STATUT');
    }
}

// Load settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        settings = await response.json();
        
        // Populate form
        document.getElementById('hfModel').value = settings.hf_model_name || 'mistralai/Mistral-7B-Instruct-v0.2';
        document.getElementById('weightLikes').value = Math.round((settings.weight_likes || 0.5) * 100);
        document.getElementById('weightViews').value = Math.round((settings.weight_views || 0.3) * 100);
        document.getElementById('weightComments').value = Math.round((settings.weight_comments || 0.2) * 100);
        document.getElementById('timezone').value = settings.timezone || 'UTC';
        document.getElementById('debugMode').checked = !!settings.debug_mode;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Save settings
document.getElementById('settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const newSettings = {
        hf_model_name: document.getElementById('hfModel').value,
        weight_likes: parseInt(document.getElementById('weightLikes').value) / 100,
        weight_views: parseInt(document.getElementById('weightViews').value) / 100,
        weight_comments: parseInt(document.getElementById('weightComments').value) / 100,
        timezone: document.getElementById('timezone').value,
        debug_mode: document.getElementById('debugMode').checked ? 1 : 0
    };
    
    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newSettings)
        });
        
        alert('PARAMÈTRES SAUVEGARDÉS AVEC SUCCÈS!');
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('ERREUR LORS DE LA SAUVEGARDE DES PARAMÈTRES');
    }
});

// Direct publication form
document.getElementById('directPubForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const content = document.getElementById('pubContent').value;
    const mediaFile = document.getElementById('pubMedia').files[0];
    const selectedChannels = Array.from(document.querySelectorAll('#channelCheckboxes input:checked'))
        .map(cb => cb.value);
    
    if (selectedChannels.length === 0) {
        alert('VÉUILLEZ SÉLECTIONNER AU MOINS UN CANAL');
        return;
    }
    
    const formData = new FormData();
    formData.append('content', content);
    if (mediaFile) formData.append('media', mediaFile);
    formData.append('channels', JSON.stringify(selectedChannels));
    
    try {
        const response = await fetch('/api/publish/direct', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            alert('PUBLICATION ENVOYÉE AVEC SUCCÈS!');
            document.getElementById('directPubForm').reset();
        } else {
            alert('ERREUR LORS DE LA PUBLICATION');
        }
    } catch (error) {
        console.error('Error publishing:', error);
        alert('ERREUR LORS DE LA PUBLICATION');
    }
});

// Scheduled publication form
document.getElementById('schedulePubForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const content = document.getElementById('scheduleContent').value;
    const mediaFile = document.getElementById('scheduleMedia').files[0];
    const selectedChannels = Array.from(document.querySelectorAll('#scheduleChannelCheckboxes input:checked'))
        .map(cb => cb.value);
    const scheduledTime = document.getElementById('scheduleDateTime').value;
    const repeatType = document.getElementById('repeatType').value;
    const repeatInterval = document.getElementById('repeatInterval').value;
    
    if (selectedChannels.length === 0) {
        alert('VÉUILLEZ SÉLECTIONNER AU MOINS UN CANAL');
        return;
    }
    
    const formData = new FormData();
    formData.append('content', content);
    if (mediaFile) formData.append('media', mediaFile);
    formData.append('channels', JSON.stringify(selectedChannels));
    formData.append('scheduled_time', scheduledTime);
    formData.append('repeat_type', repeatType);
    formData.append('repeat_interval', repeatInterval);
    
    try {
        const response = await fetch('/api/publish/schedule', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            alert('PUBLICATION PROGRAMMÉE AVEC SUCCÈS!');
            document.getElementById('schedulePubForm').reset();
        } else {
            alert('ERREUR LORS DE LA PROGRAMMATION');
        }
    } catch (error) {
        console.error('Error scheduling:', error);
        alert('ERREUR LORS DE LA PROGRAMMATION');
    }
});

// Handle repeat type change
document.getElementById('repeatType').addEventListener('change', (e) => {
    const intervalGroup = document.getElementById('intervalGroup');
    intervalGroup.style.display = e.target.value === 'INTERVAL' ? 'block' : 'none';
});

// Sort filter
document.getElementById('sortFilter').addEventListener('change', (e) => {
    const sortValue = e.target.value;
    
    let sortedChannels = [...channels];
    
    if (sortValue === 'alpha') {
        sortedChannels.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    } else if (sortValue === 'stats') {
        sortedChannels.sort((a, b) => (b.subscribers || 0) - (a.subscribers || 0));
    }
    
    renderChannels(sortedChannels);
});
