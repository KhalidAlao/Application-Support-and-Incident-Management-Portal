
//
// TOKEN STORAGE TRADE-OFF:
// This app stores the JWT in localStorage for simplicity.
// localStorage is accessible to any JavaScript running on the page.
// If the app has an XSS vulnerability anywhere, an attacker can read
// the token and impersonate the user.
// In a production system handling sensitive data, prefer httpOnly cookies
// (set by the server) which are not accessible to JavaScript at all.
// See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies

const API_BASE = '/api';

// --- Token and user management ---

export function getToken() {
    return localStorage.getItem('access_token');
}

export function setToken(token) {
    localStorage.setItem('access_token', token);
}

export function removeToken() {
    localStorage.removeItem('access_token');
}

export function getUser() {
    const stored = localStorage.getItem('user');
    if (!stored) return null;
    try {
        return JSON.parse(stored);
    } catch {
        return null;
    }
}

export function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

export function removeUser() {
    localStorage.removeItem('user');
}

// --- Login / Logout ---

export async function login(email, password) {
    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || 'Login failed');
    }

    const data = await response.json();
    setToken(data.access_token);
    if (data.user) {
        setUser(data.user);
    }
    return data;
}

export function logout() {
    removeToken();
    removeUser();
    window.location.href = '/login.html';
}

// --- Fetch wrapper with automatic token attachment and 401 handling ---

export async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const url = `${API_BASE}${endpoint}`;

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers,
    };

    const response = await fetch(url, config);

    // If we get a 401, clear token and redirect to login
    if (response.status === 401) {
        removeToken();
        removeUser();
        const currentPath = window.location.pathname + window.location.search;
        window.location.href = `/login.html?next=${encodeURIComponent(currentPath)}`;
        return; // caller should not continue
    }

    return response;
}

// Helper: fetch and parse JSON
export async function apiJson(endpoint, options = {}) {
    const response = await apiFetch(endpoint, options);
    if (!response) return null;

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const error = new Error(data.error || data.message || `Request failed (${response.status})`);
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
}