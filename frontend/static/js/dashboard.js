
import { getUser, logout, apiJson } from './api.js';

// Global state
let currentUser = null;
let currentFilters = {};
let currentPage = 1;
let totalPages = 1;
let totalItems = 0;
let applications = [];
let users = [];

// DOM refs
const userInfoEl = document.getElementById('user-info');
const logoutBtn = document.getElementById('logout-btn');

const summarySection = document.getElementById('summary-section');
const totalOpenEl = document.getElementById('total-open');
const totalClosedEl = document.getElementById('total-closed');
const statusNewEl = document.getElementById('status-new');
const statusInProgressEl = document.getElementById('status-in-progress');
const overdueCountEl = document.getElementById('overdue-count');

const filterForm = document.getElementById('filter-form');
const filterStatus = document.getElementById('filter-status');
const filterApplication = document.getElementById('filter-application');
const filterAssignee = document.getElementById('filter-assignee');
const filterDateFrom = document.getElementById('filter-date-from');
const filterDateTo = document.getElementById('filter-date-to');
const clearFiltersBtn = document.getElementById('clear-filters');

const incidentTbody = document.getElementById('incident-tbody');
const incidentCountEl = document.getElementById('incident-count');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageInfoEl = document.getElementById('page-info');

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

// --- Fetch and render ---

async function loadDashboard() {
    currentUser = getUser();
    if (!currentUser) {
        window.location.href = '/login.html';
        return;
    }
    userInfoEl.textContent = `${currentUser.name} (${currentUser.role})`;

    // Load filter dropdowns
    await loadApplications();
    await loadUsers();

    // Parse URL params for filters
    const params = new URLSearchParams(window.location.search);
    currentFilters = {
        status: params.get('status') || '',
        application_id: params.get('application_id') || '',
        assignee_id: params.get('assignee_id') || '',
        created_after: params.get('created_after') || '',
        created_before: params.get('created_before') || '',
    };
    currentPage = parseInt(params.get('page')) || 1;

    // Populate form fields
    filterStatus.value = currentFilters.status;
    filterApplication.value = currentFilters.application_id;
    filterAssignee.value = currentFilters.assignee_id;
    filterDateFrom.value = currentFilters.created_after;
    filterDateTo.value = currentFilters.created_before;

    // Load summary (if staff) and incident list
    await loadSummary();
    await loadIncidents();

    // Event listeners
    filterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        applyFilters();
    });
    clearFiltersBtn.addEventListener('click', () => {
        filterForm.reset();
        applyFilters();
    });
    prevPageBtn.addEventListener('click', () => goToPage(currentPage - 1));
    nextPageBtn.addEventListener('click', () => goToPage(currentPage + 1));
    logoutBtn.addEventListener('click', logout);
}

async function loadApplications() {
    try {
        const data = await apiJson('/applications');
        if (data) {
            applications = data;
            filterApplication.innerHTML = '<option value="">All</option>';
            data.forEach(app => {
                const opt = document.createElement('option');
                opt.value = app.id;
                opt.textContent = app.name;
                filterApplication.appendChild(opt);
            });
        }
    } catch (e) {
        console.error('Failed to load applications:', e);
    }
}

async function loadUsers() {
    if (currentUser.role === 'reporter') {
        filterAssignee.parentElement.style.display = 'none';
        return;
    }
    try {
        const data = await apiJson('/users');
        if (data) {
            users = data;
            filterAssignee.innerHTML = '<option value="">All</option>';
            data.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u.id;
                opt.textContent = u.name;
                filterAssignee.appendChild(opt);
            });
        }
    } catch (e) {
        console.error('Failed to load users:', e);
    }
}

async function loadSummary() {
    if (currentUser.role === 'reporter') {
        summarySection.style.display = 'none';
        return;
    }
    try {
        const data = await apiJson('/reports/summary');
        if (data) {
            totalOpenEl.textContent = data.total_open || 0;
            totalClosedEl.textContent = data.total_closed || 0;
            const statusCounts = data.status_counts || {};
            statusNewEl.textContent = statusCounts.new || 0;
            statusInProgressEl.textContent = statusCounts.in_progress || 0;
        }
        const overdueData = await apiJson('/reports/overdue-count');
        if (overdueData) {
            overdueCountEl.textContent = overdueData.count || 0;
        }
    } catch (e) {
        console.error('Failed to load summary:', e);
    }
}

async function loadIncidents() {
    const params = new URLSearchParams();
    if (currentFilters.status) params.set('status', currentFilters.status);
    if (currentFilters.application_id) params.set('application_id', currentFilters.application_id);
    if (currentFilters.assignee_id) params.set('assignee_id', currentFilters.assignee_id);
    if (currentFilters.created_after) params.set('created_after', currentFilters.created_after);
    if (currentFilters.created_before) params.set('created_before', currentFilters.created_before);
    params.set('page', currentPage);
    params.set('per_page', 20);

    const url = `/incidents?${params.toString()}`;
    try {
        const data = await apiJson(url);
        if (!data) return;

        const items = data.items || [];
        totalItems = data.total || 0;
        totalPages = data.pages || 1;
        incidentCountEl.textContent = totalItems;

        renderIncidentRows(items);
        updatePagination();
    } catch (e) {
        console.error('Failed to load incidents:', e);
        incidentTbody.innerHTML = '<tr><td colspan="8" class="text-center">Error loading incidents.</td></tr>';
    }
}

function renderIncidentRows(items) {
    if (!items || items.length === 0) {
        incidentTbody.innerHTML = '<tr><td colspan="8" class="text-center">No incidents found.</td></tr>';
        return;
    }
    const rows = items.map(inc => {
        const priorityLabel = inc.priority ? inc.priority.code : '—';
        const assigneeName = inc.assignee ? inc.assignee.name : 'Unassigned';
        const appName = inc.application ? inc.application.name : '—';
        return `<tr>
            <td><a href="/incident-detail.html?id=${inc.id}">#${inc.id}</a></td>
            <td>${inc.title}</td>
            <td>${statusBadge(inc.status)}</td>
            <td>${priorityLabel}</td>
            <td>${appName}</td>
            <td>${assigneeName}</td>
            <td>${formatDate(inc.created_at)}</td>
            <td><a href="/incident-detail.html?id=${inc.id}" class="btn btn-sm btn-secondary">View</a></td>
        </tr>`;
    }).join('');
    incidentTbody.innerHTML = rows;
}

function updatePagination() {
    pageInfoEl.textContent = `Page ${currentPage} of ${totalPages}`;
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages;
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    updateUrl();
    loadIncidents();
}

function applyFilters() {
    currentFilters.status = filterStatus.value;
    currentFilters.application_id = filterApplication.value;
    currentFilters.assignee_id = filterAssignee.value;
    currentFilters.created_after = filterDateFrom.value;
    currentFilters.created_before = filterDateTo.value;
    currentPage = 1;
    updateUrl();
    loadIncidents();
    loadSummary();
}

function updateUrl() {
    const params = new URLSearchParams();
    for (const [key, val] of Object.entries(currentFilters)) {
        if (val) params.set(key, val);
    }
    if (currentPage > 1) params.set('page', currentPage);
    const newUrl = window.location.pathname + '?' + params.toString();
    window.history.pushState({}, '', newUrl);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', loadDashboard);

window.addEventListener('popstate', () => {
    const params = new URLSearchParams(window.location.search);
    currentFilters.status = params.get('status') || '';
    currentFilters.application_id = params.get('application_id') || '';
    currentFilters.assignee_id = params.get('assignee_id') || '';
    currentFilters.created_after = params.get('created_after') || '';
    currentFilters.created_before = params.get('created_before') || '';
    currentPage = parseInt(params.get('page')) || 1;
    filterStatus.value = currentFilters.status;
    filterApplication.value = currentFilters.application_id;
    filterAssignee.value = currentFilters.assignee_id;
    filterDateFrom.value = currentFilters.created_after;
    filterDateTo.value = currentFilters.created_before;
    loadIncidents();
    loadSummary();
});