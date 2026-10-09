/**
 * FindBack Real-Time Synchronization Client
 * Uses WebSockets via Django Channels with exponential backoff reconnection
 * and intelligent background polling fallback when disconnected.
 */
(function() {
  'use strict';

  let socket = null;
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 10;
  let baseReconnectDelay = 1000;
  let pingInterval = null;
  let pollingInterval = null;

  const indicator = document.getElementById('ws-indicator');

  function updateIndicator(status) {
    if (!indicator) return;
    if (status === 'connected') {
      indicator.className = 'hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200';
      indicator.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span><span>Live Sync</span>';
    } else if (status === 'connecting') {
      indicator.className = 'hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200';
      indicator.innerHTML = '<span class="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span><span>Connecting...</span>';
    } else {
      indicator.className = 'hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200';
      indicator.innerHTML = '<span class="w-2 h-2 rounded-full bg-slate-400"></span><span>Polling Fallback</span>';
    }
  }

  function handleEvent(eventData) {
    const type = eventData.type;
    const data = eventData.data || {};

    // 1. Update Notification Badges across the UI
    if (type === 'notification' || data.unread_count !== undefined) {
      const badge = document.getElementById('notification-badge') || document.querySelector('[data-notification-badge]');
      if (badge && data.unread_count !== undefined) {
        badge.textContent = data.unread_count;
        if (data.unread_count > 0) {
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      }

      // If user is currently on the notifications page or dashboard, update activity
      const liveAlertContainer = document.getElementById('live-alerts-container');
      if (liveAlertContainer && data.title) {
        const alertEl = document.createElement('div');
        alertEl.className = 'p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-900 flex items-center justify-between animate-fade-in shadow-sm';
        alertEl.innerHTML = `<span><strong>${data.title}:</strong> ${data.message || ''}</span><span class="text-blue-500 text-xs font-bold">Just now</span>`;
        liveAlertContainer.prepend(alertEl);
      }
    }

    // 2. Update Claim Statuses in real-time
    if (type === 'claim_status' && data.claim_id) {
      const claimCard = document.getElementById(`claim-card-${data.claim_id}`);
      if (claimCard) {
        const badge = claimCard.querySelector('.claim-status-badge');
        if (badge) {
          badge.textContent = data.status;
          if (data.status === 'APPROVED') {
            badge.className = 'claim-status-badge px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800';
          } else if (data.status === 'REJECTED') {
            badge.className = 'claim-status-badge px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-100 text-rose-800';
          }
        }
      }
    }

    // 3. Dispatch custom browser event for page-specific listeners
    window.dispatchEvent(new CustomEvent('findback:realtime', { detail: eventData }));
  }

  function startSmartPolling() {
    if (pollingInterval) return;
    pollingInterval = setInterval(async () => {
      // Don't poll if document is hidden (user switched tabs)
      if (document.hidden) return;
      try {
        const resp = await fetch('/api/updates/');
        if (resp.ok) {
          const data = await resp.json();
          handleEvent({ type: 'poll_update', data: data });
        }
      } catch (err) {
        // Silent failure on polling error
      }
    }, 25000);
  }

  function stopSmartPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
  }

  function connect() {
    updateIndicator('connecting');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/updates/`;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = function() {
        reconnectAttempts = 0;
        updateIndicator('connected');
        stopSmartPolling();

        // Send periodic heartbeat ping
        if (pingInterval) clearInterval(pingInterval);
        pingInterval = setInterval(() => {
          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      socket.onmessage = function(event) {
        try {
          const payload = JSON.parse(event.data);
          handleEvent(payload);
        } catch (e) {
          console.debug('Inbound message parse error:', e);
        }
      };

      socket.onclose = function(event) {
        if (pingInterval) clearInterval(pingInterval);
        updateIndicator('fallback');
        startSmartPolling();

        // Don't reconnect on normal closure or unauthorized 4001
        if (event.code === 4001 || event.code === 1000) return;

        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(baseReconnectDelay * Math.pow(2, reconnectAttempts), 30000);
          reconnectAttempts++;
          setTimeout(connect, delay);
        }
      };

      socket.onerror = function() {
        if (socket) socket.close();
      };
    } catch (err) {
      updateIndicator('fallback');
      startSmartPolling();
    }
  }

  // Initialize on DOM load if user is authenticated
  document.addEventListener('DOMContentLoaded', () => {
    connect();
  });

  // Export helper
  window.FindBackRealTime = {
    connect: connect,
    handleEvent: handleEvent
  };
})();
