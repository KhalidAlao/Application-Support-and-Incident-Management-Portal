
import { login, getUser } from './api.js';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const errorElement = document.getElementById('login-error');
    const submitButton = form.querySelector('button[type="submit"]');

    // If user is already logged in, skip login and go to dashboard
    if (getUser()) {
        window.location.href = '/dashboard.html';
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Clear previous error
        errorElement.textContent = '';
        errorElement.classList.add('hidden');

        const email = emailInput.value.trim();
        const password = passwordInput.value;

        if (!email || !password) {
            errorElement.textContent = 'Please fill in both fields.';
            errorElement.classList.remove('hidden');
            return;
        }

        // Disable button and show loading state
        submitButton.disabled = true;
        submitButton.textContent = 'Signing in…';

        try {
            await login(email, password);

            // On success, redirect to dashboard (or the `next` param)
            const urlParams = new URLSearchParams(window.location.search);
            const next = urlParams.get('next') || '/dashboard.html';
            window.location.href = next;
        } catch (err) {
            errorElement.textContent = err.message || 'Login failed. Please try again.';
            errorElement.classList.remove('hidden');
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Sign In';
        }
    });
});