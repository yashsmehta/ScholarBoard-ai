document.addEventListener('DOMContentLoaded', async () => {
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
        
    } catch (error) {
        console.error('Error loading scholar data:', error);
        document.getElementById('scholar-map').innerHTML = '<div style="color: red; padding: 20px; text-align: center;">Error loading scholar data. Please check the console for details.</div>';
    }
});

function setupSidebar() {
    // Set up sidebar close button
    const closeButton = document.getElementById('close-sidebar');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            document.getElementById('sidebar').classList.remove('active');
        });
    }
}

function createScholarMap(scholars) {
    const mapContainer = document.getElementById('scholar-map');
    if (!mapContainer) return;
    
    // Clear any existing content
    mapContainer.innerHTML = '';
    
    // Get the current projection method
    const projectionMethod = window.currentProjection || 'umap';
    console.log(`Creating map with ${projectionMethod} projection`);
    
    // Create a color map for countries
    const countries = [...new Set(scholars.map(s => s.country).filter(Boolean))];
    const colorMap = {};
    const colors = [
        '#4285F4', '#EA4335', '#FBBC05', '#34A853', // Google colors
        '#8AB4F8', '#F28B82', '#FDD663', '#81C995', // Lighter versions
        '#1967D2', '#D93025', '#F9AB00', '#1E8E3E', // Darker versions
        '#D2E3FC', '#FADBD8', '#FCE8B2', '#CEEAD6', // Even lighter versions
        '#174EA6', '#A50E0E', '#E37400', '#0D652D'  // Even darker versions
    ];
    
    countries.forEach((country, i) => {
        colorMap[country] = colors[i % colors.length];
    });
    
    // Create a legend for countries
    createCountryLegend(colorMap);
    
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
        dot.setAttribute('title', `${scholar.name}${scholar.institution ? ` (${scholar.institution})` : ''}`);
        
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
        
        // Add hover effect
        dot.addEventListener('mouseenter', () => {
            dot.style.width = '24px';
            dot.style.height = '24px';
            dot.style.zIndex = '100';
        });
        
        dot.addEventListener('mouseleave', () => {
            dot.style.width = '16px';
            dot.style.height = '16px';
            dot.style.zIndex = '1';
        });
        
        // Add click event to show scholar details
        dot.addEventListener('click', () => {
            // Remove highlight from all dots
            document.querySelectorAll('.scholar-dot').forEach(d => {
                d.style.border = '2px solid white';
                d.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
            });
            
            // Highlight this dot
            dot.style.border = '3px solid #ffcc00';
            dot.style.boxShadow = '0 0 10px rgba(255,204,0,0.7)';
            
            // Show scholar details
            showScholarDetails(scholar);
        });
        
        // Add the dot to the container
        dotsContainer.appendChild(dot);
        nodesCreated++;
    });
    
    console.log(`Created ${nodesCreated} scholar dots on the map`);
    
    // Add the dots container to the map
    mapContainer.appendChild(dotsContainer);
    
    // Add zoom and pan functionality
    let scale = 1;
    let translateX = 0;
    let translateY = 0;
    let isDragging = false;
    let startX, startY;
    
    function applyTransform() {
        dotsContainer.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }
    
    // Mouse wheel zoom
    mapContainer.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        scale *= delta;
        
        // Limit zoom
        scale = Math.max(0.5, Math.min(5, scale));
        
        applyTransform();
    });
    
    // Mouse pan
    mapContainer.addEventListener('mousedown', (e) => {
        if (e.button === 0) { // Left mouse button
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
            mapContainer.style.cursor = 'grabbing';
        }
    });
    
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            applyTransform();
        }
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
        mapContainer.style.cursor = 'default';
    });
    
    // Set up zoom controls
    const zoomInButton = document.getElementById('zoom-in');
    const zoomOutButton = document.getElementById('zoom-out');
    const resetViewButton = document.getElementById('reset-view');
    
    if (zoomInButton) {
        zoomInButton.addEventListener('click', () => {
            scale *= 1.2;
            scale = Math.min(5, scale);
            applyTransform();
        });
    }
    
    if (zoomOutButton) {
        zoomOutButton.addEventListener('click', () => {
            scale *= 0.8;
            scale = Math.max(0.5, scale);
            applyTransform();
        });
    }
    
    if (resetViewButton) {
        resetViewButton.addEventListener('click', () => {
            scale = 1;
            translateX = 0;
            translateY = 0;
            applyTransform();
        });
    }
}

function createCountryLegend(colorMap) {
    // Create a legend container
    const legendContainer = document.createElement('div');
    legendContainer.className = 'country-legend';
    legendContainer.innerHTML = '<h3>Countries</h3>';
    
    // Create legend items
    const countries = Object.keys(colorMap).sort();
    
    countries.forEach(country => {
        const color = colorMap[country];
        
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        
        const colorSwatch = document.createElement('span');
        colorSwatch.className = 'color-swatch';
        colorSwatch.style.backgroundColor = color;
        
        const countryName = document.createElement('span');
        countryName.className = 'country-name';
        countryName.textContent = country;
        
        legendItem.appendChild(colorSwatch);
        legendItem.appendChild(countryName);
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
    
    // Show the sidebar
    sidebar.classList.add('active');
    
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
                if (data.raw_text) {
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
        
        // Regular paragraph
        return `<p>${paragraph}</p>`;
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