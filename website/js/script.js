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
            if (!scholar.id || !scholar.name || !scholar.coords || !Array.isArray(scholar.coords) || scholar.coords.length !== 2) {
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
        
        // Preload images to avoid rendering issues
        preloadImages(validScholars);
        
        // Create the scholar map
        createScholarMap(validScholars);
        
        // Set up sidebar functionality
        setupSidebar();
        
        // Set up search functionality
        setupSearch(validScholars);
        
        // Set up search toggle functionality
        setupSearchToggle();
    } catch (error) {
        console.error('Error loading scholar data:', error);
        // Try loading from the old file as fallback
        try {
            console.log('Attempting to load from researchers.json as fallback...');
            const fallbackResponse = await fetch('data/researchers.json');
            console.log('Fallback response:', fallbackResponse.status, fallbackResponse.statusText);
            
            if (fallbackResponse.ok) {
                const researchers = await fallbackResponse.json();
                console.log(`Loaded ${researchers.length} researchers from fallback`);
                console.log('Sample researcher data:', researchers[0]);
                
                alert('Warning: Using legacy data format. Please run prepare_data.py to update the data.');
                
                // Use the researchers data
                preloadImages(researchers);
                createScholarMap(researchers);
                setupSidebar();
                setupSearch(researchers);
                setupSearchToggle();
            }
        } catch (e) {
            console.error('Fallback also failed:', e);
        }
    }
});

function preloadImages(scholars) {
    // Preload all scholar profile images
    scholars.forEach(scholar => {
        if (scholar.profile_pic) {
            const img = new Image();
            img.src = `images/${scholar.profile_pic}`;
            img.onerror = () => {
                console.warn(`Failed to load image for ${scholar.name}`);
                // Set a default image path in the scholar data
                scholar.profile_pic = 'placeholder.jpg';
            };
        }
    });
}

function setupSearch(scholars) {
    const searchButton = document.getElementById('search-button');
    const queryInput = document.getElementById('research-query');
    const searchResults = document.getElementById('search-results');
    const resultsList = document.getElementById('results-list');
    const closeResults = document.getElementById('close-results');
    
    // Handle search button click
    searchButton.addEventListener('click', () => {
        performSearch();
    });
    
    // Handle Enter key press in search input
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Handle close results button
    closeResults.addEventListener('click', () => {
        searchResults.classList.add('hidden');
    });
    
    async function performSearch() {
        const query = queryInput.value.trim();
        
        if (!query) {
            return;
        }
        
        // Clear previous results
        resultsList.innerHTML = '';
        
        // Show loading state
        resultsList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Searching for experts...</div>';
        searchResults.classList.remove('hidden');
        
        try {
            // Call our search API
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_n: 8,
                    use_low_dim: false // Use high-dimensional embeddings for more accurate results
                })
            });
            
            if (!response.ok) {
                throw new Error(`Search request failed with status ${response.status}`);
            }
            
            const data = await response.json();
            const results = data.scholars || [];
            
            // Map the results to our expected format
            const formattedResults = results.map(result => {
                // Find the full scholar data from our loaded scholars
                const scholarData = scholars.find(s => s.id === result.scholar_id) || {};
                
                return {
                    id: result.scholar_id,
                    name: result.name,
                    profile_pic: scholarData.profile_pic || 'placeholder.jpg',
                    similarity: Math.round(result.similarity * 100) // Convert to percentage
                };
            });
            
            // Display results
            displaySearchResults(formattedResults, scholars);
        } catch (error) {
            console.error('Search error:', error);
            resultsList.innerHTML = '<div class="error"><i class="fas fa-exclamation-circle"></i> An error occurred during search. Please try again.</div>';
        }
    }
    
    function displaySearchResults(results, allScholars) {
        resultsList.innerHTML = '';
        
        if (results.length === 0) {
            resultsList.innerHTML = '<div class="no-results">No matching scholars found</div>';
            return;
        }
        
        // Create a scrollable container for results
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'results-container';
        
        // Add each result to the container
        results.forEach((scholar, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            if (index < 3) {
                resultItem.classList.add('top-result');
            }
            
            // Ensure profile pic exists or use placeholder
            const profilePic = scholar.profile_pic || 'placeholder.jpg';
            
            resultItem.innerHTML = `
                <img src="images/${profilePic}" alt="${scholar.name}" onerror="this.src='images/placeholder.jpg'">
                <div class="result-info">
                    <div class="result-name">${scholar.name}</div>
                </div>
                <div class="result-similarity">${scholar.similarity}% match</div>
            `;
            
            // Add click event to highlight scholar on the map
            resultItem.addEventListener('click', () => {
                // Find the scholar node on the map
                const scholarNode = document.querySelector(`.scholar-node[data-id="${scholar.id}"]`);
                
                if (scholarNode) {
                    // Highlight the node
                    highlightScholarNode(scholarNode);
                    
                    // Center the view on the scholar
                    window.centerViewOnScholar(scholarNode);
                    
                    // Show scholar details
                    const fullScholarData = allScholars.find(s => s.id === scholar.id);
                    if (fullScholarData) {
                        showScholarDetails(fullScholarData);
                    }
                    
                    // Close search results
                    searchResults.classList.add('hidden');
                    
                    // Close search container and show button
                    document.getElementById('search-container').classList.remove('active');
                    document.getElementById('search-toggle').classList.remove('hidden');
                }
            });
            
            resultsContainer.appendChild(resultItem);
        });
        
        resultsList.appendChild(resultsContainer);
    }
    
    function highlightScholarNode(node) {
        // Add a temporary highlight effect
        node.classList.add('highlight-pulse');
        
        // Remove the highlight after animation completes
        setTimeout(() => {
            node.classList.remove('highlight-pulse');
        }, 2000);
        
        // Scroll the node into view
        node.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
}

function setupSidebar() {
    const sidebar = document.getElementById('sidebar');
    const closeButton = document.getElementById('close-sidebar');
    const mapContainer = document.getElementById('map-container');
    
    closeButton.addEventListener('click', () => {
        sidebar.style.display = 'none';
        mapContainer.style.flex = '1 1 100%';
        
        // Remove active class from all scholar nodes
        document.querySelectorAll('.scholar-node.active').forEach(node => {
            node.classList.remove('active');
        });
    });
}

function createScholarMap(scholars) {
    const mapContainer = document.getElementById('map-container');
    const scholarMap = document.getElementById('scholar-map');
    
    console.log(`Creating scholar map with ${scholars.length} scholars`);
    
    // Clear any existing content
    scholarMap.innerHTML = '';
    
    // Find min and max coordinates to normalize
    const allCoords = scholars.map(r => r.coords);
    const xCoords = allCoords.map(c => c[0]);
    const yCoords = allCoords.map(c => c[1]);
    
    const minX = Math.min(...xCoords);
    const maxX = Math.max(...xCoords);
    const minY = Math.min(...yCoords);
    const maxY = Math.max(...yCoords);
    
    console.log(`Coordinate ranges: X(${minX} to ${maxX}), Y(${minY} to ${maxY})`);
    
    // Calculate padding (15% of the range)
    const xPadding = (maxX - minX) * 0.15;
    const yPadding = (maxY - minY) * 0.15;
    
    // Define map state variables in the outer scope so they're accessible to all functions
    let scale = 1;
    let translateX = 0;
    let translateY = 0;
    let isDragging = false;
    let startX, startY;
    
    // Function to center the view on a scholar
    window.centerViewOnScholar = function(node) {
        // Get the map container dimensions and position
        const mapRect = mapContainer.getBoundingClientRect();
        
        // Calculate the true center of the visible map area
        const visibleMapCenterX = mapRect.width / 2;
        const visibleMapCenterY = mapRect.height / 2;
        
        // Get the node's position relative to the viewport
        const nodeRect = node.getBoundingClientRect();
        const nodeX = nodeRect.left + nodeRect.width / 2;
        const nodeY = nodeRect.top + nodeRect.height / 2;
        
        // Calculate the node's position relative to the map container
        const nodeRelativeX = nodeX - mapRect.left;
        const nodeRelativeY = nodeY - mapRect.top;
        
        // Calculate the distance from the center of the map
        const distanceFromCenterX = visibleMapCenterX - nodeRelativeX;
        const distanceFromCenterY = visibleMapCenterY - nodeRelativeY;
        
        // Update the translation to center the node
        translateX += distanceFromCenterX;
        translateY += distanceFromCenterY;
        
        // Apply the transform
        applyTransform();
    };
    
    // Function to apply transform
    function applyTransform() {
        scholarMap.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }
    
    // Add scholars to the map
    console.log(`Adding ${scholars.length} scholars to the map`);
    let nodesCreated = 0;
    
    scholars.forEach((scholar, index) => {
        try {
            // Create scholar node
            const node = document.createElement('div');
            node.className = 'scholar-node';
            
            // Add animation delay for staggered appearance
            node.style.animationDelay = `${Math.random() * 2}s`;
            
            node.dataset.name = scholar.name;
            node.dataset.id = scholar.id;
            
            // Normalize coordinates to fit the container with padding
            const normalizedX = ((scholar.coords[0] - minX + xPadding) / (maxX - minX + 2 * xPadding)) * 100;
            const normalizedY = ((scholar.coords[1] - minY + yPadding) / (maxY - minY + 2 * yPadding)) * 100;
            
            // Position the node
            node.style.left = `${normalizedX}%`;
            node.style.top = `${normalizedY}%`;
            
            // Create profile picture
            const profilePic = document.createElement('img');
            profilePic.className = 'profile-pic';
            
            if (scholar.profile_pic) {
                profilePic.src = `images/${scholar.profile_pic}`;
                profilePic.alt = `${scholar.name}`;
            } else {
                // Use placeholder if no profile picture
                profilePic.src = 'images/placeholder.jpg';
                profilePic.alt = 'Profile placeholder';
            }
            
            // Create label
            const label = document.createElement('div');
            label.className = 'scholar-label';
            label.textContent = scholar.name;
            
            // Create scholar info
            const info = document.createElement('div');
            info.className = 'scholar-info';
            
            const name = document.createElement('div');
            name.className = 'scholar-name';
            name.textContent = scholar.name;
            
            // Assemble the node
            info.appendChild(name);
            node.appendChild(profilePic);
            node.appendChild(label);
            node.appendChild(info);
            
            // Add click event to show details in sidebar
            node.addEventListener('click', () => {
                showScholarDetails(scholar);
                
                // Remove active class from all nodes
                document.querySelectorAll('.scholar-node.active').forEach(n => {
                    n.classList.remove('active');
                });
                
                // Add active class to this node
                node.classList.add('active');
                
                // Show sidebar
                document.getElementById('sidebar').style.display = 'block';
                
                // Adjust map container flex
                mapContainer.style.flex = '1 1 70%';
            });
            
            // Add hover effect for info display
            node.addEventListener('mouseenter', () => {
                info.style.opacity = '1';
                info.style.visibility = 'visible';
                info.style.transform = 'translateX(-50%) translateY(5px)';
            });
            
            node.addEventListener('mouseleave', () => {
                info.style.opacity = '0';
                info.style.visibility = 'hidden';
                info.style.transform = 'translateX(-50%)';
            });
            
            // Add to map
            scholarMap.appendChild(node);
            nodesCreated++;
            
            // Log progress for large datasets
            if (index % 100 === 0 || index === scholars.length - 1) {
                console.log(`Added ${index + 1}/${scholars.length} scholars to the map`);
            }
        } catch (error) {
            console.error(`Error adding scholar ${scholar.name} (${scholar.id}) to map:`, error);
        }
    });
    
    console.log(`Created ${nodesCreated} scholar nodes on the map`);
    
    // Add a message if no nodes were created
    if (nodesCreated === 0) {
        scholarMap.innerHTML = '<div style="color: red; padding: 20px; text-align: center;">Failed to create any scholar nodes. Please check the console for errors.</div>';
    }
    
    // Set up zoom controls
    const zoomInButton = document.getElementById('zoom-in');
    const zoomOutButton = document.getElementById('zoom-out');
    const resetViewButton = document.getElementById('reset-view');
    
    zoomInButton.addEventListener('click', () => {
        scale = Math.min(3, scale + 0.2);
        applyTransform();
    });
    
    zoomOutButton.addEventListener('click', () => {
        scale = Math.max(0.5, scale - 0.2);
        applyTransform();
    });
    
    resetViewButton.addEventListener('click', () => {
        scale = 1;
        translateX = 0;
        translateY = 0;
        applyTransform();
    });
    
    // Zoom with mouse wheel
    mapContainer.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        scale = Math.max(0.5, Math.min(3, scale + delta));
        applyTransform();
    });
    
    // Pan with mouse drag
    mapContainer.addEventListener('mousedown', (e) => {
        if (e.target === scholarMap || e.target === mapContainer) {
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
}

function showScholarDetails(scholar) {
    const detailsContainer = document.getElementById('scholar-details');
    
    // Ensure profile pic exists or use placeholder
    const profilePic = scholar.profile_pic || 'placeholder.jpg';
    
    // Create details HTML
    let detailsHTML = `
        <div class="scholar-profile">
            <img src="images/${profilePic}" alt="${scholar.name}" onerror="this.src='images/placeholder.jpg'">
            <h3>${scholar.name}</h3>
        </div>
    `;
    
    // Add projections information
    if (scholar.projections) {
        detailsHTML += `
            <div class="scholar-projections">
                <h4>Projection Methods</h4>
                <div class="projection-buttons">
                    <button class="projection-button" data-method="pca">PCA</button>
                    <button class="projection-button" data-method="tsne">t-SNE</button>
                    <button class="projection-button active" data-method="umap">UMAP</button>
                </div>
            </div>
        `;
    }
    
    // Set the HTML content
    detailsContainer.innerHTML = detailsHTML;
    
    // Add event listeners to projection buttons if they exist
    const projectionButtons = detailsContainer.querySelectorAll('.projection-button');
    projectionButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            projectionButtons.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Get the projection method
            const method = button.dataset.method;
            
            // Update the visualization (this would be implemented in a real application)
            console.log(`Switching to ${method} projection`);
        });
    });
}

function formatResearchText(text) {
    if (!text) return '';
    
    // Replace newlines with HTML line breaks
    let formatted = text.replace(/\n/g, '<br>');
    
    // Make section headers bold
    formatted = formatted.replace(/(\d+\.\s+[^:]+:)/g, '<strong>$1</strong>');
    
    // Add paragraph breaks for better readability
    formatted = formatted.replace(/<strong>/g, '<p><strong>');
    formatted = formatted.replace(/<\/strong>/g, '</strong></p>');
    
    // Highlight key terms
    const keyTerms = [
        'cognitive neuroscience', 'computational modeling', 'artificial intelligence',
        'deep learning', 'visual perception', 'neural networks', 'brain', 'vision',
        'fMRI', 'EEG', 'MEG', 'neuroimaging', 'machine learning', 'computer vision',
        'cognitive science', 'neuroscience', 'perception', 'memory', 'attention',
        'object recognition', 'scene understanding', 'neural coding', 'neural representations'
    ];
    
    // Sort terms by length (longest first) to avoid partial matches
    keyTerms.sort((a, b) => b.length - a.length);
    
    // Highlight each term
    keyTerms.forEach(term => {
        const regex = new RegExp(`\\b${term}\\b`, 'gi');
        formatted = formatted.replace(regex, match => `<span class="highlight">${match}</span>`);
    });
    
    return formatted;
}

function setupSearchToggle() {
    const searchToggleBtn = document.getElementById('search-toggle');
    const searchContainer = document.getElementById('search-container');
    const searchInput = document.getElementById('research-query');
    
    // Toggle search container visibility when button is clicked
    searchToggleBtn.addEventListener('click', () => {
        searchContainer.classList.toggle('active');
        searchToggleBtn.classList.toggle('hidden');
        
        // Focus the input field when the search container is shown
        if (searchContainer.classList.contains('active')) {
            setTimeout(() => {
                searchInput.focus();
            }, 300); // Wait for the animation to complete
        }
    });
    
    // Close search container when clicking outside
    document.addEventListener('click', (e) => {
        const isClickInsideSearch = searchContainer.contains(e.target);
        const isClickOnToggle = searchToggleBtn.contains(e.target);
        const isSearchActive = searchContainer.classList.contains('active');
        
        if (isSearchActive && !isClickInsideSearch && !isClickOnToggle) {
            searchContainer.classList.remove('active');
            searchToggleBtn.classList.remove('hidden');
        }
    });
    
    // Close search container when pressing Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && searchContainer.classList.contains('active')) {
            searchContainer.classList.remove('active');
            searchToggleBtn.classList.remove('hidden');
        }
    });
} 