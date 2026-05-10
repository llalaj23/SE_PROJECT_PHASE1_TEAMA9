// ─── Notification Badge Poller ────────────────────────────────────────────────
// Runs on every page. Asks the server every 10 seconds how many unread
// notifications the logged-in user has, then updates the badge in the navbar.
// ─────────────────────────────────────────────────────────────────────────────

(function () {
  const badge = document.getElementById('notification-badge');
  if (!badge) return; // Not logged in or badge not in DOM — do nothing.

  async function fetchUnreadCount() {
    try {
      const response = await fetch('/notifications/unread-count/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!response.ok) return;
      const data = await response.json();
      const count = data.unread_count || 0;
      badge.textContent = count > 0 ? count : '';
      badge.style.display = count > 0 ? 'inline' : 'none';
    } catch (_) {
      // Silently ignore network errors — badge just won't update.
    }
  }

  // Poll immediately on page load, then every 10 seconds.
  fetchUnreadCount();
  setInterval(fetchUnreadCount, 10000);
})();
