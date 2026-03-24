/* Budgetry — Client-side interactivity */

// ========== Service Worker (PWA) ==========
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js');
}

// ========== Theme Toggle ==========
function initTheme() {
    const saved = localStorage.getItem('budgetry-theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }
    updateToggleIcon();
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('budgetry-theme', next);
    updateToggleIcon();
}

function updateToggleIcon() {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.textContent = isDark ? '\u2600\uFE0F' : '\uD83C\uDF19';
    btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
}

// Apply theme immediately to prevent flash
initTheme();

// ========== Delete Confirmations ==========
function initDeleteConfirmations() {
    document.querySelectorAll('.btn-delete').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this? This cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
}

// ========== Sortable Tables ==========
function initSortableTables() {
    document.querySelectorAll('table.sortable').forEach(function(table) {
        var headers = table.querySelectorAll('thead th');
        headers.forEach(function(th, index) {
            // Skip Actions columns
            if (th.textContent.trim() === 'Actions') return;

            // Add sort indicator
            var indicator = document.createElement('span');
            indicator.className = 'sort-indicator';
            indicator.textContent = ' \u25B4';
            th.appendChild(indicator);

            th.addEventListener('click', function() {
                sortTable(table, index, th);
            });
        });
    });
}

function sortTable(table, colIndex, clickedTh) {
    var tbody = table.querySelector('tbody');
    var rows = Array.from(tbody.querySelectorAll('tr'));
    var headers = table.querySelectorAll('thead th');

    // Determine sort direction
    var isAsc = clickedTh.getAttribute('data-sort') !== 'asc';
    headers.forEach(function(h) {
        h.removeAttribute('data-sort');
        h.classList.remove('sort-active');
    });
    clickedTh.setAttribute('data-sort', isAsc ? 'asc' : 'desc');
    clickedTh.classList.add('sort-active');

    // Update indicator
    var indicator = clickedTh.querySelector('.sort-indicator');
    if (indicator) {
        indicator.textContent = isAsc ? ' \u25B4' : ' \u25BE';
    }

    rows.sort(function(a, b) {
        var aText = a.cells[colIndex].textContent.trim();
        var bText = b.cells[colIndex].textContent.trim();

        // Try numeric (strip $ and commas)
        var aNum = parseFloat(aText.replace(/[$,]/g, ''));
        var bNum = parseFloat(bText.replace(/[$,]/g, ''));
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAsc ? aNum - bNum : bNum - aNum;
        }

        // Try date (YYYY-MM-DD)
        if (/^\d{4}-\d{2}-\d{2}$/.test(aText) && /^\d{4}-\d{2}-\d{2}$/.test(bText)) {
            return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
        }

        // Default string compare
        return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
    });

    rows.forEach(function(row) { tbody.appendChild(row); });
}

// ========== Target Date Toggle ==========
function initTargetDateToggle() {
    var typeSelect = document.getElementById('target-type');
    var dateGroup = document.getElementById('target-date-group');
    if (!typeSelect || !dateGroup) return;

    function toggleDate() {
        if (typeSelect.value === 'custom') {
            dateGroup.classList.remove('hidden');
        } else {
            dateGroup.classList.add('hidden');
        }
    }
    typeSelect.addEventListener('change', toggleDate);
    toggleDate();
}

// ========== Rule Form Toggles ==========
function initRuleFormToggles() {
    // Toggle action value inputs based on selected action type
    document.querySelectorAll('.rule-action-type').forEach(function(select) {
        select.addEventListener('change', function() {
            var form = this.closest('form');
            var catSelect = form.querySelector('.rule-value-category');
            var acctSelect = form.querySelector('.rule-value-account');
            var textInput = form.querySelector('.rule-value-text');

            if (catSelect) catSelect.style.display = (this.value === 'set_category') ? '' : 'none';
            if (acctSelect) acctSelect.style.display = (this.value === 'set_account') ? '' : 'none';
            if (textInput) textInput.style.display = (this.value === 'set_memo') ? '' : 'none';
        });
    });

    // Toggle "max amount" input for "between" match type
    document.querySelectorAll('.amount-match-type').forEach(function(select) {
        select.addEventListener('change', function() {
            var form = this.closest('form');
            var highInput = form.querySelector('.amount-high');
            if (highInput) {
                highInput.style.display = (this.value === 'between') ? '' : 'none';
            }
        });
    });
}

// ========== Settings Tabs ==========
function initSettingsTabs() {
    var tabs = document.querySelectorAll('.settings-tab');
    var panels = document.querySelectorAll('.settings-panel');
    if (!tabs.length) return;

    function activateTab(tabName) {
        tabs.forEach(function(t) {
            t.classList.toggle('active', t.getAttribute('data-tab') === tabName);
        });
        panels.forEach(function(p) {
            p.classList.toggle('active', p.getAttribute('data-tab') === tabName);
        });
    }

    // Handle tab clicks
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            var tabName = this.getAttribute('data-tab');
            activateTab(tabName);
            // Update URL without reload so refreshes stay on the same tab
            var url = new URL(window.location);
            url.searchParams.set('tab', tabName);
            history.replaceState(null, '', url);
        });
    });

    // Activate tab from URL param or default to first
    var params = new URLSearchParams(window.location.search);
    var activeTab = params.get('tab');
    if (activeTab && document.querySelector('.settings-panel[data-tab="' + activeTab + '"]')) {
        activateTab(activeTab);
    }
}

// ========== Init on DOM ready ==========
document.addEventListener('DOMContentLoaded', function() {
    updateToggleIcon();
    initDeleteConfirmations();
    initSortableTables();
    initTargetDateToggle();
    initRuleFormToggles();
    initSettingsTabs();

    var toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.addEventListener('click', toggleTheme);
    }
});
