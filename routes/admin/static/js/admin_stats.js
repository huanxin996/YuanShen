document.addEventListener('DOMContentLoaded', function() {
    // 初始化运行时间自动更新
    initUptimeCounter();
    
    // 从JSON数据块中获取数据
    var chartDataElement = document.getElementById('chart-data');
    var chartData;
    
    try {
        chartData = JSON.parse(chartDataElement.textContent);
    } catch (error) {
        console.error('解析图表数据失败:', error);
        chartData = {
            apiNames: [],
            pieData: [],
            timeLabels: [],
            trendData: []
        };
    }
    
    // 提取数据
    var apiNames = chartData.apiNames || [];
    var pieData = chartData.pieData || [];
    var timeLabels = chartData.timeLabels || [];
    var trendData = chartData.trendData || [];
    
    // 初始化饼图
    var pieChartElement = document.getElementById('api-pie-chart');
    var pieChart;
    
    if (pieChartElement) {
        pieChart = echarts.init(pieChartElement);
        var pieOption = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c} ({d}%)'
            },
            legend: {
                type: 'scroll',
                orient: 'vertical',
                right: 10,
                top: 'center',
                data: apiNames
            },
            series: [
                {
                    name: 'API调用',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '18',
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: pieData
                }
            ]
        };
        pieChart.setOption(pieOption);
    }
    
    // 初始化趋势图
    var trendChartElement = document.getElementById('api-trend-chart');
    var trendChart;
    
    if (trendChartElement) {
        trendChart = echarts.init(trendChartElement);
        var trendOption = {
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['总调用量'],
                top: 'top'
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: timeLabels
            },
            yAxis: {
                type: 'value'
            },
            series: [
                {
                    name: '总调用量',
                    type: 'line',
                    stack: 'Total',
                    data: trendData,
                    areaStyle: {},
                    emphasis: {
                        focus: 'series'
                    }
                }
            ]
        };
        trendChart.setOption(trendOption);
    }
    
    // 当窗口调整大小时重新调整图表大小
    function resizeCharts() {
        if (pieChart) pieChart.resize();
        if (trendChart) trendChart.resize();
    }
    
    window.addEventListener('resize', resizeCharts);
});

// 运行时间自动更新功能
function initUptimeCounter() {
    const serverStartTimeElement = document.getElementById('server-start-time');
    const uptimeDisplay = document.getElementById('uptime-display');
    
    if (!serverStartTimeElement || !uptimeDisplay) return;
    
    // 获取服务器启动时间（作为Unix时间戳）
    let serverStartTime = parseInt(serverStartTimeElement.value, 10);
    
    if (!serverStartTime || isNaN(serverStartTime)) {
        console.error('无法获取有效的服务器启动时间');
        return;
    }
    
    // 更新运行时间的函数
    function updateUptime() {
        const currentTime = Math.floor(Date.now() / 1000);
        const uptimeSeconds = currentTime - serverStartTime;
        
        const days = Math.floor(uptimeSeconds / 86400);
        const hours = Math.floor((uptimeSeconds % 86400) / 3600);
        const minutes = Math.floor((uptimeSeconds % 3600) / 60);
        const seconds = Math.floor(uptimeSeconds % 60);
        
        let uptimeText = '';
        
        if (days > 0) {
            uptimeText = `${days}天${hours}小时`;
        } else if (hours > 0) {
            uptimeText = `${hours}小时${minutes}分`;
        } else if (minutes > 0) {
            uptimeText = `${minutes}分${seconds}秒`;
        } else {
            uptimeText = `${seconds}秒`;
        }
        
        uptimeDisplay.textContent = uptimeText;
    }
    
    // 立即执行一次，然后每秒更新
    updateUptime();
    setInterval(updateUptime, 1000);
}