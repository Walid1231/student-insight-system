/* ============================================================
   Student Insight System — Dashboard Charts
   Modular Chart.js v4 configurations
   Reads live data from window.DASH (injected by Jinja template)
   ============================================================ */

(function () {
    'use strict';

    /* ── Theme-Aware Helpers ────────────────────────────────── */
    function isDark() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    }
    function gc() { return isDark() ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'; }
    function tc() { return isDark() ? '#9ca3af' : '#6b7280'; }
    function cardBg() { return isDark() ? '#1a1d27' : '#ffffff'; }

    /* ── Defensive Helpers ──────────────────────────────────── */
    function safeArr(v) { return (Array.isArray(v) && v.length) ? v : []; }
    function safeNum(v) { return (typeof v === 'number' && isFinite(v)) ? v : 0; }

    /* ── Color Palette ──────────────────────────────────────── */
    var C = {
        blue: '#3b82f6',
        blueFaded: 'rgba(59,130,246,0.12)',
        green: '#10b981',
        greenFaded: 'rgba(16,185,129,0.15)',
        purple: '#8b5cf6',
        purpleFaded: 'rgba(139,92,246,0.15)',
        amber: '#f59e0b',
        amberFaded: 'rgba(245,158,11,0.12)',
        red: '#ef4444'
    };

    var CAREER_COLORS = ['blue', 'green', 'purple', 'amber'];

    /* ── FIX 1: Global defaults moved here, called before every init ── */
    function _applyGlobalDefaults() {
        try {
            Chart.defaults.font.family = "'Inter', sans-serif";
            Chart.defaults.font.size = 12;
            Chart.defaults.color = tc();
            if (!Chart.defaults.plugins) Chart.defaults.plugins = {};
            if (!Chart.defaults.plugins.tooltip) Chart.defaults.plugins.tooltip = {};
            Chart.defaults.plugins.tooltip.backgroundColor = '#1f2937';
            Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 12 };
            Chart.defaults.plugins.tooltip.bodyFont = { size: 11 };
            Chart.defaults.plugins.tooltip.padding = 10;
            Chart.defaults.plugins.tooltip.cornerRadius = 8;
            Chart.defaults.plugins.tooltip.displayColors = true;
            Chart.defaults.plugins.tooltip.boxPadding = 4;
        } catch (e) {
            console.warn('[StudentAnalytics] Could not apply global defaults:', e);
        }
    }


    /* ──────────────────────────────────────────────────────────
                        CHART MODULES
       ────────────────────────────────────────────────────────── */

    /* 1 ▸ CGPA Trend — Line Chart ──────────────────────────── */
    function initCGPATrend(D) {
        var ctx = document.getElementById('cgpaTrendChart');
        var vals = safeArr(D.cgpa_values);
        if (!ctx || !vals.length) return null;

        var dataMax = Math.max.apply(null, vals);
        var dataMin = Math.min.apply(null, vals);
        var latest = vals[vals.length - 1];

        /* Y axis: zoom in on the data range for visual impact,
           but always show 0–4 scale with a sensible window        */
        var yMin = 0;
        var yMax = Math.max(4.0, Math.ceil(dataMax * 10) / 10);

        /* Custom plugin: draws gradient fill + dashed reference line.
           Works even when there is only ONE data point (built-in fill
           requires ≥ 2 points to produce an area).                  */
        var cgpaPlugin = {
            id: 'cgpaVisuals',
            afterDatasetsDraw: function (chart) {
                var meta = chart.getDatasetMeta(0);
                if (!meta || !meta.data || !meta.data.length) return;

                var c2d = chart.ctx;
                var ca = chart.chartArea;
                var pts = meta.data;
                var bottom = ca.bottom;

                c2d.save();
                c2d.beginPath();

                if (pts.length === 1) {
                    /* Single point: draw a horizontal fill from left to right */
                    c2d.moveTo(ca.left, pts[0].y);
                    c2d.lineTo(ca.right, pts[0].y);
                    c2d.lineTo(ca.right, bottom);
                    c2d.lineTo(ca.left, bottom);
                } else {
                    /* Multiple points: trace the dataset line path */
                    c2d.moveTo(pts[0].x, pts[0].y);
                    for (var i = 1; i < pts.length; i++) {
                        c2d.lineTo(pts[i].x, pts[i].y);
                    }
                    c2d.lineTo(pts[pts.length - 1].x, bottom);
                    c2d.lineTo(pts[0].x, bottom);
                }

                c2d.closePath();

                var grad = c2d.createLinearGradient(0, ca.top, 0, bottom);
                grad.addColorStop(0, 'rgba(59,130,246,0.66)');
                grad.addColorStop(0.65, 'rgba(59,130,246,0.21)');
                grad.addColorStop(1, 'rgba(59,130,246,0.0)');
                c2d.fillStyle = grad;
                c2d.fill();

                /* Dashed reference line at the latest value */
                var lastY = pts[pts.length - 1].y;
                c2d.beginPath();
                c2d.setLineDash([5, 5]);
                c2d.moveTo(ca.left, lastY);
                c2d.lineTo(ca.right, lastY);
                c2d.strokeStyle = isDark() ? 'rgba(59,130,246,0.4)' : 'rgba(59,130,246,0.3)';
                c2d.lineWidth = 1.5;
                c2d.stroke();
                c2d.setLineDash([]);

                c2d.restore();
            }
        };

        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: safeArr(D.cgpa_labels),
                datasets: [{
                    label: 'CGPA',
                    data: vals,
                    borderColor: C.blue,
                    backgroundColor: 'transparent',  // fill handled by plugin
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 9,
                    pointBackgroundColor: C.blue,
                    pointBorderColor: cardBg(),
                    pointBorderWidth: 2.5,
                    pointHoverBackgroundColor: '#ffffff',
                    pointHoverBorderColor: C.blue,
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 900, easing: 'easeOutQuart' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function (items) { return items[0].label; },
                            label: function (item) {
                                return '  CGPA: ' + Number(item.raw).toFixed(2);
                            },
                            afterLabel: function (item) {
                                var pct = Math.round((item.raw / 4.0) * 100);
                                return '  ' + pct + '% of 4.0 scale';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: yMin,
                        max: yMax,
                        grid: { color: gc() },
                        ticks: {
                            stepSize: 1.0,
                            color: tc(),
                            font: { size: 11 },
                            callback: function (v) { return v.toFixed(1); }
                        },
                        border: { dash: [4, 4], display: false }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: tc(),
                            font: { size: 11, weight: '600' }
                        },
                        border: { display: false }
                    }
                }
            },
            plugins: [cgpaPlugin]
        });
    }


    /* 2 ▸ Strengths vs Weakness — Radar Chart ──────────── */
    function initSkillRadar(D) {
        var ctx = document.getElementById('skillRadarChart');
        var rlbls = safeArr(D.radar_labels);
        if (!ctx || !rlbls.length) return null;

        /* Radar requires ≥ 3 axes to form a polygon. Pad if needed. */
        while (rlbls.length > 0 && rlbls.length < 3) {
            rlbls.push(' '.repeat(rlbls.length)); // unique spaces
            if (D.radar_scores) D.radar_scores.push(0);
        }

        /* Map 0 → 0.01 so zero axes don't collapse the polygon */
        var actual = safeArr(D.radar_scores).map(function (v) {
            return v === 0 ? 0.01 : v;
        });

        /* Benchmark polygon — fixed target so student can see the gap.
           Uses 75 on every axis as the "expected standard" reference.  */
        var benchmark = rlbls.map(function () { return 75; });

        /* Theme-aware palette matching the reference image */
        var teal = '#2ab7a9';
        var tealFill = 'rgba(42,183,169,0.30)';
        var pink = '#d1447e';
        var pinkFill = 'rgba(209,68,126,0.30)';

        return new Chart(ctx, {
            type: 'radar',
            data: {
                labels: rlbls,
                datasets: [
                    {
                        /* Outer teal ring — benchmark/target */
                        label: 'Target (75%)',
                        data: benchmark,
                        spanGaps: true,
                        backgroundColor: tealFill,
                        borderColor: teal,
                        borderWidth: 2.5,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    },
                    {
                        /* Inner pink polygon — student's actual scores */
                        label: 'Your Score',
                        data: actual,
                        spanGaps: true,
                        backgroundColor: pinkFill,
                        borderColor: pink,
                        borderWidth: 2.5,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        pointBackgroundColor: pink,
                        pointBorderColor: cardBg(),
                        pointBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 900, easing: 'easeOutQuart' },
                layout: {
                    padding: { left: 0, right: 0, top: 5, bottom: 5 }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: tc(),
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (item) {
                                return '  ' + item.dataset.label + ': ' + Number(item.raw).toFixed(0);
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 25,
                            display: false,
                            backdropColor: 'transparent'
                        },
                        grid: {
                            color: isDark()
                                ? 'rgba(255,255,255,0.12)'
                                : 'rgba(0,0,0,0.10)',
                            lineWidth: 1
                        },
                        angleLines: {
                            color: isDark()
                                ? 'rgba(255,255,255,0.12)'
                                : 'rgba(0,0,0,0.10)',
                            lineWidth: 1
                        },
                        pointLabels: {
                            color: tc(),
                            font: { size: 11, weight: '600' },
                            padding: 6
                        }
                    }
                }
            }
        });
    }



    /* 3 ▸ Core vs GED — Doughnut Chart ─────────────────────── */
    function initCoreGed(D) {
        var ctx = document.getElementById('coreGedChart');
        if (!ctx) return null;

        var core = safeNum(D.core_count);
        var ged = safeNum(D.ged_count);
        var elec = safeNum(D.elective_count);
        var total = core + ged + elec;
        if (!total) return null;

        var corePct = Math.round(core / total * 100);

        /* FIX 4: Use chart.chartArea for accurate center — accounts for legend height */
        var centerText = {
            id: 'doughnutCenterText',
            afterDraw: function (chart) {
                var _ctx = chart.ctx;
                var ca = chart.chartArea;
                var midX = (ca.left + ca.right) / 2;
                var midY = (ca.top + ca.bottom) / 2;
                _ctx.save();
                _ctx.font = '800 28px Inter, sans-serif';
                _ctx.fillStyle = isDark() ? '#e5e7eb' : '#111827';
                _ctx.textAlign = 'center';
                _ctx.textBaseline = 'middle';
                _ctx.fillText(corePct + '%', midX, midY);
                _ctx.font = '500 11px Inter, sans-serif';
                _ctx.fillStyle = isDark() ? '#9ca3af' : '#6b7280';
                _ctx.fillText('Core Credits', midX, midY + 20);
                _ctx.restore();
            }
        };

        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Core (Major)', 'GED (Gen Ed)', 'Elective'],
                datasets: [{
                    data: [core, ged, elec],
                    backgroundColor: [C.blue, C.green, C.amber],
                    borderWidth: 3,
                    borderColor: cardBg(),
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: tc(),
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (c) {
                                var pct = total > 0 ? Math.round(c.raw / total * 100) : 0;
                                return c.label + ': ' + c.raw + ' (' + pct + '%)';
                            }
                        }
                    }
                }
            },
            plugins: [centerText]
        });
    }


    /* 4 ▸ Weekly Study Hours — Bar Chart ────────────────────── */
    function initWeeklyHours(D) {
        var ctx = document.getElementById('weeklyHoursChart');
        if (!ctx) return null;
        var hours = safeArr(D.weekly_hours);
        if (!hours.length) return null;

        var maxH = Math.max.apply(null, hours) || 1;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: safeArr(D.weekly_labels),
                datasets: [{
                    label: 'Study Hours',
                    data: hours,
                    /* FIX 5: Non-peak bars use a higher opacity purple in dark mode */
                    backgroundColor: hours.map(function (h) {
                        return h >= maxH * 0.8
                            ? C.blue
                            : h > 0
                                ? (isDark() ? 'rgba(99,102,241,0.55)' : 'rgba(99,102,241,0.65)')
                                : (isDark() ? 'rgba(99,102,241,0.10)' : 'rgba(99,102,241,0.15)');
                    }),
                    borderRadius: 8,
                    maxBarThickness: 44,
                    hoverBackgroundColor: C.blue
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: gc() },
                        ticks: { color: tc(), font: { size: 11 }, callback: function (v) { return v + 'h'; } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: tc(), font: { size: 11, weight: '600' } }
                    }
                }
            }
        });
    }


    /* 5 ▸ Skill Effort Distribution — Grouped Bar ──────────── */
    function initSkillEffort(D) {
        var ctx = document.getElementById('skillEffortChart');
        if (!ctx || !safeArr(D.effort_labels).length) return null;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: D.effort_labels,
                datasets: [
                    {
                        label: 'Last 7 days',
                        data: safeArr(D.effort_week_b),
                        backgroundColor: C.blue,
                        borderRadius: 6,
                        maxBarThickness: 28
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: gc() },
                        ticks: { color: tc(), font: { size: 11 }, callback: function (v) { return v + 'h'; } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: tc(), font: { size: 11, weight: '500' } }
                    }
                }
            }
        });
    }


    /* Career bars implementation was moved to pure HTML/CSS in Jinja */

    /* 7 ▸ Burnout Risk Gauge — Canvas 2D Arc ───────────────── */
    function initBurnoutGauge(D) {
        var canvas = document.getElementById('burnoutGauge');
        if (!canvas) return;

        var pct = safeNum(D.burnout_pct);
        var dpr = window.devicePixelRatio || 1;
        var W = 260, H = 140;

        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';

        var c = canvas.getContext('2d');
        c.scale(dpr, dpr);

        var cx = W / 2;
        var cy = H - 10;
        var r = 100;
        var lineW = 20;
        var SA = Math.PI;
        var EA = 2 * Math.PI;

        // Background arc
        c.beginPath();
        c.arc(cx, cy, r, SA, EA, false);
        c.lineWidth = lineW + 4;
        c.strokeStyle = isDark() ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.04)';
        c.lineCap = 'round';
        c.stroke();

        // Colored segments
        var segments = [
            { start: 0, end: 0.33, color: '#10b981' },
            { start: 0.33, end: 0.66, color: '#f59e0b' },
            { start: 0.66, end: 1.0, color: '#ef4444' }
        ];

        segments.forEach(function (seg) {
            c.beginPath();
            c.arc(cx, cy, r, SA + Math.PI * seg.start, SA + Math.PI * seg.end, false);
            c.lineWidth = lineW;
            c.strokeStyle = seg.color;
            c.lineCap = 'butt';
            c.stroke();
        });

        // Needle
        var needleAngle = SA + Math.PI * (pct / 100);
        var needleLen = r * 0.88;                              // FIX 7: was 0.70 (stubby)

        c.save();
        c.translate(cx, cy);
        c.rotate(needleAngle);
        c.beginPath();
        c.moveTo(0, 0);
        c.lineTo(needleLen, 0);
        c.lineWidth = 3;
        c.strokeStyle = isDark() ? '#e5e7eb' : '#1f2937';
        c.lineCap = 'round';
        c.stroke();
        c.restore();

        // Center dot
        c.beginPath();
        c.arc(cx, cy, 6, 0, 2 * Math.PI);
        c.fillStyle = isDark() ? '#e5e7eb' : '#1f2937';
        c.fill();
        c.beginPath();
        c.arc(cx, cy, 3, 0, 2 * Math.PI);
        c.fillStyle = cardBg();
        c.fill();
    }


    /* 8 ▸ Goal Achievability — Bell Curve ───────────────── */
    function initGoalCurve(D) {
        var canvas = document.getElementById('goalCurveChart');
        if (!canvas) return null;

        var prob = (D.goal_prob !== null && D.goal_prob !== undefined) ? safeNum(D.goal_prob) : null;
        if (prob === null) return null;

        // Generate Bell Curve data (Normal Distribution)
        var dataPoints = [];
        var labels = [];
        var mean = 70; // Peak of the bell curve
        var stdDev = 15; // Spread

        for (var x = 0; x <= 100; x++) {
            var y = Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2));
            dataPoints.push(y);
            labels.push(x + '%');
        }

        // Custom plugin to draw the "You are here" marker line
        var probMarkerPlugin = {
            id: 'probMarker',
            afterDatasetsDraw: function (chart) {
                var c2d = chart.ctx;
                var ca = chart.chartArea;
                var meta = chart.getDatasetMeta(0);

                // Find X coordinate for the user's probability score
                var targetIdx = Math.max(0, Math.min(100, Math.round(prob)));
                var pt = meta.data[targetIdx];
                if (!pt) return;

                c2d.save();

                // Vertical dashed line
                c2d.beginPath();
                c2d.setLineDash([5, 5]);
                c2d.moveTo(pt.x, ca.top);
                c2d.lineTo(pt.x, ca.bottom);
                c2d.strokeStyle = isDark() ? '#34d399' : '#10b981'; // Emerald
                c2d.lineWidth = 2;
                c2d.stroke();

                // Marker Dot
                c2d.beginPath();
                c2d.arc(pt.x, pt.y, 6, 0, 2 * Math.PI);
                c2d.fillStyle = isDark() ? '#34d399' : '#10b981';
                c2d.fill();
                c2d.lineWidth = 3;
                c2d.strokeStyle = cardBg();
                c2d.stroke();

                // "You" Label
                c2d.fillStyle = isDark() ? '#f8fafc' : '#0f172a';
                c2d.font = "bold 12px 'Inter', sans-serif";
                c2d.textAlign = 'center';
                c2d.fillText('You', pt.x, pt.y - 12);

                c2d.restore();
            }
        };

        return new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Distribution',
                    data: dataPoints,
                    borderColor: isDark() ? '#818cf8' : '#6366f1', // Indigo
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    backgroundColor: isDark() ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)',
                    pointRadius: 0,
                    pointHoverRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                layout: { padding: { top: 20 } },
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    y: { display: false, min: 0 },
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: {
                            maxTicksLimit: 5,
                            color: tc(),
                            font: { size: 11, weight: '500' }
                        }
                    }
                }
            },
            plugins: [probMarkerPlugin]
        });
    }



    /* ── Chart instance registry — prevents memory leaks on SPA re-nav ── */
    window._studentChartInstances = window._studentChartInstances || {};

    function _destroyAllCharts() {
        Object.keys(window._studentChartInstances).forEach(function (key) {
            var inst = window._studentChartInstances[key];
            if (inst && typeof inst.destroy === 'function') inst.destroy();
            delete window._studentChartInstances[key];
        });
        // Also clear dynamically-generated career bars (deprecated code removed)
    }

    function _initAll() {
        var D = window.DASH;
        if (!D) {
            console.warn('[StudentAnalytics] No DASH data found on window — charts skipped.');
            return;
        }

        _applyGlobalDefaults();
        _destroyAllCharts();

        var inst = window._studentChartInstances;

        var safeCall = function (name, initFn) {
            try { return initFn(D); }
            catch (e) { console.error('[StudentAnalytics] Failed to initialize ' + name, e); return null; }
        };

        inst.cgpaTrend = safeCall('cgpaTrend', initCGPATrend);
        inst.skillRadar = safeCall('skillRadar', initSkillRadar);
        inst.coreGed = safeCall('coreGed', initCoreGed);
        inst.weeklyHours = safeCall('weeklyHours', initWeeklyHours);
        inst.skillEffort = safeCall('skillEffort', initSkillEffort);

        safeCall('burnoutGauge', initBurnoutGauge);
        inst.goalCurve = safeCall('goalCurve', initGoalCurve);
    }

    /* ── Expose globally so the SPA router can call it after content injection ── */
    window.initStudentDashboardCharts = _initAll;

    /* ── First-load: fires after deferred scripts execute, DASH already set ── */
    document.addEventListener('DOMContentLoaded', function () {
        if (window.DASH) _initAll();
    });

})();
