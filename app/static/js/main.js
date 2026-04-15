// Fonctions utilitaires
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide des alertes après 5 secondes
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirmation pour les actions destructives
    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            var message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// Fonction de recherche autocomplete
function initAutocomplete(inputId, apiUrl, callback) {
    const input = document.getElementById(inputId);
    if (!input) return;

    let timeout;
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'autocomplete-results position-absolute w-100 bg-white border rounded-bottom shadow-sm';
    resultsContainer.style.zIndex = '1000';
    input.parentNode.style.position = 'relative';
    input.parentNode.appendChild(resultsContainer);

    input.addEventListener('input', function() {
        clearTimeout(timeout);
        const query = this.value.trim();

        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
            return;
        }

        timeout = setTimeout(function() {
            fetch(apiUrl + '?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = '';
                    if (data.length === 0) {
                        resultsContainer.style.display = 'none';
                        return;
                    }

                    data.forEach(function(item) {
                        const div = document.createElement('div');
                        div.className = 'autocomplete-item p-2 border-bottom cursor-pointer hover-bg-light';
                        div.innerHTML = `
                            <div class="fw-bold">${item.name || item.full_name}</div>
                            <small class="text-muted">${item.code} - ${item.phone || item.activity}</small>
                        `;
                        
                        div.addEventListener('click', function() {
                            input.value = item.code || item.name;
                            resultsContainer.style.display = 'none';
                            if (callback) callback(item);
                        });

                        resultsContainer.appendChild(div);
                    });

                    resultsContainer.style.display = 'block';
                })
                .catch(error => {
                    console.error('Erreur de recherche:', error);
                });
        }, 300);
    });

    // Cacher les résultats au clic ailleurs
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
            resultsContainer.style.display = 'none';
        }
    });
}

// Fonction de formatage des nombres
function formatNumber(num) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'XOF',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(num);
}

// Fonction de formatage des dates
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

// Fonction pour afficher les graphiques
function initCharts() {
    // Vérifier si Chart.js est disponible
    if (typeof Chart === 'undefined') return;

    // Graphique des prêts par mois
    const loansChartCtx = document.getElementById('loansChart');
    if (loansChartCtx) {
        fetch('/dashboard/charts')
            .then(response => response.json())
            .then(data => {
                new Chart(loansChartCtx, {
                    type: 'line',
                    data: {
                        labels: data.loans_by_month.map(item => item.month),
                        datasets: [{
                            label: 'Nombre de prêts',
                            data: data.loans_by_month.map(item => item.count),
                            borderColor: '#1E3A8A',
                            backgroundColor: 'rgba(30, 58, 138, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
                });
            });
    }

    // Graphique des paiements par mois
    const paymentsChartCtx = document.getElementById('paymentsChart');
    if (paymentsChartCtx) {
        fetch('/dashboard/charts')
            .then(response => response.json())
            .then(data => {
                new Chart(paymentsChartCtx, {
                    type: 'bar',
                    data: {
                        labels: data.payments_by_month.map(item => item.month),
                        datasets: [{
                            label: 'Montant des paiements',
                            data: data.payments_by_month.map(item => item.amount),
                            backgroundColor: '#16A34A'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return formatNumber(value);
                                    }
                                }
                            }
                        }
                    }
                });
            });
    }

    // Graphique des statuts de prêts
    const statusChartCtx = document.getElementById('statusChart');
    if (statusChartCtx) {
        fetch('/dashboard/charts')
            .then(response => response.json())
            .then(data => {
                new Chart(statusChartCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.loan_status.labels,
                        datasets: [{
                            data: data.loan_status.data,
                            backgroundColor: [
                                '#16A34A',  // Vert pour approuvé
                                '#F59E0B',  // Orange pour en attente
                                '#DC2626',  // Rouge pour rejeté
                                '#1E3A8A',  // Bleu pour complété
                                '#6B7280'   // Gris pour autres
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            });
    }
}

// Fonction pour rafraîchir les données du dashboard
function refreshDashboard() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Actualisation...';
        
        setTimeout(function() {
            location.reload();
        }, 1000);
    }
}

// Fonction pour imprimer un rapport
function printReport() {
    window.print();
}

// Fonction pour exporter en CSV
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(function(col) {
            // Nettoyer le texte et gérer les virgules
            let text = col.textContent.trim();
            if (text.includes(',')) {
                text = '"' + text.replace(/"/g, '""') + '"';
            }
            rowData.push(text);
        });
        
        csv.push(rowData.join(','));
    });

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename || 'export.csv');
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Validation des formulaires
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Fonction pour afficher une notification
function showNotification(message, type = 'info') {
    const container = document.querySelector('.container-fluid');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    container.insertBefore(alert, container.firstChild);

    // Auto-suppression après 5 secondes
    setTimeout(function() {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 5000);
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les graphiques
    initCharts();
    
    // Initialiser les autocompletes
    initAutocomplete('clientSearch', '/api/clients/search', function(item) {
        console.log('Client sélectionné:', item);
    });
    
    // Gestion des boutons d'actualisation
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }
    
    // Gestion des boutons d'impression
    const printBtn = document.getElementById('printBtn');
    if (printBtn) {
        printBtn.addEventListener('click', printReport);
    }
    
    // Gestion des boutons d'export
    const exportBtns = document.querySelectorAll('[data-export]');
    exportBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const tableId = this.getAttribute('data-export');
            const filename = this.getAttribute('data-filename') || 'export.csv';
            exportToCSV(tableId, filename);
        });
    });
});
