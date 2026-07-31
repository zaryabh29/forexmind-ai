let chartInstances = {};

function renderCandlestickChart(containerId, candleData) {
    if (chartInstances[containerId]) {
        chartInstances[containerId].destroy();
    }

    const seriesData = candleData.map(c => ({
        x: new Date(c.time),
        y: [c.open, c.high, c.low, c.close]
    }));

    const options = {
        series: [{
            name: 'Price',
            data: seriesData
        }],
        chart: {
            type: 'candlestick',
            height: 440,
            background: 'transparent',
            toolbar: { show: true },
            animations: { enabled: true }
        },
        theme: { mode: 'dark' },
        stroke: { width: 1 },
        xaxis: {
            type: 'datetime',
            labels: { style: { colors: '#8a99ad' } }
        },
        yaxis: {
            tooltip: { enabled: true },
            labels: {
                style: { colors: '#8a99ad' },
                formatter: (val) => val.toFixed(val < 10 ? 4 : 2)
            }
        },
        plotOptions: {
            candlestick: {
                colors: {
                    upward: '#00e676',
                    downward: '#ff1744'
                }
            }
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.05)'
        }
    };

    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = "";
        chartInstances[containerId] = new ApexCharts(container, options);
        chartInstances[containerId].render();
    }
}

function renderEquityChart(containerId, equityCurve) {
    if (chartInstances[containerId]) {
        chartInstances[containerId].destroy();
    }

    const seriesData = equityCurve.map((val, idx) => ({
        x: idx + 1,
        y: val
    }));

    const options = {
        series: [{
            name: 'Account Equity ($)',
            data: seriesData
        }],
        chart: {
            type: 'area',
            height: 380,
            background: 'transparent',
            toolbar: { show: true }
        },
        colors: ['#00f2fe'],
        stroke: { curve: 'smooth', width: 2 },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0.05,
                stops: [0, 90, 100]
            }
        },
        theme: { mode: 'dark' },
        xaxis: {
            labels: { style: { colors: '#8a99ad' } },
            title: { text: 'Trades Count', style: { color: '#8a99ad' } }
        },
        yaxis: {
            labels: {
                style: { colors: '#8a99ad' },
                formatter: (val) => '$' + val.toFixed(2)
            }
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.05)'
        }
    };

    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = "";
        chartInstances[containerId] = new ApexCharts(container, options);
        chartInstances[containerId].render();
    }
}

function renderWinLossChart(containerId, winCount, lossCount) {
    if (chartInstances[containerId]) {
        chartInstances[containerId].destroy();
    }

    const options = {
        series: [winCount, lossCount],
        labels: ['Winning Trades', 'Losing Trades'],
        chart: {
            type: 'donut',
            height: 260,
            background: 'transparent'
        },
        colors: ['#00e676', '#ff1744'],
        theme: { mode: 'dark' },
        legend: {
            position: 'bottom',
            labels: { colors: '#8a99ad' }
        },
        stroke: { width: 0 }
    };

    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = "";
        chartInstances[containerId] = new ApexCharts(container, options);
        chartInstances[containerId].render();
    }
}
