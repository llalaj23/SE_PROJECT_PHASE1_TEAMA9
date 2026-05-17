// ─── Badge Pollers ────────────────────────────────────────────────────────────
// Runs on every authenticated page (loaded from base.html).
// Updates the notification bell badge and the inbox badge every 10 seconds.
// ─────────────────────────────────────────────────────────────────────────────

(function () {
  const notifBadge = document.getElementById('notification-badge');
  const inboxBadge = document.getElementById('inbox-badge');

  // ── Notification bell badge ────────────────────────────────────────────────
  async function fetchNotifCount() {
    try {
      const r = await fetch('/notifications/unread-count/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!r.ok) return;
      const data = await r.json();
      const count = data.unread_count || 0;
      if (notifBadge) {
        notifBadge.textContent = count > 0 ? count : '';
        notifBadge.style.display = count > 0 ? 'inline' : 'none';
      }
    } catch (_) {
      // Silently ignore network errors.
    }
  }

  // ── Inbox (unread messages) badge ─────────────────────────────────────────
  async function fetchInboxCount() {
    try {
      const r = await fetch('/messages/unread-count/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!r.ok) return;
      const data = await r.json();
      const count = data.count || 0;
      if (inboxBadge) {
        inboxBadge.textContent = count > 0 ? count : '';
        inboxBadge.style.display = count > 0 ? 'inline' : 'none';
      }
    } catch (_) {
      // Silently ignore network errors.
    }
  }

  // Poll immediately on page load, then every 10 seconds.
  fetchNotifCount();
  fetchInboxCount();
  setInterval(function () {
    fetchNotifCount();
    fetchInboxCount();
  }, 10000);
})();
