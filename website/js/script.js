/**
 * ScholarBoard.ai — Interactive researcher visualization
 * D3.js v7 scatter plot with zoom/pan, search, and detail sidebar
 */

(function () {
    'use strict';

    // ── Constants ──────────────────────────────────────────────
    const SPECTRAL = [
        '#9e0142', '#d53e4f', '#f46d43', '#fdae61', '#fee08b',
        '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2',
        '#7b3294', '#ffffbf'
    ];
    const DOT_RADIUS = 5;
    const DOT_RADIUS_HOVER = 12;
    const PIC_RADIUS = 16;
    const NOISE_COLOR = '#888';

    // ── State ──────────────────────────────────────────────────
    let scholars = [];
    let scholarsById = {};
    let svg, g, xScale, yScale, zoom;
    let activeFilters = new Set();
    let selectedScholar = null;

    // ── Init ───────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', init);

    async function init() {
        try {
            scholars = await loadData();
            if (!scholars.length) {
                showError('No scholar data found');
                return;
            }
            scholarsById = Object.fromEntries(scholars.map(s => [s.id, s]));
            createMap(scholars);
            setupSearch(scholars);
            setupFilters(scholars);
            setupSidebar();
            createTooltip();
        } catch (err) {
            console.error('Init error:', err);
            showError('Failed to load scholar data: ' + err.message);
        }
    }

    // ── Data Loading ───────────────────────────────────────────
    async function loadData() {
        const resp = await fetch('data/scholars.json');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const raw = await resp.json();

        return Object.entries(raw)
            .map(([id, s]) => ({
                id: s.id || id,
                name: s.name || '',
                institution: s.institution || '',
                department: s.department || '',
                bio: s.bio || null,
                research_areas: s.research_areas || [],
                papers: s.papers || [],
                education: s.education || [],
                profile_pic: s.profile_pic || null,
                cluster: s.cluster != null ? s.cluster : -1,
                x: s.umap_projection ? s.umap_projection.x : null,
                y: s.umap_projection ? s.umap_projection.y : null,
            }))
            .filter(s => s.x != null && s.y != null && s.name);
    }

    // ── Map Creation ───────────────────────────────────────────
    function createMap(data) {
        const container = document.getElementById('scholar-map');
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Scales
        const xExtent = d3.extent(data, d => d.x);
        const yExtent = d3.extent(data, d => d.y);
        const pad = 60;

        xScale = d3.scaleLinear()
            .domain(xExtent)
            .range([pad, width - pad]);

        yScale = d3.scaleLinear()
            .domain(yExtent)
            .range([pad, height - pad]);

        // SVG
        svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Main group (zoom target)
        g = svg.append('g');

        // Zoom behavior
        zoom = d3.zoom()
            .scaleExtent([0.3, 20])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Cluster color function
        const clusterColor = (cluster) => {
            if (cluster < 0) return NOISE_COLOR;
            return SPECTRAL[cluster % SPECTRAL.length];
        };

        // Draw dots
        const dots = g.selectAll('.scholar-dot')
            .data(data)
            .join('circle')
            .attr('class', 'scholar-dot')
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y))
            .attr('r', DOT_RADIUS)
            .attr('fill', d => clusterColor(d.cluster))
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.2)
            .on('mouseenter', onDotEnter)
            .on('mouseleave', onDotLeave)
            .on('click', onDotClick);

        // Handle resize
        window.addEventListener('resize', () => {
            const w = container.clientWidth;
            const h = container.clientHeight;
            svg.attr('width', w).attr('height', h);
        });
    }

    // ── Dot Interactions ───────────────────────────────────────
    function onDotEnter(event, d) {
        d3.select(this)
            .transition().duration(150)
            .attr('r', DOT_RADIUS_HOVER)
            .attr('stroke-width', 2);

        showTooltip(event, d);

        // Bring to front
        this.parentNode.appendChild(this);
    }

    function onDotLeave(event, d) {
        const isSelected = selectedScholar && selectedScholar.id === d.id;
        d3.select(this)
            .transition().duration(150)
            .attr('r', isSelected ? DOT_RADIUS_HOVER : DOT_RADIUS)
            .attr('stroke-width', 1.2);

        hideTooltip();
    }

    function onDotClick(event, d) {
        event.stopPropagation();
        selectedScholar = d;
        showScholarDetails(d);

        // Highlight selected, reset others
        g.selectAll('.scholar-dot')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.2)
            .attr('r', DOT_RADIUS);

        d3.select(this)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2.5)
            .attr('r', DOT_RADIUS_HOVER);
    }

    // ── Tooltip ────────────────────────────────────────────────
    let tooltipEl;

    function createTooltip() {
        tooltipEl = document.createElement('div');
        tooltipEl.className = 'tooltip';
        tooltipEl.innerHTML = '<div class="tooltip-name"></div><div class="tooltip-institution"></div>';
        document.getElementById('map-container').appendChild(tooltipEl);
    }

    function showTooltip(event, d) {
        const mapRect = document.getElementById('map-container').getBoundingClientRect();
        tooltipEl.querySelector('.tooltip-name').textContent = d.name;
        tooltipEl.querySelector('.tooltip-institution').textContent = d.institution;
        tooltipEl.classList.add('visible');

        const x = event.clientX - mapRect.left + 12;
        const y = event.clientY - mapRect.top - 10;
        tooltipEl.style.left = x + 'px';
        tooltipEl.style.top = y + 'px';
    }

    function hideTooltip() {
        tooltipEl.classList.remove('visible');
    }

    // ── Scholar Details Sidebar ────────────────────────────────
    function showScholarDetails(scholar) {
        const sidebar = document.getElementById('sidebar');
        const details = document.getElementById('scholar-details');
        sidebar.classList.add('active');

        // Profile pic path
        const picSrc = scholar.profile_pic
            ? `data/profile_pics/${scholar.profile_pic}`
            : 'data/profile_pics/default_avatar.jpg';

        let html = '<div class="scholar-profile">';

        // Header: photo + name + institution
        html += `
            <div class="profile-header">
                <div class="profile-image">
                    <img src="${picSrc}" alt="${scholar.name}"
                         onerror="this.src='data/profile_pics/default_avatar.jpg'">
                </div>
                <div class="profile-info">
                    <h3>${scholar.name}</h3>
                    ${scholar.institution ? `<div class="institution">${scholar.institution}</div>` : ''}
                    ${scholar.department && scholar.department !== 'null' && scholar.department !== 'nan'
                        ? `<div class="department">${scholar.department}</div>` : ''}
                </div>
            </div>`;

        // Bio
        if (scholar.bio) {
            html += `<div class="profile-bio">${scholar.bio}</div>`;
        }

        // Research areas
        if (scholar.research_areas && scholar.research_areas.length) {
            html += '<div class="research-areas">';
            scholar.research_areas.forEach(area => {
                html += `<span class="research-tag">${area}</span>`;
            });
            html += '</div>';
        }

        // Papers
        if (scholar.papers && scholar.papers.length) {
            html += '<div class="papers-section"><h4>Recent Papers</h4>';
            scholar.papers.forEach(p => {
                const titleHtml = p.url
                    ? `<a href="${p.url}" target="_blank" rel="noopener">${p.title}</a>`
                    : p.title;
                html += `
                    <div class="paper-item">
                        <div class="paper-title">${titleHtml}</div>
                        <div class="paper-meta">
                            ${p.year ? `<span>${p.year}</span>` : ''}
                            ${p.venue ? `<span>${p.venue}</span>` : ''}
                            ${p.citations ? `<span>${p.citations} cit.</span>` : ''}
                        </div>
                    </div>`;
            });
            html += '</div>';
        }

        // Education
        if (scholar.education && scholar.education.length) {
            html += '<div class="education-section"><h4>Education</h4>';
            scholar.education.forEach(e => {
                html += `
                    <div class="education-item">
                        <div class="education-degree">${e.degree || 'Degree'}${e.field ? ' in ' + e.field : ''}</div>
                        <div class="education-details">
                            ${e.institution || ''}${e.year ? ' (' + e.year + ')' : ''}
                            ${e.advisor ? ' — Advisor: ' + e.advisor : ''}
                        </div>
                    </div>`;
            });
            html += '</div>';
        }

        // Nearby scholars
        const nearby = findNearbyScholars(scholar, 5);
        if (nearby.length) {
            html += '<div class="nearby-section"><h4>Similar Researchers</h4>';
            nearby.forEach(n => {
                const color = n.scholar.cluster >= 0
                    ? SPECTRAL[n.scholar.cluster % SPECTRAL.length]
                    : NOISE_COLOR;
                html += `
                    <div class="nearby-scholar" data-id="${n.scholar.id}">
                        <div class="dot" style="background:${color}"></div>
                        <div>
                            <div class="nearby-name">${n.scholar.name}</div>
                            <div class="nearby-institution">${n.scholar.institution}</div>
                        </div>
                    </div>`;
            });
            html += '</div>';
        }

        html += '</div>';
        details.innerHTML = html;

        // Click handlers for nearby scholars
        details.querySelectorAll('.nearby-scholar').forEach(el => {
            el.addEventListener('click', () => {
                const s = scholarsById[el.dataset.id];
                if (s) {
                    showScholarDetails(s);
                    panToScholar(s);
                }
            });
        });
    }

    function findNearbyScholars(scholar, count) {
        return scholars
            .filter(s => s.id !== scholar.id)
            .map(s => ({
                scholar: s,
                dist: Math.hypot(s.x - scholar.x, s.y - scholar.y)
            }))
            .sort((a, b) => a.dist - b.dist)
            .slice(0, count);
    }

    function panToScholar(scholar) {
        const container = document.getElementById('scholar-map');
        const w = container.clientWidth;
        const h = container.clientHeight;
        const sx = xScale(scholar.x);
        const sy = yScale(scholar.y);
        const scale = 3;

        svg.transition().duration(600).call(
            zoom.transform,
            d3.zoomIdentity
                .translate(w / 2, h / 2)
                .scale(scale)
                .translate(-sx, -sy)
        );

        // Highlight the dot
        selectedScholar = scholar;
        g.selectAll('.scholar-dot')
            .attr('stroke', '#fff')
            .attr('stroke-width', 1.2)
            .attr('r', DOT_RADIUS);

        g.selectAll('.scholar-dot')
            .filter(d => d.id === scholar.id)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2.5)
            .attr('r', DOT_RADIUS_HOVER)
            .each(function () { this.parentNode.appendChild(this); });
    }

    // ── Search ─────────────────────────────────────────────────
    function setupSearch(data) {
        const input = document.getElementById('search-input');
        const resultsEl = document.getElementById('search-results');

        input.addEventListener('input', () => {
            const query = input.value.trim().toLowerCase();
            if (query.length < 2) {
                resultsEl.classList.remove('active');
                return;
            }

            const matches = data
                .filter(s => s.name.toLowerCase().includes(query))
                .slice(0, 10);

            if (!matches.length) {
                resultsEl.innerHTML = '<div class="search-no-results">No scholars found</div>';
                resultsEl.classList.add('active');
                return;
            }

            resultsEl.innerHTML = matches.map(s => {
                const name = highlightMatch(s.name, query);
                const picSrc = s.profile_pic
                    ? `data/profile_pics/${s.profile_pic}`
                    : 'data/profile_pics/default_avatar.jpg';
                return `
                    <div class="search-result-item" data-id="${s.id}">
                        <div class="search-result-image">
                            <img src="${picSrc}" alt="${s.name}"
                                 onerror="this.src='data/profile_pics/default_avatar.jpg'">
                        </div>
                        <div>
                            <div class="search-result-name">${name}</div>
                            <div class="search-result-institution">${s.institution}</div>
                        </div>
                    </div>`;
            }).join('');

            resultsEl.classList.add('active');

            // Attach click handlers
            resultsEl.querySelectorAll('.search-result-item').forEach(el => {
                el.addEventListener('click', () => {
                    const s = scholarsById[el.dataset.id];
                    if (s) {
                        resultsEl.classList.remove('active');
                        input.value = s.name;
                        showScholarDetails(s);
                        panToScholar(s);
                    }
                });
            });
        });

        // Close results on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                resultsEl.classList.remove('active');
            }
        });
    }

    function highlightMatch(text, query) {
        const idx = text.toLowerCase().indexOf(query.toLowerCase());
        if (idx < 0) return text;
        const before = text.substring(0, idx);
        const match = text.substring(idx, idx + query.length);
        const after = text.substring(idx + query.length);
        return `${before}<span class="search-result-highlight">${match}</span>${after}`;
    }

    // ── Filters ────────────────────────────────────────────────
    function setupFilters(data) {
        const toggle = document.getElementById('filter-toggle');
        const dropdown = document.getElementById('filter-dropdown');
        const optionsEl = document.getElementById('filter-options');
        const applyBtn = document.getElementById('apply-filters');
        const clearBtn = document.getElementById('clear-filters');

        // Build institution counts
        const counts = new Map();
        data.forEach(s => {
            const inst = s.institution || 'Unknown';
            counts.set(inst, (counts.get(inst) || 0) + 1);
        });

        const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);

        optionsEl.innerHTML = sorted.map(([inst, count]) => `
            <div class="filter-option">
                <input type="checkbox" value="${inst}" id="f-${inst.replace(/\s+/g, '-')}">
                <label for="f-${inst.replace(/\s+/g, '-')}">${inst}</label>
                <span class="count">${count}</span>
            </div>
        `).join('');

        toggle.addEventListener('click', () => {
            dropdown.classList.toggle('active');
            toggle.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-container')) {
                dropdown.classList.remove('active');
                toggle.classList.remove('active');
            }
        });

        applyBtn.addEventListener('click', () => {
            activeFilters.clear();
            optionsEl.querySelectorAll('input:checked').forEach(cb => {
                activeFilters.add(cb.value);
            });
            applyFilterVisuals();
            dropdown.classList.remove('active');
            toggle.classList.remove('active');
        });

        clearBtn.addEventListener('click', () => {
            optionsEl.querySelectorAll('input').forEach(cb => cb.checked = false);
            activeFilters.clear();
            applyFilterVisuals();
        });
    }

    function applyFilterVisuals() {
        if (!activeFilters.size) {
            g.selectAll('.scholar-dot')
                .attr('opacity', 1)
                .style('pointer-events', 'auto');
            return;
        }

        g.selectAll('.scholar-dot')
            .attr('opacity', d => activeFilters.has(d.institution) ? 1 : 0.08)
            .style('pointer-events', d => activeFilters.has(d.institution) ? 'auto' : 'none');
    }

    // ── Sidebar ────────────────────────────────────────────────
    function setupSidebar() {
        document.getElementById('close-sidebar').addEventListener('click', () => {
            document.getElementById('sidebar').classList.remove('active');
            selectedScholar = null;

            // Reset dot highlights
            g.selectAll('.scholar-dot')
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.2)
                .attr('r', DOT_RADIUS);
        });
    }

    // ── Utilities ──────────────────────────────────────────────
    function showError(msg) {
        document.getElementById('scholar-map').innerHTML =
            `<div style="color:#c0392b;padding:40px;text-align:center;font-size:14px">${msg}</div>`;
    }

})();
