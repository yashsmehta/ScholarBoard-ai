document.addEventListener('DOMContentLoaded', async () => {
    // Create header animation
    createHeaderAnimation();
    
    // Load scholar data
    try {
        console.log('Loading scholar data from data/scholars.json...');
        
        // Add a cache-busting parameter to the URL
        const timestamp = new Date().getTime();
        const url = `data/scholars.json?_=${timestamp}`;
        console.log('URL with cache-busting:', url);
        
        // Check if the file exists by making a HEAD request
        try {
            const headResponse = await fetch(url, { method: 'HEAD' });
            console.log('HEAD request status:', headResponse.status, headResponse.statusText);
        } catch (headError) {
            console.error('HEAD request failed:', headError);
        }
        
        const response = await fetch(url);
        console.log('Fetch response:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`Failed to load scholars.json: ${response.status} ${response.statusText}`);
        }
        
        const scholars = await response.json();
        console.log(`Loaded ${scholars.length} scholars`);
        
        if (scholars.length === 0) {
            console.error('No scholar data found');
            document.getElementById('scholar-map').innerHTML = '<div style="color: red; padding: 20px; text-align: center;">No scholar data found. Please check the console for errors.</div>';
            return;
        }
        
        // Log a sample scholar to debug
        console.log('Sample scholar data:', scholars[0]);
        
        // Check if all scholars have a country
        checkScholarCountries(scholars);
        
        // Check if scholars have the required properties
        const validScholars = scholars.filter(scholar => {
            // Check if scholar has at least one projection method
            const hasPCA = scholar.pca && Array.isArray(scholar.pca) && scholar.pca.length === 2;
            const hasTSNE = scholar.tsne && Array.isArray(scholar.tsne) && scholar.tsne.length === 2;
            const hasUMAP = scholar.umap && Array.isArray(scholar.umap) && scholar.umap.length === 2;
            
            if (!scholar.id || !scholar.name || (!hasPCA && !hasTSNE && !hasUMAP)) {
                console.warn('Invalid scholar data:', scholar);
                return false;
            }
            return true;
        });
        
        console.log(`Found ${validScholars.length} valid scholars out of ${scholars.length}`);
        
        if (validScholars.length === 0) {
            document.getElementById('scholar-map').innerHTML = '<div style="color: red; padding: 20px; text-align: center;">No valid scholar data found. Please check the console for details.</div>';
            return;
        }
        
        // Store the original scholars data with projections
        window.scholarsData = validScholars;
        
        // Set default projection method
        window.currentProjection = 'umap';
        
        // Create the scholar map
        createScholarMap(validScholars);
        
        // Set up sidebar functionality
        setupSidebar();
        
        // Set up projection buttons
        setupProjectionButtons();
        
        // Set up filter functionality
        setupFilters(validScholars);
        
        // Set up search functionality
        setupSearch(validScholars);
        
    } catch (error) {
        console.error('Error loading scholar data:', error);
        document.getElementById('scholar-map').innerHTML = '<div style="color: red; padding: 20px; text-align: center;">Error loading scholar data. Please check the console for details.</div>';
    }
});

function createHeaderAnimation() {
    const container = document.getElementById('header-animation');
    if (!container) return;
    
    // Clear any existing content
    container.innerHTML = '';
    
    // Create floating nodes
    const nodeCount = 25;
    const nodes = [];
    const headerWidth = container.offsetWidth;
    const headerHeight = container.offsetHeight;
    
    // Create nodes with random positions
    for (let i = 0; i < nodeCount; i++) {
        const node = document.createElement('div');
        node.className = 'node';
        
        // Random position
        const x = Math.random() * headerWidth;
        const y = Math.random() * headerHeight;
        
        // Random velocity for movement
        const vx = (Math.random() - 0.5) * 0.5;
        const vy = (Math.random() - 0.5) * 0.5;
        
        node.style.left = `${x}px`;
        node.style.top = `${y}px`;
        
        // Random size
        const size = 3 + Math.random() * 3;
        node.style.width = `${size}px`;
        node.style.height = `${size}px`;
        
        container.appendChild(node);
        nodes.push({ element: node, x, y, vx, vy, size });
    }
    
    // Function to update node positions and connections
    function updateNodes() {
        // Remove all existing connections
        const connections = container.querySelectorAll('.connection');
        connections.forEach(conn => conn.remove());
        
        // Update node positions
        for (let i = 0; i < nodes.length; i++) {
            const node = nodes[i];
            
            // Update position based on velocity
            node.x += node.vx;
            node.y += node.vy;
            
            // Bounce off edges
            if (node.x <= 0 || node.x >= headerWidth - node.size) {
                node.vx = -node.vx;
                node.x = Math.max(0, Math.min(headerWidth - node.size, node.x));
            }
            
            if (node.y <= 0 || node.y >= headerHeight - node.size) {
                node.vy = -node.vy;
                node.y = Math.max(0, Math.min(headerHeight - node.size, node.y));
            }
            
            // Apply small random changes to velocity for more natural movement
            node.vx += (Math.random() - 0.5) * 0.05;
            node.vy += (Math.random() - 0.5) * 0.05;
            
            // Limit velocity
            const maxSpeed = 0.8;
            const speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy);
            if (speed > maxSpeed) {
                node.vx = (node.vx / speed) * maxSpeed;
                node.vy = (node.vy / speed) * maxSpeed;
            }
            
            // Update DOM element position
            node.element.style.left = `${node.x}px`;
            node.element.style.top = `${node.y}px`;
        }
        
        // Create connections between nearby nodes
        const maxDistance = 80; // Maximum distance for connection
        
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const nodeA = nodes[i];
                const nodeB = nodes[j];
                
                // Calculate distance between nodes
                const dx = nodeB.x - nodeA.x;
                const dy = nodeB.y - nodeA.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // Only connect nodes that are close enough
                if (distance < maxDistance) {
                    const connection = document.createElement('div');
                    connection.className = 'connection';
                    
                    // Position and size the connection
                    connection.style.left = `${nodeA.x + nodeA.size / 2}px`;
                    connection.style.top = `${nodeA.y + nodeA.size / 2}px`;
                    connection.style.width = `${distance}px`;
                    
                    // Calculate the angle
                    const angle = Math.atan2(dy, dx) * (180 / Math.PI);
                    connection.style.transform = `rotate(${angle}deg)`;
                    
                    // Opacity based on distance - closer nodes have stronger connections
                    const opacity = 1 - (distance / maxDistance);
                    connection.style.opacity = opacity;
                    
                    container.appendChild(connection);
                }
            }
        }
        
        // Schedule next update
        requestAnimationFrame(updateNodes);
    }
    
    // Start the animation
    updateNodes();
    
    // Make sure the header content is visible
    const headerContent = document.querySelector('.header-content');
    if (headerContent) {
        headerContent.style.zIndex = '10';
        
        // Ensure the tagline is visible
        const tagline = headerContent.querySelector('p');
        if (tagline) {
            tagline.style.display = 'block';
            tagline.style.visibility = 'visible';
            tagline.style.opacity = '1';
        }
    }
}

function setupSidebar() {
    // No need for close button functionality as sidebar is always visible
    console.log('Setting up sidebar with always-visible layout');
}

function createScholarMap(scholars) {
    const mapContainer = document.getElementById('scholar-map');
    if (!mapContainer) return;
    
    // Clear any existing content
    mapContainer.innerHTML = '';
    
    // Get the current projection method
    const projectionMethod = window.currentProjection || 'umap';
    console.log(`Creating map with ${projectionMethod} projection`);
    
    // Create a color map for countries and count scholars per country
    const countries = [...new Set(scholars.map(s => s.country).filter(Boolean))];
    const colorMap = {};
    const countryCount = {};
    const colors = [
        '#4285F4', '#EA4335', '#FBBC05', '#34A853', // Google colors
        '#8AB4F8', '#F28B82', '#FDD663', '#81C995', // Lighter versions
        '#1967D2', '#D93025', '#F9AB00', '#1E8E3E', // Darker versions
        '#D2E3FC', '#FADBD8', '#FCE8B2', '#CEEAD6', // Even lighter versions
        '#174EA6', '#A50E0E', '#E37400', '#0D652D'  // Even darker versions
    ];
    
    // Count scholars per country
    scholars.forEach(scholar => {
        if (scholar.country) {
            countryCount[scholar.country] = (countryCount[scholar.country] || 0) + 1;
        }
    });
    
    // Sort countries by count (descending)
    const sortedCountries = countries.sort((a, b) => countryCount[b] - countryCount[a]);
    
    // Assign colors to countries
    sortedCountries.forEach((country, i) => {
        colorMap[country] = colors[i % colors.length];
    });
    
    // Create a legend for top countries
    createCountryLegend(colorMap, countryCount, scholars.length);
    
    // Calculate the min and max coordinates to normalize
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    
    // First pass: find min/max coordinates
    scholars.forEach(scholar => {
        // Get coordinates based on the current projection method
        const coords = scholar[projectionMethod];
        if (!coords || !Array.isArray(coords) || coords.length !== 2) {
            console.warn(`Scholar ${scholar.name} (${scholar.id}) has invalid ${projectionMethod} coordinates:`, coords);
            return;
        }
        
        const x = coords[0];
        const y = coords[1];
        
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
    });
    
    console.log(`Coordinate ranges for ${projectionMethod}: X(${minX} to ${maxX}), Y(${minY} to ${maxY})`);
    
    // Add some padding
    const padding = 0.1;
    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;
    
    minX -= rangeX * padding;
    maxX += rangeX * padding;
    minY -= rangeY * padding;
    maxY += rangeY * padding;
    
    // Create a container for the dots
    const dotsContainer = document.createElement('div');
    dotsContainer.className = 'dots-container';
    dotsContainer.style.position = 'relative';
    dotsContainer.style.width = '100%';
    dotsContainer.style.height = '100%';
    dotsContainer.style.overflow = 'hidden';
    
    // Store current scale for label visibility
    window.currentScale = 1;
    
    // Second pass: create nodes
    let nodesCreated = 0;
    scholars.forEach(scholar => {
        // Get coordinates based on the current projection method
        const coords = scholar[projectionMethod];
        if (!coords || !Array.isArray(coords) || coords.length !== 2) {
            return; // Skip scholars with invalid coordinates
        }
        
        const x = coords[0];
        const y = coords[1];
        
        // Normalize coordinates to fit in the container (0-100%)
        const normalizedX = ((x - minX) / (maxX - minX)) * 100;
        const normalizedY = ((y - minY) / (maxY - minY)) * 100;
        
        // Create a dot for the scholar
        const dot = document.createElement('div');
        dot.className = 'scholar-dot';
        dot.setAttribute('data-id', scholar.id);
        dot.setAttribute('data-name', scholar.name);
        
        // Position the dot
        dot.style.position = 'absolute';
        dot.style.left = `${normalizedX}%`;
        dot.style.top = `${normalizedY}%`;
        dot.style.width = '16px';
        dot.style.height = '16px';
        dot.style.borderRadius = '50%';
        dot.style.backgroundColor = colorMap[scholar.country] || '#999';
        dot.style.border = '2px solid white';
        dot.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
        dot.style.transform = 'translate(-50%, -50%)';
        dot.style.cursor = 'pointer';
        dot.style.transition = 'all 0.2s ease';
        
        // Create tooltip that follows mouse
        const tooltip = document.createElement('div');
        tooltip.className = 'scholar-tooltip';
        tooltip.textContent = scholar.name;
        tooltip.style.display = 'none';
        document.body.appendChild(tooltip);
        
        // Create label for scholar name (visible when zoomed in)
        const label = document.createElement('div');
        label.className = 'scholar-label';
        label.textContent = scholar.name;
        label.style.position = 'absolute';
        label.style.left = `${normalizedX}%`;
        label.style.top = `${normalizedY + 2}%`;
        label.style.transform = 'translate(-50%, 0)';
        label.style.fontSize = '10px';
        label.style.color = '#333';
        label.style.textAlign = 'center';
        label.style.whiteSpace = 'nowrap';
        label.style.pointerEvents = 'none';
        label.style.opacity = '0';
        label.style.transition = 'opacity 0.3s ease';
        
        // Show tooltip on hover
        dot.addEventListener('mouseenter', (e) => {
            tooltip.style.display = 'block';
            updateTooltipPosition(e);
            dot.style.transform = 'translate(-50%, -50%) scale(1.2)';
            dot.style.zIndex = '10';
        });
        
        dot.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
            dot.style.transform = 'translate(-50%, -50%) scale(1)';
            dot.style.zIndex = '1';
        });
        
        dot.addEventListener('mousemove', updateTooltipPosition);
        
        function updateTooltipPosition(e) {
            const x = e.clientX;
            const y = e.clientY;
            tooltip.style.left = `${x}px`;
            tooltip.style.top = `${y}px`;
        }
        
        // Add click event to show scholar details
        dot.addEventListener('click', () => {
            // Remove highlight from all dots
            document.querySelectorAll('.scholar-dot').forEach(d => {
                d.classList.remove('highlighted');
            });
            
            // Add highlight to this dot
            dot.classList.add('highlighted');
            
            // Show scholar details
            showScholarDetails(scholar);
        });
        
        // Add the dot and label to the container
        dotsContainer.appendChild(dot);
        dotsContainer.appendChild(label);
        nodesCreated++;
    });
    
    console.log(`Created ${nodesCreated} scholar nodes`);
    
    // Add the dots container to the map
    mapContainer.appendChild(dotsContainer);
    
    // Set up zoom and pan functionality
    let isDragging = false;
    let startX, startY;
    let translateX = 0, translateY = 0;
    let scale = 1;
    
    // Function to apply transform
    function applyTransform() {
        dotsContainer.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
        
        // Update current scale for label visibility
        window.currentScale = scale;
        
        // Show/hide labels based on zoom level
        updateLabelVisibility();
    }
    
    // Function to update label visibility based on zoom level
    function updateLabelVisibility() {
        const labels = document.querySelectorAll('.scholar-label');
        
        if (scale >= 3.5) {
            // When zoomed in significantly, use a grid-based approach to prevent overcrowding
            const gridSize = 40; // pixels
            const visibleLabels = new Set();
            const occupiedCells = new Map();
            
            // First pass: assign each label to a grid cell
            labels.forEach((label, index) => {
                // Get label position
                const rect = label.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                // Calculate grid cell
                const cellX = Math.floor(centerX / gridSize);
                const cellY = Math.floor(centerY / gridSize);
                const cellKey = `${cellX},${cellY}`;
                
                // If cell is already occupied, compare with existing label
                if (occupiedCells.has(cellKey)) {
                    const existingIndex = occupiedCells.get(cellKey);
                    // Randomly choose which label to display in case of conflict
                    // This ensures different labels get a chance to be displayed
                    if (Math.random() > 0.5) {
                        occupiedCells.set(cellKey, index);
                        visibleLabels.delete(existingIndex);
                        visibleLabels.add(index);
                    }
                } else {
                    // Cell is free, occupy it
                    occupiedCells.set(cellKey, index);
                    visibleLabels.add(index);
                }
            });
            
            // Apply visibility
            labels.forEach((label, index) => {
                label.style.opacity = visibleLabels.has(index) ? '1' : '0';
            });
        } else if (scale >= 2.5) {
            // Show a very limited number of labels when moderately zoomed in
            const totalLabels = labels.length;
            const visibleLabels = Math.floor(totalLabels * 0.05); // Show only 5% of labels
            
            // Create an array of indices and shuffle it
            const indices = Array.from({ length: totalLabels }, (_, i) => i);
            shuffleArray(indices);
            
            // Show only a subset of labels
            labels.forEach((label, i) => {
                label.style.opacity = indices.indexOf(i) < visibleLabels ? '1' : '0';
            });
        } else {
            // Hide all labels when zoomed out
            labels.forEach(label => {
                label.style.opacity = '0';
            });
        }
    }
    
    // Function to shuffle array (Fisher-Yates algorithm)
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }
    
    // Mouse events for panning
    dotsContainer.addEventListener('mousedown', (e) => {
        isDragging = true;
        startX = e.clientX - translateX;
        startY = e.clientY - translateY;
        dotsContainer.style.cursor = 'grabbing';
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        applyTransform();
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
        dotsContainer.style.cursor = 'grab';
    });
    
    // Zoom controls
    const zoomIn = document.getElementById('zoom-in');
    const zoomOut = document.getElementById('zoom-out');
    const resetView = document.getElementById('reset-view');
    
    if (zoomIn) {
        zoomIn.addEventListener('click', () => {
            scale = Math.min(scale * 1.5, 5); // Max zoom: 5x
            applyTransform();
        });
    }
    
    if (zoomOut) {
        zoomOut.addEventListener('click', () => {
            scale = Math.max(scale / 1.5, 0.5); // Min zoom: 0.5x
            applyTransform();
        });
    }
    
    if (resetView) {
        resetView.addEventListener('click', () => {
            translateX = 0;
            translateY = 0;
            scale = 1;
            applyTransform();
        });
    }
    
    // Mouse wheel zoom
    mapContainer.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        // Get mouse position relative to container
        const rect = mapContainer.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Calculate position in the transformed space
        const x = (mouseX - translateX) / scale;
        const y = (mouseY - translateY) / scale;
        
        // Adjust scale based on wheel direction
        const delta = -Math.sign(e.deltaY) * 0.1;
        const newScale = Math.max(0.5, Math.min(5, scale * (1 + delta)));
        
        // Adjust translation to zoom toward mouse position
        translateX = mouseX - x * newScale;
        translateY = mouseY - y * newScale;
        
        scale = newScale;
        applyTransform();
    });
    
    // Initial transform
    applyTransform();
}

function createCountryLegend(colorMap, countryCount, totalScholars) {
    // Remove existing legend if any
    const existingLegend = document.querySelector('.country-legend');
    if (existingLegend) {
        existingLegend.remove();
    }
    
    // Create a legend container
    const legendContainer = document.createElement('div');
    legendContainer.className = 'country-legend';
    legendContainer.innerHTML = '<h3>Top Countries</h3>';
    
    // Get top 4 countries by count
    const countries = Object.keys(countryCount).sort((a, b) => countryCount[b] - countryCount[a]);
    const topCountries = countries.slice(0, 4);
    
    topCountries.forEach(country => {
        const color = colorMap[country];
        const count = countryCount[country];
        const percentage = ((count / totalScholars) * 100).toFixed(1);
        
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        
        const colorSwatch = document.createElement('span');
        colorSwatch.className = 'color-swatch';
        colorSwatch.style.backgroundColor = color;
        
        const countryName = document.createElement('span');
        countryName.className = 'country-name';
        countryName.textContent = country;
        
        const countryPercentage = document.createElement('span');
        countryPercentage.className = 'country-percentage';
        countryPercentage.textContent = `(${percentage}%)`;
        
        legendItem.appendChild(colorSwatch);
        legendItem.appendChild(countryName);
        legendItem.appendChild(countryPercentage);
        legendContainer.appendChild(legendItem);
    });
    
    // Add the legend to the page
    const mapContainer = document.getElementById('map-container');
    if (mapContainer) {
        mapContainer.appendChild(legendContainer);
    }
}

function showScholarDetails(scholar) {
    const sidebar = document.getElementById('sidebar');
    const detailsContainer = document.getElementById('scholar-details');
    
    if (!sidebar || !detailsContainer) return;
    
    // Show loading state
    detailsContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading scholar profile...</div>';
    
    console.log(`Loading profile for scholar ${scholar.id}: ${scholar.name}`);
    
    // Create a basic profile with the data we already have
    const basicProfileHtml = `
        <div class="scholar-profile">
            <div class="profile-header">
                <div class="profile-image">
                    <img src="images/${scholar.profile_pic || 'placeholder.jpg'}" alt="${scholar.name}" onerror="this.src='images/placeholder.jpg'">
                </div>
                <div class="profile-info">
                    <h3>${scholar.name}</h3>
                    ${scholar.institution ? `<p class="institution">${scholar.institution}</p>` : ''}
                    ${scholar.country ? `<p class="country"><i class="fas fa-globe-americas"></i> ${scholar.country}</p>` : ''}
                </div>
            </div>
            <div class="profile-content">
                <p class="loading-text">Loading additional information...</p>
            </div>
        </div>
    `;
    
    // Update with basic profile immediately
    detailsContainer.innerHTML = basicProfileHtml;
    
    // Fetch additional scholar details if needed
    fetch(`/api/scholar/${scholar.id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load scholar profile: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received scholar profile data:', data);
            
            // Only update the profile content with the additional information
            const profileContent = detailsContainer.querySelector('.profile-content');
            if (profileContent) {
                if (data.markdown_content) {
                    profileContent.innerHTML = `
                        <div class="research-info">
                            <div class="research-text markdown-content">
                                ${formatMarkdown(data.markdown_content)}
                            </div>
                        </div>
                    `;
                } else if (data.raw_text) {
                    profileContent.innerHTML = `
                        <div class="research-info">
                            <h4>Research Information</h4>
                            <div class="research-text">
                                ${formatResearchText(data.raw_text)}
                            </div>
                        </div>
                    `;
                } else {
                    profileContent.innerHTML = '<p class="no-info">No detailed information available for this scholar.</p>';
                }
            }
        })
        .catch(error => {
            console.error('Error loading scholar profile:', error);
            
            // Only update the profile content with the error
            const profileContent = detailsContainer.querySelector('.profile-content');
            if (profileContent) {
                profileContent.innerHTML = `
                    <div class="error">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Error loading additional information</p>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        });
}

function formatMarkdown(markdown) {
    if (!markdown) return '';
    
    // Split the markdown into sections by headings
    const sections = [];
    let currentSection = { heading: null, content: [] };
    
    // Process the markdown line by line
    const lines = markdown.split('\n');
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check if this is a heading
        if (line.startsWith('## ')) {
            // If we already have a section, save it
            if (currentSection.heading) {
                sections.push(currentSection);
            }
            
            // Start a new section
            currentSection = { 
                heading: line.substring(3), 
                content: []
            };
        } else if (line.trim() !== '') {
            // Add non-empty lines to the current section content
            currentSection.content.push(line);
        }
    }
    
    // Add the last section
    if (currentSection.heading) {
        sections.push(currentSection);
    }
    
    // Generate HTML for each section
    let html = '<div class="markdown-sections">';
    
    sections.forEach((section, index) => {
        const sectionId = `section-${index}`;
        const headingHtml = formatSectionHeading(section.heading);
        const contentHtml = formatSectionContent(section.content);
        
        // Only expand the first section by default
        const isExpanded = index === 0;
        const iconClass = isExpanded ? 'fa-chevron-up' : 'fa-chevron-down';
        const expandedClass = isExpanded ? 'expanded' : '';
        
        html += `
            <div class="markdown-section">
                <div class="section-header" data-target="${sectionId}">
                    ${headingHtml}
                    <span class="toggle-icon"><i class="fas ${iconClass}"></i></span>
                </div>
                <div class="section-content ${expandedClass}" id="${sectionId}">
                    ${contentHtml}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Add event listeners for toggling sections after the content is added to the DOM
    setTimeout(() => {
        const sectionHeaders = document.querySelectorAll('.section-header');
        sectionHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const targetId = header.getAttribute('data-target');
                const content = document.getElementById(targetId);
                const icon = header.querySelector('.toggle-icon i');
                
                // Toggle the content visibility
                if (content.classList.contains('expanded')) {
                    content.classList.remove('expanded');
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                } else {
                    content.classList.add('expanded');
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                }
            });
        });
    }, 100);
    
    return html;
}

function formatSectionHeading(heading) {
    // Extract emoji if present
    const emojiMatch = heading.match(/^([\u{1F300}-\u{1F6FF}\u{2600}-\u{26FF}])\s+(.*?)$/u);
    if (emojiMatch) {
        const emoji = emojiMatch[1];
        const text = emojiMatch[2];
        return `<h4><span class="section-emoji">${emoji}</span> ${text}</h4>`;
    }
    return `<h4>${heading}</h4>`;
}

function formatSectionContent(contentLines) {
    // Join the content lines back into a single string
    let content = contentLines.join('\n');
    
    // First, normalize bullet points to ensure consistent format
    // Replace any instances where there might be extra spaces after the asterisk
    content = content.replace(/^\*\s+/gm, '* ');
    
    // Process bold text first
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle italic text, but be careful not to affect bullet points
    content = content.replace(/(?<!\*)\*([^\*\n]+)\*/g, '<em>$1</em>');
    
    // Check if content contains bullet points
    if (content.includes('\n* ') || content.startsWith('* ')) {
        // Split by bullet points
        const parts = content.split('\n* ');
        
        // The first part might be an introductory paragraph
        let html = '';
        let startIndex = 0;
        
        if (!content.startsWith('* ')) {
            // There's an intro paragraph - clean up any standalone asterisks
            const introPara = parts[0].replace(/(?<!\*)\*(?!\*)/g, '').trim();
            html += `<p>${introPara}</p>`;
            startIndex = 1;
        }
        
        // Add the bullet points as a list
        if (parts.length > startIndex) {
            html += '<ul>';
            for (let i = startIndex; i < parts.length; i++) {
                if (parts[i].trim()) {
                    // Clean up any remaining asterisks that might be part of the content
                    let bulletContent = parts[i];
                    
                    // Remove any leading asterisk with space that might have been missed
                    bulletContent = bulletContent.replace(/^\* /g, '');
                    
                    // Handle any standalone asterisks that might be in the content
                    bulletContent = bulletContent.replace(/(?<!\*)\*(?!\*)/g, '');
                    
                    html += `<li>${bulletContent}</li>`;
                }
            }
            html += '</ul>';
        }
        
        return html;
    } else {
        // No bullet points, just format as paragraphs
        const paragraphs = content.split('\n\n');
        return paragraphs
            .map(p => {
                // Clean up any standalone asterisks
                return p.trim().replace(/(?<!\*)\*(?!\*)/g, '');
            })
            .filter(p => p.length > 0)
            .map(p => `<p>${p}</p>`)
            .join('');
    }
}

function formatResearchText(text) {
    // Split the text into paragraphs
    const paragraphs = text.split('\n\n');
    
    // Format each paragraph
    return paragraphs.map(paragraph => {
        // Skip empty paragraphs
        if (!paragraph.trim()) return '';
        
        // Check if this is a heading (starts with # or ##)
        if (paragraph.startsWith('# ')) {
            return `<h4>${paragraph.substring(2)}</h4>`;
        } else if (paragraph.startsWith('## ')) {
            return `<h5>${paragraph.substring(3)}</h5>`;
        }
        
        // Format lists
        if (paragraph.includes('\n- ')) {
            const parts = paragraph.split('\n- ');
            const intro = parts[0];
            const listItems = parts.slice(1);
            
            return `
                <p>${intro}</p>
                <ul>
                    ${listItems.map(item => `<li>${item}</li>`).join('')}
                </ul>
            `;
        }
        
        // Highlight keywords
        const keywordsToHighlight = [
            'neural networks', 'deep learning', 'machine learning', 'artificial intelligence',
            'computer vision', 'natural language processing', 'cognitive science', 'neuroscience',
            'perception', 'attention', 'memory', 'consciousness', 'brain', 'cognition'
        ];
        
        let formattedParagraph = paragraph;
        
        keywordsToHighlight.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            formattedParagraph = formattedParagraph.replace(regex, match => `<strong>${match}</strong>`);
        });
        
        // Regular paragraph
        return `<p>${formattedParagraph}</p>`;
    }).join('');
}

function setupProjectionButtons() {
    const projectionButtons = document.querySelectorAll('.projection-button');
    
    projectionButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Get the projection method
            const method = button.getAttribute('data-method');
            
            // Update active button
            projectionButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update the visualization
            updateScholarCoordinates(method);
        });
    });
}

function updateScholarCoordinates(method) {
    // Update current projection method
    window.currentProjection = method;
    
    // Recreate the map with the new projection
    if (window.scholarsData) {
        createScholarMap(window.scholarsData);
    }
}

function setupFilters(scholars) {
    // Get filter elements
    const filterToggle = document.getElementById('filter-toggle');
    const filterDropdown = document.querySelector('.filter-dropdown');
    const filterTabs = document.querySelectorAll('.filter-tab');
    const filterOptions = document.getElementById('filter-options');
    const applyButton = document.getElementById('apply-filters');
    const clearButton = document.getElementById('clear-filters');
    
    // Store filter state
    const filterState = {
        type: 'country', // Default filter type
        selectedFilters: []
    };
    
    // Toggle filter dropdown
    filterToggle.addEventListener('click', () => {
        filterDropdown.classList.toggle('active');
        filterToggle.classList.toggle('active');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!filterToggle.contains(e.target) && !filterDropdown.contains(e.target)) {
            filterDropdown.classList.remove('active');
            filterToggle.classList.remove('active');
        }
    });
    
    // Switch between filter tabs
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            filterTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Update filter type
            filterState.type = tab.dataset.type;
            
            // Reset selected filters
            filterState.selectedFilters = [];
            
            // Update filter options
            populateFilterOptions(scholars, filterState.type);
        });
    });
    
    // Apply filters
    applyButton.addEventListener('click', () => {
        applyFilters(scholars);
        filterDropdown.classList.remove('active');
        filterToggle.classList.remove('active');
        
        // Update filter button text to show active filters
        if (filterState.selectedFilters.length > 0) {
            filterToggle.innerHTML = `<i class="fas fa-filter"></i> Filtered (${filterState.selectedFilters.length})`;
            filterToggle.classList.add('active');
        } else {
            filterToggle.innerHTML = `<i class="fas fa-filter"></i> Filter`;
            filterToggle.classList.remove('active');
        }
    });
    
    // Clear filters
    clearButton.addEventListener('click', () => {
        filterState.selectedFilters = [];
        
        // Uncheck all checkboxes
        const checkboxes = filterOptions.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Apply filters (which will show all scholars)
        applyFilters(scholars);
        
        // Reset filter button text
        filterToggle.innerHTML = `<i class="fas fa-filter"></i> Filter`;
        filterToggle.classList.remove('active');
    });
    
    // Initial population of filter options
    populateFilterOptions(scholars, filterState.type);
    
    // Function to populate filter options based on type
    function populateFilterOptions(scholars, type) {
        // Clear existing options
        filterOptions.innerHTML = '';
        
        // Get unique values and counts
        const valueMap = new Map();
        
        scholars.forEach(scholar => {
            const value = scholar[type];
            if (value) {
                if (valueMap.has(value)) {
                    valueMap.set(value, valueMap.get(value) + 1);
                } else {
                    valueMap.set(value, 1);
                }
            }
        });
        
        // Sort values by count (descending)
        const sortedValues = [...valueMap.entries()]
            .sort((a, b) => b[1] - a[1]);
        
        // Create filter options
        sortedValues.forEach(([value, count]) => {
            const option = document.createElement('div');
            option.className = 'filter-option';
            
            const isChecked = filterState.selectedFilters.includes(value);
            
            option.innerHTML = `
                <label>
                    <input type="checkbox" value="${value}" ${isChecked ? 'checked' : ''}>
                    ${value}
                </label>
                <span class="count">${count}</span>
            `;
            
            // Add event listener to checkbox
            const checkbox = option.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    // Add to selected filters
                    if (!filterState.selectedFilters.includes(value)) {
                        filterState.selectedFilters.push(value);
                    }
                } else {
                    // Remove from selected filters
                    filterState.selectedFilters = filterState.selectedFilters.filter(f => f !== value);
                }
            });
            
            filterOptions.appendChild(option);
        });
    }
    
    // Function to apply filters
    function applyFilters(scholars) {
        // Get all scholar dots
        const dots = document.querySelectorAll('.scholar-dot');
        
        // If no filters selected, show all scholars
        if (filterState.selectedFilters.length === 0) {
            dots.forEach(dot => {
                dot.classList.remove('filtered-dot');
            });
            return;
        }
        
        // Apply filters
        dots.forEach(dot => {
            const scholarId = dot.getAttribute('data-id');
            const scholar = scholars.find(s => s.id === scholarId);
            
            if (scholar) {
                const value = scholar[filterState.type];
                
                if (value && filterState.selectedFilters.includes(value)) {
                    // Scholar matches filter, show it
                    dot.classList.remove('filtered-dot');
                } else {
                    // Scholar doesn't match filter, hide it
                    dot.classList.add('filtered-dot');
                }
            }
        });
    }
}

function setupSearch(scholars) {
    const searchInput = document.getElementById('scholar-search');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    
    // Function to perform fuzzy search
    function fuzzySearch(query, scholars) {
        if (!query) return [];
        
        query = query.toLowerCase();
        
        // Score each scholar based on how well they match the query
        const scoredScholars = scholars.map(scholar => {
            const name = scholar.name.toLowerCase();
            let score = 0;
            
            // Exact match gets highest score
            if (name === query) {
                score = 100;
            }
            // Starts with query gets high score
            else if (name.startsWith(query)) {
                score = 80;
            }
            // Contains query as a word gets medium score
            else if (name.includes(` ${query}`) || name.includes(`${query} `)) {
                score = 60;
            }
            // Contains query anywhere gets lower score
            else if (name.includes(query)) {
                score = 40;
            }
            // Check for partial matches (each word in the name)
            else {
                const nameWords = name.split(' ');
                for (const word of nameWords) {
                    if (word.startsWith(query)) {
                        score = Math.max(score, 30);
                    } else if (word.includes(query)) {
                        score = Math.max(score, 20);
                    }
                }
            }
            
            // Calculate Levenshtein distance for more fuzzy matching
            const distance = levenshteinDistance(query, name);
            const maxLength = Math.max(query.length, name.length);
            const similarityScore = (1 - distance / maxLength) * 20;
            
            score += similarityScore;
            
            return { scholar, score };
        });
        
        // Filter out scholars with zero score and sort by score (descending)
        return scoredScholars
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
            .map(item => item.scholar);
    }
    
    // Calculate Levenshtein distance between two strings
    function levenshteinDistance(a, b) {
        const matrix = [];
        
        // Initialize matrix
        for (let i = 0; i <= b.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= a.length; j++) {
            matrix[0][j] = j;
        }
        
        // Fill in the rest of the matrix
        for (let i = 1; i <= b.length; i++) {
            for (let j = 1; j <= a.length; j++) {
                if (b.charAt(i - 1) === a.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1, // substitution
                        matrix[i][j - 1] + 1,     // insertion
                        matrix[i - 1][j] + 1      // deletion
                    );
                }
            }
        }
        
        return matrix[b.length][a.length];
    }
    
    // Function to highlight matching text
    function highlightMatch(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<span class="search-result-highlight">$1</span>');
    }
    
    // Function to display search results
    function displaySearchResults(results, query) {
        searchResults.innerHTML = '';
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">No scholars found matching your search</div>';
            return;
        }
        
        results.forEach(scholar => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            
            const highlightedName = highlightMatch(scholar.name, query);
            
            resultItem.innerHTML = `
                <div class="search-result-image">
                    <img src="images/${scholar.profile_pic || 'placeholder.jpg'}" alt="${scholar.name}" onerror="this.src='images/placeholder.jpg'">
                </div>
                <div class="search-result-info">
                    <div class="search-result-name">${highlightedName}</div>
                    ${scholar.institution ? `<div class="search-result-institution">${scholar.institution}</div>` : ''}
                </div>
            `;
            
            // Add click event to show scholar details and highlight on map
            resultItem.addEventListener('click', () => {
                // Show scholar details
                showScholarDetails(scholar);
                
                // Highlight scholar on map
                highlightScholarOnMap(scholar.id);
                
                // Hide search results
                searchResults.classList.remove('active');
            });
            
            searchResults.appendChild(resultItem);
        });
    }
    
    // Function to highlight scholar on map
    function highlightScholarOnMap(scholarId) {
        // Remove highlight from all dots
        document.querySelectorAll('.scholar-dot').forEach(dot => {
            dot.classList.remove('highlighted');
            dot.classList.remove('highlighted-scholar');
        });
        
        // Add highlight to the matching scholar dot
        const dot = document.querySelector(`.scholar-dot[data-id="${scholarId}"]`);
        if (dot) {
            dot.classList.add('highlighted');
            dot.classList.add('highlighted-scholar');
            
            // Scroll the dot into view
            const dotsContainer = document.querySelector('.dots-container');
            if (dotsContainer) {
                // Get dot position
                const dotRect = dot.getBoundingClientRect();
                const containerRect = dotsContainer.getBoundingClientRect();
                
                // Calculate center position
                const centerX = dotRect.left + dotRect.width / 2 - containerRect.left;
                const centerY = dotRect.top + dotRect.height / 2 - containerRect.top;
                
                // Get current transform
                const transform = window.getComputedStyle(dotsContainer).transform;
                const matrix = new DOMMatrix(transform);
                
                // Calculate new transform to center the dot
                const scale = matrix.a; // Current scale
                const newTranslateX = -centerX * scale + containerRect.width / 2;
                const newTranslateY = -centerY * scale + containerRect.height / 2;
                
                // Apply new transform
                dotsContainer.style.transform = `translate(${newTranslateX}px, ${newTranslateY}px) scale(${scale})`;
            }
        }
    }
    
    // Handle search input
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        
        if (query.length >= 2) {
            const results = fuzzySearch(query, scholars);
            displaySearchResults(results, query);
            searchResults.classList.add('active');
        } else {
            searchResults.classList.remove('active');
        }
    });
    
    // Handle search button click
    searchButton.addEventListener('click', () => {
        const query = searchInput.value.trim();
        
        if (query.length >= 2) {
            const results = fuzzySearch(query, scholars);
            displaySearchResults(results, query);
            searchResults.classList.add('active');
        }
    });
    
    // Handle Enter key in search input
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            
            if (query.length >= 2) {
                const results = fuzzySearch(query, scholars);
                displaySearchResults(results, query);
                searchResults.classList.add('active');
            }
        }
    });
    
    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && 
            !searchButton.contains(e.target) && 
            !searchResults.contains(e.target)) {
            searchResults.classList.remove('active');
        }
    });
}

// Function to check if all scholars have a country
function checkScholarCountries(scholars) {
    const scholarsWithoutCountry = scholars.filter(scholar => !scholar.country);
    
    if (scholarsWithoutCountry.length > 0) {
        console.warn(`Found ${scholarsWithoutCountry.length} scholars without a country:`);
        scholarsWithoutCountry.forEach(scholar => {
            console.warn(`- ${scholar.name} (ID: ${scholar.id})`);
        });
    } else {
        console.log('All scholars have a country associated with them.');
    }
    
    // Count scholars by country
    const countryCount = {};
    scholars.forEach(scholar => {
        if (scholar.country) {
            countryCount[scholar.country] = (countryCount[scholar.country] || 0) + 1;
        }
    });
    
    // Log country distribution
    console.log('Scholar country distribution:');
    Object.entries(countryCount)
        .sort((a, b) => b[1] - a[1])
        .forEach(([country, count]) => {
            const percentage = ((count / scholars.length) * 100).toFixed(1);
            console.log(`- ${country}: ${count} scholars (${percentage}%)`);
        });
} 