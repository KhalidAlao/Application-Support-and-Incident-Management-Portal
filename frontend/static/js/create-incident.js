import { getUser, logout, apiJson } from './api.js';

const userInfoEl = document.getElementById('user-info');
const logoutBtn = document.getElementById('logout-btn');
const form = document.getElementById('create-form');
const titleInput = document.getElementById('incident-title');
const descriptionInput = document.getElementById('incident-description');
const priorityTextInput = document.getElementById('reported-priority-text');
const applicationSelect = document.getElementById('application-select');
const errorEl = document.getElementById('create-error');
const submitBtn = form.querySelector('button[type="submit"]');

async function loadCreatePage() {
    const user = getUser();
    if (!user) {
        window.location.href = '/login.html';
        return;
    }
    userInfoEl.textContent = `${user.name} (${user.role})`;

    await loadApplications();

    form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.classList.add('hidden');

    const title = titleInput.value.trim();
    const description = descriptionInput.value.trim();
    const applicationId = applicationSelect.value;
    const reportedPriority = priorityTextInput.value.trim(); // <-- read it

    if (!title || !description || !applicationId) {
        errorEl.textContent = 'Title, Description, and Application are required.';
        errorEl.classList.remove('hidden');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating…';

    const payload = {
        title,
        description,
        reported_priority_text: reportedPriority || null, // <-- now included
        application_id: parseInt(applicationId, 10)
    };

    try {
        const data = await apiJson('/incidents', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (data) {
            window.location.href = `/incident-detail.html?id=${data.id}`;
        }
    } catch (err) {
        errorEl.textContent = err.message || 'Failed to create incident.';
        errorEl.classList.remove('hidden');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Incident';
    }
});

    logoutBtn.addEventListener('click', logout);
}

async function loadApplications() {
    try {
        const data = await apiJson('/applications');
        if (data && data.length) {
            applicationSelect.innerHTML = '<option value="">Select an application</option>';
            data.forEach(app => {
                const opt = document.createElement('option');
                opt.value = app.id;
                opt.textContent = app.name;
                applicationSelect.appendChild(opt);
            });
        } else {
            applicationSelect.innerHTML = '<option value="">No applications available</option>';
        }
    } catch (err) {
        applicationSelect.innerHTML = '<option value="">Error loading applications</option>';
        console.error('Failed to load applications:', err);
    }
}

document.addEventListener('DOMContentLoaded', loadCreatePage);