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
    
    // Create nodes
    const nodeCount = 15;
    const nodes = [];
    const headerWidth = container.offsetWidth;
    const headerHeight = container.offsetHeight;
    
    for (let i = 0; i < nodeCount; i++) {
        const node = document.createElement('div');
        node.className = 'node';
        
        // Random position
        const x = Math.random() * headerWidth;
        const y = Math.random() * headerHeight;
        
        node.style.left = `${x}px`;
        node.style.top = `${y}px`;
        
        // Random size
        const size = 3 + Math.random() * 5;
        node.style.width = `${size}px`;
        node.style.height = `${size}px`;
        
        // Random animation delay
        node.style.animationDelay = `${Math.random() * 2}s`;
        
        container.appendChild(node);
        nodes.push({ element: node, x, y, size });
    }
    
    // Create connections between nearby nodes
    const maxDistance = 150;
    
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
                
                // Opacity based on distance
                const opacity = 1 - (distance / maxDistance);
                connection.style.opacity = opacity;
                
                container.appendChild(connection);
            }
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
        
        // Add hover effect with tooltip following mouse
        dot.addEventListener('mouseenter', () => {
            dot.style.width = '24px';
            dot.style.height = '24px';
            dot.style.zIndex = '100';
            tooltip.style.display = 'block';
        });
        
        dot.addEventListener('mousemove', (e) => {
            const x = e.clientX;
            const y = e.clientY;
            tooltip.style.left = `${x + 15}px`;
            tooltip.style.top = `${y - 15}px`;
        });
        
        dot.addEventListener('mouseleave', () => {
            dot.style.width = '16px';
            dot.style.height = '16px';
            dot.style.zIndex = '1';
            tooltip.style.display = 'none';
        });
        
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

function createCountryLegend(colorMap, countryCount, totalScholars) {
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