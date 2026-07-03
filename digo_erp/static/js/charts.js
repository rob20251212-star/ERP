document.addEventListener("DOMContentLoaded", function () {
    const months = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ];

    // Chart Vendas
    const ctxVendas = document.getElementById("chartVendas");
    if (ctxVendas && typeof vendasMensais !== 'undefined') {
        new Chart(ctxVendas, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Faturamento (R$)',
                    data: vendasMensais,
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Chart Produção
    const ctxProducao = document.getElementById("chartProducao");
    if (ctxProducao && typeof producaoMensal !== 'undefined') {
        new Chart(ctxProducao, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Sacos Produzidos',
                    data: producaoMensal,
                    backgroundColor: 'rgba(6, 182, 212, 0.2)',
                    borderColor: 'rgba(6, 182, 212, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
});
