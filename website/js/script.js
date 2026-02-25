/**
 * ScholarBoard.ai — Interactive researcher visualization
 * D3.js v7 scatter plot with zoom/pan, search, and detail sidebar
 */

(function () {
    'use strict';

    // ── Constants ──────────────────────────────────────────────
    const SPECTRAL = [
        '#d1495b', '#ef8354', '#f4b860', '#c9c46b',
        '#7ac7a1', '#4fb3bf', '#4c8ed9', '#5f6ad4',
        '#7f5cc9', '#a855a1', '#c0567e', '#c17f59'
    ];
    const DOT_RADIUS = 4.4;
    const DOT_RADIUS_HOVER = 6.4;
    const DOT_RADIUS_SELECTED = 8.6;
    const NOISE_COLOR = '#8f99ab';
    const BASE_STROKE = 'rgba(255,255,255,0.78)';
    const SELECTED_STROKE = '#172235';
    const MAP_PAD = 72;

    // ── State ──────────────────────────────────────────────────
    let scholars = [];
    let scholarsById = {};
    let svg, g, xScale, yScale, zoom;
    let dots, selectionRing, brush, brushLayer;
    let activeFilters = new Set();
    let selectedScholar = null;
    let hoveredScholarId = null;
    let xDomain, yDomain;
    let resizeRaf = null;
    let currentTransform = d3.zoomIdentity;
    let boxZoomModifierActive = false;

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
            setupBoxZoomModifier();
            setupMapControls();
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
                main_research_area: s.main_research_area || null,
                lab_url: s.lab_url || null,
                papers: s.papers || [],
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
        xDomain = d3.extent(data, d => d.x);
        yDomain = d3.extent(data, d => d.y);

        xScale = d3.scaleLinear()
            .domain(xDomain);

        yScale = d3.scaleLinear()
            .domain(yDomain);
        updateScaleRanges(width, height);

        // SVG
        svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Cluster color function
        const clusterColor = (cluster) => {
            if (cluster < 0) return NOISE_COLOR;
            return SPECTRAL[cluster % SPECTRAL.length];
        };

        // Main group (zoom target)
        g = svg.append('g');
        const ringLayer = g.append('g').attr('class', 'selection-ring-layer');
        const dotLayer = g.append('g').attr('class', 'dots-layer');
        selectionRing = ringLayer.append('circle')
            .attr('class', 'selection-ring')
            .style('display', 'none');

        // Zoom behavior
        zoom = d3.zoom()
            .filter((event) => {
                if (event.type === 'wheel') return true;
                if (event.type === 'mousedown' || event.type === 'pointerdown') {
                    return (event.button ?? 0) === 0 && !boxZoomModifierActive;
                }
                return !boxZoomModifierActive;
            })
            .scaleExtent([0.3, 20])
            .on('zoom', (event) => {
                currentTransform = event.transform;
                g.attr('transform', event.transform);
            });

        svg.call(zoom);
        svg.on('dblclick.zoom', null);
        svg.on('dblclick', onMapDoubleClick);

        // Box zoom (Shift + drag)
        brushLayer = svg.append('g')
            .attr('class', 'brush-layer')
            .style('pointer-events', 'all');

        brush = d3.brush()
            .extent([[0, 0], [width, height]])
            .filter((event) =>
                (event.type === 'mousedown' || event.type === 'pointerdown') &&
                (event.button ?? 0) === 0 &&
                boxZoomModifierActive
            )
            .on('start', () => hideTooltip())
            .on('end', onBrushEnd);

        brushLayer.call(brush);

        // Draw dots
        dots = dotLayer.selectAll('.scholar-dot')
            .data(data)
            .join('circle')
            .attr('class', 'scholar-dot')
            .attr('cx', d => xScale(d.x))
            .attr('cy', d => yScale(d.y))
            .attr('r', DOT_RADIUS)
            .attr('fill', d => clusterColor(d.cluster))
            .attr('fill-opacity', d => d.cluster < 0 ? 0.6 : 0.97)
            .attr('stroke', BASE_STROKE)
            .attr('stroke-width', 1.1)
            .on('mouseenter', onDotEnter)
            .on('mousemove', onDotMove)
            .on('mouseleave', onDotLeave)
            .on('click', onDotClick);
        refreshDotStyles();

        // Handle resize
        window.addEventListener('resize', () => {
            if (resizeRaf) cancelAnimationFrame(resizeRaf);
            resizeRaf = requestAnimationFrame(() => {
                resizeRaf = null;
                const w = container.clientWidth;
                const h = container.clientHeight;
                svg.attr('width', w).attr('height', h);
                updateScaleRanges(w, h);
                if (brush && brushLayer) {
                    brush.extent([[0, 0], [w, h]]);
                    brushLayer.call(brush);
                    brushLayer.call(brush.move, null);
                }
                if (dots) {
                    dots
                        .attr('cx', d => xScale(d.x))
                        .attr('cy', d => yScale(d.y));
                }
                updateSelectionRing();
            });
        });
    }

    // ── Dot Interactions ───────────────────────────────────────
    function onDotEnter(event, d) {
        hoveredScholarId = d.id;
        refreshDotStyles();
        showTooltip(event, d);
        raiseDot(this);
    }

    function onDotMove(event) {
        positionTooltip(event);
    }

    function onDotLeave(event, d) {
        if (hoveredScholarId === d.id) hoveredScholarId = null;
        refreshDotStyles();
        hideTooltip();
    }

    function onDotClick(event, d) {
        event.stopPropagation();
        selectedScholar = d;
        hoveredScholarId = d.id;
        showScholarDetails(d);
        refreshDotStyles();
        raiseDot(this);
    }

    function onMapDoubleClick(event) {
        if (!svg || !zoom) return;
        hideTooltip();

        const [px, py] = d3.pointer(event, svg.node());
        const factor = event.shiftKey ? (1 / 1.8) : 1.8;
        zoomAtViewportPoint(px, py, factor, 190);
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
        tooltipEl.querySelector('.tooltip-name').textContent = d.name;
        tooltipEl.querySelector('.tooltip-institution').textContent = d.institution;
        tooltipEl.classList.add('visible');
        positionTooltip(event);
    }

    function hideTooltip() {
        tooltipEl.classList.remove('visible');
    }

    function positionTooltip(event) {
        if (!tooltipEl || !tooltipEl.classList.contains('visible')) return;

        const mapRect = document.getElementById('map-container').getBoundingClientRect();
        const tooltipRect = tooltipEl.getBoundingClientRect();
        let x = event.clientX - mapRect.left + 14;
        let y = event.clientY - mapRect.top - tooltipRect.height - 10;

        if (x + tooltipRect.width > mapRect.width - 8) {
            x = mapRect.width - tooltipRect.width - 8;
        }
        if (x < 8) x = 8;
        if (y < 8) y = event.clientY - mapRect.top + 14;

        tooltipEl.style.left = `${x}px`;
        tooltipEl.style.top = `${y}px`;
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
                    ${scholar.lab_url ? `<a class="lab-link" href="${scholar.lab_url}" target="_blank" rel="noopener">Lab Website</a>` : ''}
                </div>
            </div>`;

        // Bio
        if (scholar.bio) {
            html += `<div class="profile-bio">${scholar.bio}</div>`;
        }

        // Research area
        if (scholar.main_research_area) {
            html += `<div class="research-areas"><span class="research-tag">${scholar.main_research_area}</span></div>`;
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

        svg.transition().duration(260).call(
            zoom.transform,
            d3.zoomIdentity
                .translate(w / 2, h / 2)
                .scale(scale)
                .translate(-sx, -sy)
        );

        selectedScholar = scholar;
        hoveredScholarId = scholar.id;
        refreshDotStyles();
        g.selectAll('.scholar-dot')
            .filter(d => d.id === scholar.id)
            .each(function () { raiseDot(this); });
    }

    function setupMapControls() {
        const resetBtn = document.getElementById('reset-view');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => resetView());
        }
    }

    function resetView(duration = 220) {
        if (!svg || !zoom) return;
        hideTooltip();
        clearBrushSelection();
        svg.transition().duration(duration).call(zoom.transform, d3.zoomIdentity);
    }

    function zoomAtViewportPoint(px, py, factor, duration = 180) {
        if (!svg || !zoom) return;
        const current = currentTransform || d3.zoomIdentity;
        const targetK = Math.max(0.3, Math.min(20, current.k * factor));
        const localX = current.invertX(px);
        const localY = current.invertY(py);
        const target = d3.zoomIdentity
            .translate(px, py)
            .scale(targetK)
            .translate(-localX, -localY);

        svg.transition().duration(duration).call(zoom.transform, target);
    }

    // ── Search ─────────────────────────────────────────────────
    function setupSearch(data) {
        const input = document.getElementById('search-input');
        const resultsEl = document.getElementById('search-results');
        let currentMatches = [];
        let activeIndex = -1;

        function closeResults() {
            resultsEl.classList.remove('active');
            activeIndex = -1;
        }

        function selectScholarFromSearch(s) {
            if (!s) return;
            closeResults();
            input.value = s.name;
            showScholarDetails(s);
            panToScholar(s);
        }

        function renderResults(matches, query) {
            currentMatches = matches;
            activeIndex = matches.length ? 0 : -1;

            if (!matches.length) {
                resultsEl.innerHTML = '<div class="search-no-results">No scholars found</div>';
                resultsEl.classList.add('active');
                return;
            }

            resultsEl.innerHTML = matches.map((s, idx) => {
                const name = highlightMatch(s.name, query);
                const picSrc = s.profile_pic
                    ? `data/profile_pics/${s.profile_pic}`
                    : 'data/profile_pics/default_avatar.jpg';
                return `
                    <div class="search-result-item${idx === activeIndex ? ' active' : ''}" data-id="${s.id}">
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
            attachSearchResultHandlers();
        }

        function attachSearchResultHandlers() {
            resultsEl.querySelectorAll('.search-result-item').forEach((el, idx) => {
                el.addEventListener('mouseenter', () => {
                    activeIndex = idx;
                    updateActiveSearchResult();
                });
                el.addEventListener('click', () => {
                    selectScholarFromSearch(scholarsById[el.dataset.id]);
                });
            });
        }

        function updateActiveSearchResult() {
            const items = resultsEl.querySelectorAll('.search-result-item');
            items.forEach((el, idx) => el.classList.toggle('active', idx === activeIndex));
            const activeEl = items[activeIndex];
            if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
        }

        input.addEventListener('input', () => {
            const query = input.value.trim().toLowerCase();
            if (query.length < 2) {
                currentMatches = [];
                closeResults();
                return;
            }

            const matches = data
                .filter(s => s.name.toLowerCase().includes(query))
                .slice(0, 10);
            renderResults(matches, query);
        });

        input.addEventListener('keydown', (event) => {
            if (!resultsEl.classList.contains('active')) return;

            if (event.key === 'ArrowDown') {
                if (!currentMatches.length) return;
                event.preventDefault();
                activeIndex = (activeIndex + 1) % currentMatches.length;
                updateActiveSearchResult();
                return;
            }

            if (event.key === 'ArrowUp') {
                if (!currentMatches.length) return;
                event.preventDefault();
                activeIndex = activeIndex <= 0 ? currentMatches.length - 1 : activeIndex - 1;
                updateActiveSearchResult();
                return;
            }

            if (event.key === 'Enter') {
                if (!currentMatches.length) return;
                event.preventDefault();
                const idx = activeIndex >= 0 ? activeIndex : 0;
                selectScholarFromSearch(currentMatches[idx]);
                return;
            }

            if (event.key === 'Escape') {
                event.preventDefault();
                closeResults();
            }
        });

        // Close results on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                closeResults();
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
                .classed('is-dimmed', false)
                .attr('opacity', 1)
                .style('pointer-events', 'auto');
            return;
        }

        g.selectAll('.scholar-dot')
            .classed('is-dimmed', d => !activeFilters.has(d.institution))
            .attr('opacity', d => activeFilters.has(d.institution) ? 1 : 0.08)
            .style('pointer-events', d => activeFilters.has(d.institution) ? 'auto' : 'none');
    }

    // ── Sidebar ────────────────────────────────────────────────
    function setupSidebar() {
        document.getElementById('close-sidebar').addEventListener('click', () => {
            document.getElementById('sidebar').classList.remove('active');
            selectedScholar = null;
            hoveredScholarId = null;
            refreshDotStyles();
        });
    }

    function updateScaleRanges(width, height) {
        const pad = Math.max(42, Math.min(MAP_PAD, Math.min(width, height) * 0.12));
        xScale.range([pad, width - pad]);
        yScale.range([pad, height - pad]);
    }

    function setupBoxZoomModifier() {
        window.addEventListener('keydown', (event) => {
            if (event.key !== 'Shift') return;
            if (!boxZoomModifierActive) {
                boxZoomModifierActive = true;
                updateBoxZoomModifierUI();
            }
        });

        window.addEventListener('keyup', (event) => {
            if (event.key !== 'Shift') return;
            if (boxZoomModifierActive) {
                boxZoomModifierActive = false;
                clearBrushSelection();
                updateBoxZoomModifierUI();
            }
        });

        window.addEventListener('blur', () => {
            if (!boxZoomModifierActive) return;
            boxZoomModifierActive = false;
            clearBrushSelection();
            updateBoxZoomModifierUI();
        });

        updateBoxZoomModifierUI();
    }

    function updateBoxZoomModifierUI() {
        const map = document.getElementById('scholar-map');
        if (map) map.classList.toggle('box-zoom-mode', boxZoomModifierActive);
    }

    function clearBrushSelection() {
        if (brushLayer && brush) {
            brushLayer.call(brush.move, null);
        }
    }

    function onBrushEnd(event) {
        if (!event.selection || !svg || !zoom) return;

        const [[x0, y0], [x1, y1]] = event.selection;
        const width = Math.abs(x1 - x0);
        const height = Math.abs(y1 - y0);
        clearBrushSelection();

        if (width < 12 || height < 12) return;

        const minX = Math.min(x0, x1);
        const maxX = Math.max(x0, x1);
        const minY = Math.min(y0, y1);
        const maxY = Math.max(y0, y1);

        const lx0 = currentTransform.invertX(minX);
        const lx1 = currentTransform.invertX(maxX);
        const ly0 = currentTransform.invertY(minY);
        const ly1 = currentTransform.invertY(maxY);

        const localWidth = Math.max(1, Math.abs(lx1 - lx0));
        const localHeight = Math.max(1, Math.abs(ly1 - ly0));
        const cx = (lx0 + lx1) / 2;
        const cy = (ly0 + ly1) / 2;

        const container = document.getElementById('scholar-map');
        const viewW = container.clientWidth;
        const viewH = container.clientHeight;
        const targetScale = Math.max(0.3, Math.min(20, Math.min(viewW / localWidth, viewH / localHeight) * 0.94));

        const target = d3.zoomIdentity
            .translate(viewW / 2, viewH / 2)
            .scale(targetScale)
            .translate(-cx, -cy);

        svg.transition().duration(220).call(zoom.transform, target);
    }

    function refreshDotStyles() {
        if (!g) return;
        g.selectAll('.scholar-dot').each(function (d) {
            const isSelected = selectedScholar && selectedScholar.id === d.id;
            const isHovered = hoveredScholarId === d.id && !isSelected;
            const sel = d3.select(this);

            sel.classed('is-selected', isSelected)
                .classed('is-hovered', isHovered)
                .attr('r', isSelected ? DOT_RADIUS_SELECTED : (isHovered ? DOT_RADIUS_HOVER : DOT_RADIUS))
                .attr('stroke', isSelected ? SELECTED_STROKE : BASE_STROKE)
                .attr('stroke-width', isSelected ? 3.1 : (isHovered ? 1.9 : 0.95));
        });
        updateSelectionRing();
    }

    function updateSelectionRing() {
        if (!selectionRing) return;
        if (!selectedScholar) {
            selectionRing.style('display', 'none').classed('is-visible', false);
            return;
        }

        selectionRing
            .style('display', null)
            .classed('is-visible', true)
            .attr('cx', xScale(selectedScholar.x))
            .attr('cy', yScale(selectedScholar.y))
            .attr('r', DOT_RADIUS_SELECTED + 6.8);
    }

    function raiseDot(node) {
        if (node && node.parentNode) node.parentNode.appendChild(node);
    }

    // ── Utilities ──────────────────────────────────────────────
    function showError(msg) {
        document.getElementById('scholar-map').innerHTML =
            `<div style="color:#c0392b;padding:40px;text-align:center;font-size:14px">${msg}</div>`;
    }

})();
