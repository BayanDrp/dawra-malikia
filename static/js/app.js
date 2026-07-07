document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await fetch('/auth/logout', { method: 'POST' });
      } catch (err) {}
      window.location.href = '/login';
    });
  }
});
