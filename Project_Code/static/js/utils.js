// ─── Shared JavaScript Utilities ─────────────────────────────────────────────
// Helpers used across multiple pages.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Reads a cookie by name. Used to get the CSRF token for fetch() requests.
 */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

/**
 * Returns the CSRF token from the cookie set by Django.
 */
function getCSRFToken() {
  return getCookie('csrftoken');
}

/**
 * Sends a POST request with JSON body and CSRF token header.
 * Usage: await postJSON('/some/url/', { key: value })
 */
async function postJSON(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
    },
    body: JSON.stringify(data),
  });
  return response.json();
}
