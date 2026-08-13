import { getUser, logout, apiJson } from './api.js';

let incidentId = null;
let currentUser = null;

// DOM refs
const userInfoEl = document.getElementById('user-info');
const logoutBtn = document.getElementById('logout-btn');

const incidentTitle = document.getElementById('incident-title');
const incidentStatusBadge = document.getElementById('incident-status-badge');
const incidentIdEl = document.getElementById('incident-id');

const incidentDescription = document.getElementById('incident-description');
const incidentPriority = document.getElementById('incident-priority');
const incidentImpact = document.getElementById('incident-impact');
const incidentUrgency = document.getElementById('incident-urgency');
const incidentApplication = document.getElementById('incident-application');
const incidentAssignee = document.getElementById('incident-assignee');
const incidentReporter = document.getElementById('incident-reporter');
const incidentCreated = document.getElementById('incident-created');
const incidentUpdated = document.getElementById('incident-updated');
const incidentResponseDue = document.getElementById('incident-response-due');
const incidentResolveDue = document.getElementById('incident-resolve-due');
const incidentHoldMinutes = document.getElementById('incident-hold-minutes');
const incidentResolutionCode = document.getElementById('incident-resolution-code');

const slaProgressBar = document.getElementById('sla-progress-bar');
const slaTimeRemaining = document.getElementById('sla-time-remaining');

const editSection = document.getElementById('edit-section');
const editTitle = document.getElementById('edit-title');
const editDescription = document.getElementById('edit-description');
const editForm = document.getElementById('edit-form');
const editError = document.getElementById('edit-error');

const statusSection = document.getElementById('status-section');
const statusSelect = document.getElementById('status-select');
const statusReason = document.getElementById('status-reason');
const resolutionCodeGroup = document.getElementById('resolution-code-group');
const resolutionCode = document.getElementById('resolution-code');
const statusForm = document.getElementById('status-form');
const statusError = document.getElementById('status-error');

const auditTbody = document.getElementById('audit-tbody');

// --- Helpers ---

function statusBadge(status) {
    const colors = {
        new: 'badge-blue',
        triage: 'badge-purple',
        assigned: 'badge-orange',
        in_progress: 'badge-yellow',
        on_hold: 'badge-gray',
        resolved: 'badge-green',
        closed: 'badge-gray',
        reopened: 'badge-red',
    };
    return `<span class="badge ${colors[status] || 'badge-gray'}">${status.replace('_', ' ')}</span>`;
}

function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getStatusOptions() {
    return ['new', 'triage', 'assigned', 'in_progress', 'on_hold', 'resolved', 'closed', 'reopened'];
}

function showError(el, msg) {
    el.textContent = msg;
    el.classList.remove('hidden');
}

function hideError(el) {
    el.textContent = '';
    el.classList.add('hidden');
}

// --- Render functions (pure display, no listeners) ---

function renderIncident(data) {
    incidentTitle.textContent = data.title || 'Untitled';
    incidentStatusBadge.innerHTML = statusBadge(data.status);
    incidentIdEl.textContent = `#${data.id}`;

    incidentDescription.textContent = data.description || '—';
    incidentPriority.textContent = data.priority ? data.priority.code : '—';
    incidentImpact.textContent = data.impact || '—';
    incidentUrgency.textContent = data.urgency || '—';
    incidentApplication.textContent = data.application ? data.application.name : '—';
    incidentAssignee.textContent = data.assignee ? data.assignee.name : 'Unassigned';
    incidentReporter.textContent = data.reporter ? data.reporter.name : '—';
    incidentCreated.textContent = formatDate(data.created_at);
    incidentUpdated.textContent = formatDate(data.updated_at);
    incidentResponseDue.textContent = formatDate(data.response_due);
    incidentResolveDue.textContent = formatDate(data.resolve_due);
    incidentHoldMinutes.textContent = data.total_hold_minutes || 0;
    incidentResolutionCode.textContent = data.resolution_code || '—';
}

function renderAuditLog(logs) {
    if (!logs || logs.length === 0) {
        auditTbody.innerHTML = '<tr><td colspan="6" class="text-center">No audit entries.</td></tr>';
        return;
    }
    const rows = logs.map(log => `
        <tr>
            <td>${log.field_changed}</td>
            <td>${log.old_value || '—'}</td>
            <td>${log.new_value || '—'}</td>
            <td>${log.reason || '—'}</td>
            <td>${log.actor_name || 'System'}</td>
            <td>${formatDate(log.timestamp)}</td>
        </tr>
    `).join('');
    auditTbody.innerHTML = rows;
}

function renderSLA(data) {
    if (!data.resolve_due) {
        slaTimeRemaining.textContent = 'No SLA deadline set.';
        slaProgressBar.style.width = '0%';
        return;
    }
    const now = new Date();
    const created = new Date(data.created_at);
    const resolveDue = new Date(data.resolve_due);

    const total = resolveDue - created;
    const elapsed = now - created;
    const progress = total > 0 ? Math.min((elapsed / total) * 100, 100) : 0;
    slaProgressBar.style.width = `${progress}%`;

    if (progress >= 100) {
        slaProgressBar.style.background = '#dc2626';
        slaTimeRemaining.textContent = 'SLA breached!';
    } else {
        const remaining = resolveDue - now;
        const hours = Math.floor(remaining / (1000 * 60 * 60));
        const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
        slaTimeRemaining.textContent = `${hours}h ${minutes}m remaining`;
    }
}

// --- Permission helpers ---

function canEdit(data) {
    if (currentUser.role === 'reporter') {
        return data.reporter_id === currentUser.id && ['new', 'triage'].includes(data.status);
    }
    if (currentUser.role === 'support_engineer') {
        return data.assignee_id === currentUser.id;
    }
    return ['team_lead', 'admin'].includes(currentUser.role);
}

function canUpdateStatus(data) {
    if (currentUser.role === 'reporter') return false;
    if (currentUser.role === 'support_engineer') {
        return data.assignee_id === currentUser.id;
    }
    return ['team_lead', 'admin'].includes(currentUser.role);
}

// --- Data refresh (re-fetch + re-render, no form setup) ---

async function refreshIncidentData() {
    try {
        const data = await apiJson(`/incidents/${incidentId}`);
        if (!data) return;
        renderIncident(data);
        renderAuditLog(data.audit_logs || []);
        renderSLA(data);
    } catch (err) {
        console.error('Failed to refresh incident data:', err);
    }
}

// --- Form setup (called once on initial load) ---

function setupEditForm(data) {
    const submitBtn = editForm.querySelector('button[type="submit"]');

    editTitle.value = data.title || '';
    editDescription.value = data.description || '';

    // Remove any existing listener to prevent duplicates (safe guard)
    editForm.removeEventListener('submit', editForm._submitHandler);
    editForm._submitHandler = async (e) => {
        e.preventDefault();
        hideError(editError);

        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Saving…';

        const payload = {
            title: editTitle.value.trim(),
            description: editDescription.value.trim(),
        };

        try {
            const response = await apiJson(`/incidents/${incidentId}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
            if (response) {
                alert('Incident updated successfully.');
                await refreshIncidentData();
            }
        } catch (err) {
            showError(editError, err.message || 'Failed to update incident.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    };
    editForm.addEventListener('submit', editForm._submitHandler);
}

function setupStatusForm(data) {
    const submitBtn = statusForm.querySelector('button[type="submit"]');

    // Populate status dropdown
    const options = getStatusOptions();
    statusSelect.innerHTML = options.map(s =>
        `<option value="${s}" ${s === data.status ? 'selected' : ''}>${s.replace('_', ' ')}</option>`
    ).join('');

    // Show/hide resolution code based on selected status
    statusSelect.addEventListener('change', () => {
        resolutionCodeGroup.style.display = statusSelect.value === 'closed' ? 'block' : 'none';
    });
    resolutionCodeGroup.style.display = statusSelect.value === 'closed' ? 'block' : 'none';

    // Remove any existing listener to prevent duplicates
    statusForm.removeEventListener('submit', statusForm._submitHandler);
    statusForm._submitHandler = async (e) => {
        e.preventDefault();
        hideError(statusError);

        submitBtn.disabled = true;
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Updating…';

        const payload = {
            status: statusSelect.value,
            reason: statusReason.value.trim() || null,
        };
        if (statusSelect.value === 'closed') {
            payload.resolution_code = resolutionCode.value;
        }

        try {
            const response = await apiJson(`/incidents/${incidentId}/status`, {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            if (response) {
                alert('Status updated successfully.');
                await refreshIncidentData();
            }
        } catch (err) {
            const msg = err.message || 'Failed to update status.';
            showError(statusError, msg);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    };
    statusForm.addEventListener('submit', statusForm._submitHandler);
}

// --- Initial load (runs once on page load) ---

async function loadIncidentDetail() {
    currentUser = getUser();
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    userInfoEl.textContent = `${currentUser.name} (${currentUser.role})`;

    const params = new URLSearchParams(window.location.search);
    incidentId = params.get('id');
    if (!incidentId) {
        alert('No incident ID provided.');
        window.location.href = '/dashboard.html';
        return;
    }

    try {
        const data = await apiJson(`/incidents/${incidentId}`);
        if (!data) return;

        // Render everything
        renderIncident(data);
        renderAuditLog(data.audit_logs || []);
        renderSLA(data);

        // Setup forms only once
        setupEditForm(data);
        setupStatusForm(data);

        // Show/hide sections based on permissions
        if (canEdit(data)) {
            editSection.style.display = 'block';
        }
        if (canUpdateStatus(data)) {
            statusSection.style.display = 'block';
        }
    } catch (err) {
        console.error('Failed to load incident:', err);
        document.querySelector('#incident-content').innerHTML = '<p>Error loading incident.</p>';
    }
}

// --- Init ---
document.addEventListener('DOMContentLoaded', loadIncidentDetail);
logoutBtn.addEventListener('click', logout);