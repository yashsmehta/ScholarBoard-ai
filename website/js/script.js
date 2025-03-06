document.addEventListener('DOMContentLoaded', async () => {
    // Load researcher data
    try {
        const response = await fetch('data/researchers.json');
        const researchers = await response.json();
        
        if (researchers.length === 0) {
            console.error('No researcher data found');
            return;
        }
        
        // Preload images to avoid rendering issues
        preloadImages(researchers);
        
        // Create the researcher map
        createResearcherMap(researchers);
        
        // Set up sidebar functionality
        setupSidebar();
        
        // Set up search functionality
        setupSearch(researchers);
        
        // Set up search toggle functionality
        setupSearchToggle();
    } catch (error) {
        console.error('Error loading researcher data:', error);
    }
});

function preloadImages(researchers) {
    // Preload all researcher profile images
    researchers.forEach(researcher => {
        if (researcher.profile_pic) {
            const img = new Image();
            img.src = `images/${researcher.profile_pic}`;
            img.onerror = () => {
                console.warn(`Failed to load image for ${researcher.name}`);
                // Set a default image path in the researcher data
                researcher.profile_pic = 'placeholder.jpg';
            };
        }
    });
}

function setupSearch(researchers) {
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
            // In a real application, this would be an API call to a backend service
            // For this demo, we'll simulate a search by waiting and then returning random results
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Simulate search results by selecting random researchers
            // In a real app, this would be based on actual relevance to the query
            const numResults = Math.min(8, researchers.length);
            const shuffled = [...researchers].sort(() => 0.5 - Math.random());
            const results = shuffled.slice(0, numResults).map(r => ({
                ...r,
                // Simulate a relevance score between 70-95%
                similarity: Math.floor(70 + Math.random() * 25)
            }));
            
            // Sort by similarity (highest first)
            results.sort((a, b) => b.similarity - a.similarity);
            
            // Display results
            displaySearchResults(results, researchers);
        } catch (error) {
            console.error('Search error:', error);
            resultsList.innerHTML = '<div class="error"><i class="fas fa-exclamation-circle"></i> An error occurred during search. Please try again.</div>';
        }
    }
    
    function displaySearchResults(results, allResearchers) {
        resultsList.innerHTML = '';
        
        if (results.length === 0) {
            resultsList.innerHTML = '<div class="no-results">No matching researchers found</div>';
            return;
        }
        
        // Create a scrollable container for results
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'results-container';
        
        // Add each result to the container
        results.forEach((researcher, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            if (index < 3) {
                resultItem.classList.add('top-result');
            }
            
            // Ensure profile pic exists or use placeholder
            const profilePic = researcher.profile_pic || 'placeholder.jpg';
            
            resultItem.innerHTML = `
                <img src="images/${profilePic}" alt="${researcher.name}" onerror="this.src='images/placeholder.jpg'">
                <div class="result-info">
                    <div class="result-name">${researcher.name}</div>
                    <div class="result-institution">${researcher.institution || 'Independent Researcher'}</div>
                </div>
                <div class="result-similarity">${researcher.similarity}% match</div>
            `;
            
            // Add click event to highlight researcher on the map
            resultItem.addEventListener('click', () => {
                // Find the researcher node on the map
                const researcherNode = document.querySelector(`.researcher-node[data-id="${researcher.id}"]`);
                
                if (researcherNode) {
                    // Highlight the node
                    highlightResearcherNode(researcherNode);
                    
                    // Center the view on the researcher
                    window.centerViewOnResearcher(researcherNode);
                    
                    // Show researcher details
                    showResearcherDetails(researcher);
                    
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
    
    function highlightResearcherNode(node) {
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
        
        // Remove active class from all researcher nodes
        document.querySelectorAll('.researcher-node.active').forEach(node => {
            node.classList.remove('active');
        });
    });
}

function createResearcherMap(researchers) {
    const mapContainer = document.getElementById('map-container');
    const researcherMap = document.getElementById('researcher-map');
    
    // Find min and max coordinates to normalize
    const allCoords = researchers.map(r => r.coords);
    const xCoords = allCoords.map(c => c[0]);
    const yCoords = allCoords.map(c => c[1]);
    
    const minX = Math.min(...xCoords);
    const maxX = Math.max(...xCoords);
    const minY = Math.min(...yCoords);
    const maxY = Math.max(...yCoords);
    
    // Calculate padding (15% of the range)
    const xPadding = (maxX - minX) * 0.15;
    const yPadding = (maxY - minY) * 0.15;
    
    // Define map state variables in the outer scope so they're accessible to all functions
    let scale = 1;
    let translateX = 0;
    let translateY = 0;
    let isDragging = false;
    let startX, startY;
    
    // Function to center the view on a researcher
    window.centerViewOnResearcher = function(node) {
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
        const distanceFromCenterX = Math.abs(visibleMapCenterX - nodeRelativeX);
        const distanceFromCenterY = Math.abs(visibleMapCenterY - nodeRelativeY);
        
        // Define thresholds for when centering should occur (as percentage of container size)
        const thresholdX = mapRect.width * 0.3; // Only center if node is more than 30% away from center
        const thresholdY = mapRect.height * 0.3;
        
        // Only apply centering if the node is far enough from the center
        if (distanceFromCenterX > thresholdX || distanceFromCenterY > thresholdY) {
            // Calculate the translation needed to center the node
            const dx = visibleMapCenterX - nodeRelativeX;
            const dy = visibleMapCenterY - nodeRelativeY;
            
            // Update the translation values (keeping the current scale)
            translateX += dx;
            translateY += dy;
            
            // Apply the transform with a smooth animation
            researcherMap.style.transition = 'transform 0.5s ease-out';
            applyTransform();
            
            // Remove the transition after animation completes
            setTimeout(() => {
                researcherMap.style.transition = 'none';
            }, 500);
            
            // Log centering information for debugging
            console.log('Centering applied:', {
                mapCenter: { x: visibleMapCenterX, y: visibleMapCenterY },
                nodePosition: { x: nodeRelativeX, y: nodeRelativeY },
                translation: { dx, dy },
                newTranslation: { x: translateX, y: translateY }
            });
        }
    };
    
    // Function to apply transform
    function applyTransform() {
        researcherMap.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    }
    
    // Add researchers to the map
    researchers.forEach(researcher => {
        // Create researcher node
        const node = document.createElement('div');
        node.className = 'researcher-node';
        
        // Add float animation with random delay for a more natural look
        node.classList.add('float');
        node.style.animationDelay = `${Math.random() * 2}s`;
        
        node.dataset.name = researcher.name;
        node.dataset.id = researcher.id;
        
        // Normalize coordinates to fit the container with padding
        const normalizedX = ((researcher.coords[0] - minX + xPadding) / (maxX - minX + 2 * xPadding)) * 100;
        const normalizedY = ((researcher.coords[1] - minY + yPadding) / (maxY - minY + 2 * yPadding)) * 100;
        
        // Position the node
        node.style.left = `${normalizedX}%`;
        node.style.top = `${normalizedY}%`;
        
        // Create profile picture
        const profilePic = document.createElement('img');
        profilePic.className = 'profile-pic';
        
        if (researcher.profile_pic) {
            profilePic.src = `images/${researcher.profile_pic}`;
            profilePic.alt = `${researcher.name}`;
        } else {
            // Use placeholder if no profile picture
            profilePic.src = 'images/placeholder.jpg';
            profilePic.alt = 'No profile picture';
        }
        
        // Add error handler for images
        profilePic.onerror = function() {
            this.src = 'images/placeholder.jpg';
            this.alt = 'No profile picture';
        };
        
        // Create researcher label (name below icon)
        const label = document.createElement('div');
        label.className = 'researcher-label';
        label.textContent = researcher.name;
        
        // Create researcher info
        const info = document.createElement('div');
        info.className = 'researcher-info';
        
        const name = document.createElement('div');
        name.className = 'researcher-name';
        name.textContent = researcher.name;
        
        const institution = document.createElement('div');
        institution.className = 'researcher-institution';
        institution.textContent = researcher.institution || 'Independent Researcher';
        
        // Assemble the node
        info.appendChild(name);
        info.appendChild(institution);
        node.appendChild(profilePic);
        node.appendChild(label);
        node.appendChild(info);
        
        // Add click event to show details in sidebar
        node.addEventListener('click', () => {
            showResearcherDetails(researcher);
            
            // Remove active class from all nodes
            document.querySelectorAll('.researcher-node.active').forEach(n => {
                n.classList.remove('active');
            });
            
            // Add active class to clicked node
            node.classList.add('active');
            
            // Center the view on the clicked researcher
            window.centerViewOnResearcher(node);
            
            // Show sidebar if hidden
            const sidebar = document.getElementById('sidebar');
            sidebar.style.display = 'flex';
            
            // Adjust map container width
            mapContainer.style.flex = `0 0 calc(100% - var(--sidebar-width) - 1.5rem)`;
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
        researcherMap.appendChild(node);
    });
    
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
        if (e.target === researcherMap || e.target === mapContainer) {
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

function showResearcherDetails(researcher) {
    const detailsContainer = document.getElementById('researcher-details');
    
    // Ensure profile pic exists or use placeholder
    const profilePic = researcher.profile_pic || 'placeholder.jpg';
    
    // Create details HTML
    let detailsHTML = `
        <div class="researcher-profile">
            <img src="images/${profilePic}" alt="${researcher.name}" onerror="this.src='images/placeholder.jpg'">
            <h3>${researcher.name}</h3>
            <p>${researcher.institution || 'Independent Researcher'}</p>
        </div>
    `;
    
    if (researcher.research_areas && researcher.research_areas.length > 0) {
        // Format the research areas text for better readability
        const formattedText = formatResearchText(researcher.research_areas);
        
        detailsHTML += `
            <div class="research-area">
                <h4>Research Areas</h4>
                <div class="research-content">${formattedText}</div>
            </div>
        `;
    } else {
        detailsHTML += `
            <div class="research-area">
                <h4>Research Areas</h4>
                <p>No research area information available.</p>
            </div>
        `;
    }
    
    // Add animation class
    detailsContainer.classList.add('fade-in');
    
    // Update details container
    detailsContainer.innerHTML = detailsHTML;
    
    // Remove animation class after animation completes
    setTimeout(() => {
        detailsContainer.classList.remove('fade-in');
    }, 500);
    
    // Make sure sidebar is visible
    document.getElementById('sidebar').style.display = 'flex';
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