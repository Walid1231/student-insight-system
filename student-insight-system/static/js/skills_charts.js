
// skills_charts.js

// Initialize Radar Chart for Current Skills
function initSkillRadarChart(canvasId, skillsData) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const labels = skillsData.map(s => s.skill);
    const data = skillsData.map(s => s.current_score);

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Current Proficiency',
                data: data,
                fill: true,
                backgroundColor: 'rgba(255, 155, 124, 0.2)', // Coral
                borderColor: 'rgb(255, 155, 124)',
                pointBackgroundColor: 'rgb(255, 155, 124)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(255, 155, 124)'
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            elements: { line: { borderWidth: 3 } }
        }
    });
}

// Initialize Line Chart for Progress History
function initSkillHistoryChart(canvasId, skillHistory) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // We need to normalize data if multiple skills have different timelines
    // For simplicity, let's plot the first skill or aggregate
    // In production: Use distinct datasets

    const datasets = skillHistory.map(skill => {
        return {
            label: skill.skill,
            data: skill.history.map(h => ({ x: h.date, y: h.score })), // Time series data
            borderColor: getRandomColor(),
            tension: 0.1
        };
    });

    new Chart(ctx, {
        type: 'line',
        data: { datasets: datasets },
        options: {
            scales: {
                x: {
                    type: 'time', // Requires chartjs-adapter-date-fns
                    time: { unit: 'day' }
                },
                y: { beginAtZero: true, max: 100 }
            }
        }
    });
}

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Function to load charts dynamically
async function loadSkillVisualizations() {
    try {
        const response = await fetch('/api/skills/history');
        const data = await response.json();

        if (data.length > 0) {
            if (document.getElementById('skillRadarChart')) {
                initSkillRadarChart('skillRadarChart', data);
            }
            // if(document.getElementById('skillTrendChart')) {
            //     initSkillHistoryChart('skillTrendChart', data);
            // }
        }
    } catch (error) {
        console.error("Failed to load skill data", error);
    }
}

// Call on load
document.addEventListener('DOMContentLoaded', loadSkillVisualizations);
