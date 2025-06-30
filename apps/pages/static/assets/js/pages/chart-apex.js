'use strict';
document.addEventListener("DOMContentLoaded", function () {

    new Sortable(document.getElementById('sortable-card-container'), {
        animation: 150,
        ghostClass: 'bg-light',
        handle: '.card-header',
        scroll: true,               
        scrollSensitivity: 60,
        scrollSpeed: 10,  
        onEnd: function (evt) {
            const cards = Array.from(document.querySelectorAll('#sortable-card-container > div'));
            const payload = cards.map((el, index) => {
                return {
                    name: el.getAttribute('data-id'),
                    position: index + 1
                };
            });

            const csrfToken = '{{ csrf_token }}';
            fetch("{% url 'update-dashboard-component-position' %}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken, 
                },
                body: JSON.stringify(payload),
            })
            .then(response => {
                if (!response.ok) throw new Error("Failed to save order");
                return response.json();
            })
            .catch(err => {
            });
        }
    });


    // chart js 

    const chartCards = document.querySelectorAll(".chart-card");
    let delay = 0;

    chartCards.forEach((card) => {
        setTimeout(() => {
            const chartId = card.dataset.id;
            const ajaxUrl = card.dataset.url;
            const chartType = card.dataset.type;
            const chartTitle = card.dataset.title;
            const chartContainer = document.getElementById(chartId);

            const defaultFilterBtn = card.querySelector('.filter-btn');
            const allButtons = card.querySelectorAll('.filter-btn');
            allButtons.forEach(btn => {
                if (btn.getAttribute("data-filter") === "month"){
                    btn.classList.add('active');
                }
            });
            const filter = 'month';

            renderChart(chartId, ajaxUrl, chartType, chartTitle, chartContainer, filter);
        }, delay);

        delay += 500;
    });

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const filter = this.dataset.filter;
            const chartId = this.dataset.target;
            const card = document.querySelector(`.chart-card[data-id="${chartId}"]`);

            if (!card) return;

            const ajaxUrl = card.dataset.url;
            const chartType = card.dataset.type;
            const chartTitle = card.dataset.title;
            const chartContainer = document.getElementById(chartId);

            const allButtons = card.querySelectorAll('.filter-btn');

            allButtons.forEach(btn => btn.disabled = true);

            allButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            renderChart(chartId, ajaxUrl, chartType, chartTitle, chartContainer, filter, allButtons);
        });
    });

    function renderChart(chartId, ajaxUrl, chartType, chartTitle, chartContainer, filter, buttons = []) {
        // const loader = document.getElementById(`loader-${chartId}`);
        // if (loader) loader.style.display = "flex";
        // chartContainer.style.display = "none";

        fetch(`${window.location.origin}${ajaxUrl}/?filter=${filter}`)
            .then(res => res.json())
            .then(json => {
                const categories = json.map(entry => entry.label);
                const keys = Object.keys(json[0]).filter(key => key !== 'label');
                const totals = {};
                keys.forEach(key => {
                    totals[key] = json.reduce((sum, entry) => sum + (entry[key] || 0), 0);
                });
                const series = keys.map(key => ({
                    name: toTitleCase(key), 
                    data: json.map(entry => entry[key] || 0)
                }));

                const options = {
                    chart: {
                        type: chartType,
                        height: 500,
                        toolbar: {
                            show: true,
                            tools: {
                                download: true,
                                selection: false,
                                zoom: false,
                                zoomin: false,
                                zoomout: false,
                                pan: false,
                                reset: false,
                            },
                            autoSelected: "zoom"
                        },
                        animations: {
                            enabled: true,
                            easing: 'easeinout',
                            speed: 800,
                        },
                    },
                    stroke: { curve: "smooth" },
                    dataLabels: {
                        enabled: true,
                        style: {
                            fontSize: '12px',
                            fontWeight: 'bold',
                            colors: ['#000']
                        },
                        background: {
                            enabled: true,
                            borderRadius: 2,
                            padding: 4,
                            opacity: 0.7,
                        }
                    },
                    tooltip: {
                        enabled: true,
                        shared: true,
                        intersect: false,
                        custom: function({ series, dataPointIndex, w }) {
                            const label = w.globals.labels[dataPointIndex];
                            let total = 0;

                            const tooltipSeries = w.config.series.map((s, idx) => {
                                const value = s.data[dataPointIndex] || 0;
                                total += value;

                                return `
                                    <div class="apexcharts-tooltip-series-group apexcharts-tooltip-series-group-${idx} apexcharts-active" style="order: ${idx + 1}; display: flex;">
                                        <span class="apexcharts-tooltip-marker" style="color: ${w.config.colors[idx]};"></span>
                                        <div class="apexcharts-tooltip-text">
                                            <div class="apexcharts-tooltip-y-group">
                                                <span class="apexcharts-tooltip-text-y-label">${s.name}: </span>
                                                <span class="apexcharts-tooltip-text-y-value">${value}</span>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join("");

                            const totalRow = `
                                <div class="apexcharts-tooltip-series-group apexcharts-active" style="order: 999; display: flex; border-top: 1px solid #ddd; margin-top: 4px; padding-top: 4px;">
                                    <span class="apexcharts-tooltip-marker" style="color: #000;"></span>
                                    <div class="apexcharts-tooltip-text">
                                        <div class="apexcharts-tooltip-y-group">
                                            <span class="apexcharts-tooltip-text-y-label"><strong>Total:</strong> </span>
                                            <span class="apexcharts-tooltip-text-y-value"><strong>${total}</strong></span>
                                        </div>
                                    </div>
                                </div>
                            `;

                            return `
                                <div class="apexcharts-tooltip-title">${label}</div>
                                ${tooltipSeries}
                                ${totalRow}
                            `;
                        }
                    },
                    series: series,
                    xaxis: {categories: categories},
                    plotOptions: {
                        bar: {
                            horizontal: false,
                            columnWidth: '75%',
                            dataLabels: {
                                position: 'top'
                            }
                        }
                    },
                    colors: ['#00BFFF', '#FF8C00', '#FF0000'],
                    annotations: {
                        position: 'front',
                        texts: [
                            {
                                x: 10,
                                y: 10,
                                text: keys.map(key => `${toTitleCase(key)}: ${totals[key]}`).join(" | "),
                                textAnchor: 'start',
                                foreColor: '#6c757d',
                                fontSize: '14px',
                                fontWeight: 'bold',
                                backgroundColor: '#ffffff',
                                borderColor: '#dddddd',
                                borderRadius: 4,
                                borderWidth: 1,
                                padding: {
                                    left: 10,
                                    right: 10,
                                    top: 5,
                                    bottom: 5
                                }
                            }
                        ]
                    }
                    
                };

                if (chartContainer.chartInstance) {
                    chartContainer.chartInstance.destroy();
                }
                
                const chart = new ApexCharts(chartContainer, options);
                chart.render();
                
                chartContainer.chartInstance = chart;
                buttons.forEach(btn => btn.disabled = false);
            })
            .catch(error => {
                console.error(`Failed to load chart ${chartId}:`, error);
                buttons.forEach(btn => btn.disabled = false);
            })
    }

    const tableCards = document.querySelectorAll(".table-card");
    let tableDelay = 0;

    tableCards.forEach((card) => {
        setTimeout(() => {
            const tableId = card.dataset.id;
            const ajaxUrl = card.dataset.url;
            const title = card.dataset.title;
            const table = document.getElementById(tableId);
            const thead = table.querySelector("thead");
            const tbody = table.querySelector("tbody");

            const defaultFilterBtn = card.querySelector('.filter-btn');
            const filter = defaultFilterBtn ? defaultFilterBtn.dataset.filter : '';

            if (defaultFilterBtn) defaultFilterBtn.classList.add('active');

            renderTable(tableId, ajaxUrl, thead, tbody, filter);
        }, tableDelay);

        tableDelay += 500;
    });

    // Handle filter button clicks for tables
    document.querySelectorAll('.table-card .filter-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const filter = this.dataset.filter;
            const tableId = this.dataset.target;
            const card = document.querySelector(`.table-card[data-id="${tableId}"]`);

            if (!card) return;

            const table = document.getElementById(tableId);
            const thead = table.querySelector("thead");
            const tbody = table.querySelector("tbody");

            const allButtons = card.querySelectorAll('.filter-btn');
            allButtons.forEach(btn => {
                btn.disabled = true;
                btn.classList.remove('active');
            });
            this.classList.add('active');

            renderTable(tableId, card.dataset.url, thead, tbody, filter, allButtons);
        });
    });

    function renderTable(tableId, ajaxUrl, thead, tbody, filter, buttons = []) {
        const loader = document.getElementById(`loader-${tableId}`);
        const tableElement = document.getElementById(tableId);

        if (loader) loader.style.display = "flex";
        tableElement.closest('.table-responsive').style.display = "none";

        fetch(`${window.location.origin}${ajaxUrl}/?filter=${filter}`)
            .then(res => res.json())
            .then(json => {
                const records = json.data;

                // Clear table first
                thead.innerHTML = "";
                tbody.innerHTML = "";

                if (!records || !records.length) {
                    thead.innerHTML = "<tr><th>No Data Found</th></tr>";
                    return;
                }

                const headers = Object.keys(records[0]);

                thead.innerHTML = "<tr>" + headers.map(key => `<th>${toTitleCase(key.replace(/_/g, " "))}</th>`).join("") + "</tr>";

                tbody.innerHTML = records.map(row => {
                    return "<tr>" + headers.map(key => `<td>${row[key] !== null ? row[key] : ''}</td>`).join("") + "</tr>";
                }).join("");
            })
            .catch(error => {
                console.error(`Failed to load table ${tableId}:`, error);
                thead.innerHTML = "<tr><th class='text-danger text-center' colspan='1'>Failed to load data</th></tr>";
            })
            .finally(() => {
                if (loader) loader.style.display = "none";
                tableElement.closest('.table-responsive').style.display = "block";
                buttons.forEach(btn => btn.disabled = false);
            });
    }

    function isSeriesDataEmpty(series) {
        return series.every(serie => serie.data.every(val => val === 0 || val === null || val === undefined));
    }
    // Utility: Convert snake_case to Title Case
    function toTitleCase(str) {
        return str.replace(/\w\S*/g, function (txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }
});