import { getUser, logout } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const user = getUser();
    if (!user) {
        // No user stored – redirect to login
        window.location.href = '/login.html';
        return;
    }

    document.getElementById('user-name').textContent = user.name || 'Unknown';
    document.getElementById('user-role').textContent = user.role || 'N/A';

    document.getElementById('logout-btn').addEventListener('click', logout);
});