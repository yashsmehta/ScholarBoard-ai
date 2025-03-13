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
        
        const scholarsData = await response.json();
        console.log('Loaded scholars data:', scholarsData);
        
        // Convert from object format to array format
        const scholars = Object.entries(scholarsData).map(([id, scholar]) => {
            return {
                id: scholar.id,
                name: scholar.name,
                institution: scholar.institution || '',
                country: scholar.country || '',
                umap: scholar.umap_projection ? [scholar.umap_projection.x, scholar.umap_projection.y] : null,
                cluster_id: scholar.cluster || 0
            };
        });
        
        console.log(`Converted ${scholars.length} scholars`);
        
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
            // Check if scholar has UMAP coordinates
            const hasUMAP = scholar.umap && Array.isArray(scholar.umap) && scholar.umap.length === 2;
            
            if (!scholar.id || !scholar.name || !hasUMAP) {
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
        
        // Store the original scholars data
        window.scholarsData = validScholars;
        
        // Create the scholar map
        createScholarMap(validScholars);
        
        // Set up sidebar functionality
        setupSidebar();
        
        // Set up filter functionality
        setupFilters(validScholars);
        
        // Set up search functionality
        setupSearch();
        
    } catch (error) {
        console.error('Error loading scholar data:', error);
        document.getElementById('scholar-map').innerHTML = '<div style="color: red; padding: 20px; text-align: center;">Error loading scholar data. Please check the console for details.</div>';
    }
    
    // Add event listener for the close sidebar button
    document.getElementById('close-sidebar').addEventListener('click', () => {
        document.getElementById('sidebar').classList.remove('active');
        resetView();
    });
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
    
    // Create SVG element
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', '0 0 1000 1000');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    mapContainer.appendChild(svg);
    
    // Create a group for all scholars
    const scholarsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    scholarsGroup.setAttribute('class', 'scholars-group');
    svg.appendChild(scholarsGroup);
    
    // Create a group for labels
    const labelsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    labelsGroup.setAttribute('class', 'labels-group');
    svg.appendChild(labelsGroup);
    
    // Get all UMAP coordinates
    const coordinates = scholars.map(scholar => scholar.umap);
    
    // Find min and max values for scaling
    const xValues = coordinates.map(coord => coord[0]);
    const yValues = coordinates.map(coord => coord[1]);
    
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);
    
    // Calculate padding (10% of range)
    const xPadding = (xMax - xMin) * 0.1;
    const yPadding = (yMax - yMin) * 0.1;
    
    // Scale coordinates to fit SVG
    const scaleX = (x) => {
        return ((x - xMin) / (xMax - xMin)) * 900 + 50;
    };
    
    const scaleY = (y) => {
        return ((y - yMin) / (yMax - yMin)) * 900 + 50;
    };
    
    // Get all unique cluster IDs
    const clusterIds = [...new Set(scholars.map(scholar => scholar.cluster_id || 0))];
    
    // Use Spectral colormap for cluster colors, similar to the Python code
    const clusterColors = {};
    clusterIds.forEach((clusterId, index) => {
        // Skip noise cluster (-1) which should be black
        if (clusterId === -1) {
            clusterColors[clusterId] = '#000000'; // Black for noise points
        } else {
            // Use a similar color scheme to matplotlib's Spectral colormap
            // We'll use the CSS variables defined for clusters 1-12
            const colorIndex = (index % 12) + 1; // We have 12 colors defined
            clusterColors[clusterId] = `var(--cluster-color-${colorIndex})`;
        }
    });
    
    // Shuffle scholars to avoid z-index bias
    const shuffledScholars = shuffleArray([...scholars]);
    
    // Add global variables for animations
    let animationFrameId = null;
    let lastSpotlightTime = 0;
    let spotlightInterval = 2000; // 2 seconds
    let currentSpotlight = null;
    let isMouseOverMap = false;
    
    // Store all scholar groups for animation
    const scholarGroups = [];
    
    // Add scholar nodes to the map
    shuffledScholars.forEach(scholar => {
        if (!scholar.umap) return;
        
        const [x, y] = scholar.umap;
        const scaledX = scaleX(x);
        const scaledY = scaleY(y);
        
        // Get color based on cluster
        const clusterId = scholar.cluster_id || 0;
        const color = clusterColors[clusterId] || '#4a6fa5';
        
        // Create a group for this scholar
        const scholarGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        scholarGroup.setAttribute('class', 'scholar-group');
        scholarGroup.setAttribute('data-id', scholar.id);
        
        // Add original position data for animation
        scholarGroup.dataset.originalX = scaledX;
        scholarGroup.dataset.originalY = scaledY;
        scholarGroup.dataset.currentX = scaledX;
        scholarGroup.dataset.currentY = scaledY;
        
        // Random movement speed and direction
        scholarGroup.dataset.speedX = (Math.random() - 0.5) * 0.05;
        scholarGroup.dataset.speedY = (Math.random() - 0.5) * 0.05;
        
        // Create circle for scholar
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', scaledX);
        circle.setAttribute('cy', scaledY);
        circle.setAttribute('r', '6'); // Default size
        circle.setAttribute('fill', color);
        circle.setAttribute('class', 'scholar-node');
        circle.setAttribute('data-id', scholar.id);
        circle.setAttribute('data-name', scholar.name);
        circle.setAttribute('data-institution', scholar.institution || '');
        circle.setAttribute('data-country', scholar.country || '');
        circle.setAttribute('data-cluster', clusterId);
        
        // Create a clipPath for the profile image
        const clipPathId = `clip-${scholar.id}`;
        const clipPath = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath');
        clipPath.setAttribute('id', clipPathId);
        
        const clipCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        clipCircle.setAttribute('cx', scaledX);
        clipCircle.setAttribute('cy', scaledY);
        clipCircle.setAttribute('r', '22.5'); // Size for spotlight (1.5x larger than hover)
        clipPath.appendChild(clipCircle);
        
        // Add clipPath to defs
        let defs = svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
            svg.appendChild(defs);
        }
        defs.appendChild(clipPath);
        
        // Create image element for profile picture
        const profilePicPath = `data/profile_pics/${scholar.id}.jpg`;
        const image = document.createElementNS('http://www.w3.org/2000/svg', 'image');
        image.setAttribute('x', scaledX - 15);
        image.setAttribute('y', scaledY - 15);
        image.setAttribute('width', '30');
        image.setAttribute('height', '30');
        image.setAttribute('clip-path', `url(#${clipPathId})`);
        image.setAttribute('class', 'scholar-node-image');
        image.setAttributeNS('http://www.w3.org/1999/xlink', 'href', profilePicPath);
        
        // Add error handling for image
        image.addEventListener('error', () => {
            image.setAttributeNS('http://www.w3.org/1999/xlink', 'href', 'images/placeholder.jpg');
        });
        
        // Create text for scholar name
        const nameLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        nameLabel.setAttribute('x', scaledX);
        nameLabel.setAttribute('y', scaledY - 20); // Position above the node
        nameLabel.setAttribute('class', 'scholar-name-label');
        nameLabel.textContent = scholar.name;
        
        // Add elements to the group
        scholarGroup.appendChild(circle);
        scholarGroup.appendChild(image);
        scholarGroup.appendChild(nameLabel);
        
        // Add event listeners
        scholarGroup.addEventListener('click', () => {
            // Highlight selected scholar
            document.querySelectorAll('.scholar-node').forEach(node => {
                node.classList.remove('selected');
            });
            circle.classList.add('selected');
            
            // Show scholar details in the details panel
            showScholarDetails(scholar);
            
            // Add clicked class to this name label but don't remove clicked class from other labels
            nameLabel.classList.add('clicked');
            nameLabel.classList.add('visible');
        });
        
        scholarGroup.addEventListener('mouseenter', () => {
            // Enlarge the circle
            circle.setAttribute('r', '15');
            
            // Only show the name label, not the profile image
            nameLabel.classList.add('visible');
            
            // Bring this scholar to front
            scholarsGroup.appendChild(scholarGroup);
        });
        
        scholarGroup.addEventListener('mouseleave', () => {
            // Reset circle size
            circle.setAttribute('r', '6');
            
            // Hide the name label if it's not clicked
            if (!nameLabel.classList.contains('clicked')) {
                nameLabel.classList.remove('visible');
            }
        });
        
        scholarsGroup.appendChild(scholarGroup);
        scholarGroups.push(scholarGroup);
    });
    
    // Add mouse enter/leave detection for the map container
    mapContainer.addEventListener('mouseenter', () => {
        isMouseOverMap = true;
        
        // Reset current spotlight when mouse enters the map
        if (currentSpotlight) {
            const spotlightCircle = currentSpotlight.querySelector('circle');
            const spotlightImage = currentSpotlight.querySelector('image');
            const spotlightLabel = currentSpotlight.querySelector('text');
            
            if (spotlightCircle) spotlightCircle.setAttribute('r', '6');
            if (spotlightImage) spotlightImage.classList.remove('visible');
            if (spotlightLabel && !spotlightLabel.classList.contains('clicked')) {
                spotlightLabel.classList.remove('visible');
            }
            
            currentSpotlight = null;
        }
    });
    
    mapContainer.addEventListener('mouseleave', () => {
        isMouseOverMap = false;
        // Reset the spotlight timer to show a new spotlight immediately
        lastSpotlightTime = 0;
    });
    
    // Function to animate scholar nodes
    function animateScholars(timestamp) {
        // Animate slow movement
        scholarGroups.forEach(group => {
            // Skip animation for the current spotlight
            if (currentSpotlight === group) return;
            
            // Get current position
            let x = parseFloat(group.dataset.currentX);
            let y = parseFloat(group.dataset.currentY);
            
            // Get original position
            const originalX = parseFloat(group.dataset.originalX);
            const originalY = parseFloat(group.dataset.originalY);
            
            // Get speed
            const speedX = parseFloat(group.dataset.speedX);
            const speedY = parseFloat(group.dataset.speedY);
            
            // Update position with small random movement
            x += speedX;
            y += speedY;
            
            // Limit movement to a small area around original position
            const maxDistance = 5;
            const dx = x - originalX;
            const dy = y - originalY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance > maxDistance) {
                // Reverse direction with a small random change
                group.dataset.speedX = -speedX * (0.9 + Math.random() * 0.2);
                group.dataset.speedY = -speedY * (0.9 + Math.random() * 0.2);
                
                // Move back toward original position
                x = x - (dx / distance) * 0.5;
                y = y - (dy / distance) * 0.5;
            }
            
            // Occasionally change direction slightly
            if (Math.random() < 0.01) {
                group.dataset.speedX = parseFloat(group.dataset.speedX) + (Math.random() - 0.5) * 0.02;
                group.dataset.speedY = parseFloat(group.dataset.speedY) + (Math.random() - 0.5) * 0.02;
            }
            
            // Update position
            group.dataset.currentX = x;
            group.dataset.currentY = y;
            
            // Update elements
            const circle = group.querySelector('circle');
            const image = group.querySelector('image');
            const nameLabel = group.querySelector('text');
            
            if (circle) {
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
            }
            
            if (image) {
                image.setAttribute('x', x - 15); // Half of the image width (30)
                image.setAttribute('y', y - 15); // Half of the image height (30)
            }
            
            if (nameLabel) {
                nameLabel.setAttribute('x', x);
                nameLabel.setAttribute('y', y - 20);
            }
            
            // Update clipPath if it exists
            const clipPathId = group.querySelector('image')?.getAttribute('clip-path')?.match(/url\(#(.*)\)/)?.[1];
            if (clipPathId) {
                const clipCircle = document.querySelector(`#${clipPathId} circle`);
                if (clipCircle) {
                    clipCircle.setAttribute('cx', x);
                    clipCircle.setAttribute('cy', y);
                }
            }
        });
        
        // Handle spotlight feature when mouse is not over the map
        if (!isMouseOverMap) {
            if (timestamp - lastSpotlightTime > spotlightInterval) {
                // Reset previous spotlight
                if (currentSpotlight) {
                    const prevCircle = currentSpotlight.querySelector('circle');
                    const prevImage = currentSpotlight.querySelector('image');
                    const prevLabel = currentSpotlight.querySelector('text');
                    
                    if (prevCircle) prevCircle.setAttribute('r', '6');
                    if (prevImage) prevImage.classList.remove('visible');
                    if (prevLabel && !prevLabel.classList.contains('clicked')) {
                        prevLabel.classList.remove('visible');
                    }
                }
                
                // Pick a random scholar for spotlight
                const randomIndex = Math.floor(Math.random() * scholarGroups.length);
                currentSpotlight = scholarGroups[randomIndex];
                
                // Highlight the spotlight scholar with larger size (1.5x)
                const spotlightCircle = currentSpotlight.querySelector('circle');
                const spotlightImage = currentSpotlight.querySelector('image');
                const spotlightLabel = currentSpotlight.querySelector('text');
                
                // Make the spotlight 1.5 times larger (22.5 instead of 15)
                if (spotlightCircle) spotlightCircle.setAttribute('r', '22.5');
                
                // Update image size and position for the larger spotlight
                if (spotlightImage) {
                    spotlightImage.setAttribute('width', '45'); // 1.5x larger
                    spotlightImage.setAttribute('height', '45'); // 1.5x larger
                    spotlightImage.setAttribute('x', parseFloat(currentSpotlight.dataset.currentX) - 22.5);
                    spotlightImage.setAttribute('y', parseFloat(currentSpotlight.dataset.currentY) - 22.5);
                    spotlightImage.classList.add('visible');
                }
                
                // Update clipPath for the larger image
                const clipPathId = spotlightImage?.getAttribute('clip-path')?.match(/url\(#(.*)\)/)?.[1];
                if (clipPathId) {
                    const clipCircle = document.querySelector(`#${clipPathId} circle`);
                    if (clipCircle) {
                        clipCircle.setAttribute('r', '22.5');
                    }
                }
                
                // Make the label larger and position it higher
                if (spotlightLabel) {
                    spotlightLabel.style.fontSize = '16px';
                    spotlightLabel.style.fontWeight = '700';
                    spotlightLabel.setAttribute('y', parseFloat(currentSpotlight.dataset.currentY) - 30);
                    spotlightLabel.classList.add('visible');
                }
                
                // Bring to front
                scholarsGroup.appendChild(currentSpotlight);
                
                // Update timestamp
                lastSpotlightTime = timestamp;
            }
        }
        
        // Continue animation
        animationFrameId = requestAnimationFrame(animateScholars);
    }
    
    // Start animation
    animationFrameId = requestAnimationFrame(animateScholars);
    
    // Clean up animation when needed
    mapContainer.addEventListener('remove', () => {
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }
    });
    
    // Set up zoom and pan functionality
    let currentZoom = 1;
    let currentTranslate = { x: 0, y: 0 };
    
    // Zoom in button
    document.getElementById('zoom-in').addEventListener('click', () => {
        currentZoom *= 1.2;
        applyTransform();
    });
    
    // Zoom out button
    document.getElementById('zoom-out').addEventListener('click', () => {
        currentZoom /= 1.2;
        if (currentZoom < 0.1) currentZoom = 0.1;
        applyTransform();
    });
    
    // Reset view button
    document.getElementById('reset-view').addEventListener('click', () => {
        currentZoom = 1;
        currentTranslate = { x: 0, y: 0 };
        applyTransform();
    });
    
    // Apply transform to scholar group
    function applyTransform() {
        const transform = `translate(${currentTranslate.x}px, ${currentTranslate.y}px) scale(${currentZoom})`;
        scholarsGroup.style.transform = transform;
        labelsGroup.style.transform = transform;
        
        // Update label visibility based on zoom level
        updateLabelVisibility();
    }
    
    // Add function to update label visibility based on zoom level
    function updateLabelVisibility() {
        // Don't automatically show labels based on zoom level
        // Only show labels for clicked scholars
        
        // If we're at a very high zoom level, we might want to show labels
        // but we'll leave this commented out as per the user's request
        /*
        if (currentZoom > 3) {
            document.querySelectorAll('.scholar-name-label').forEach(label => {
                label.classList.add('visible');
            });
        }
        */
    }
    
    // Shuffle array function
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }
    
    // Set up drag functionality
    let isDragging = false;
    let dragStart = { x: 0, y: 0 };
    
    // Add rectangle selection for zooming
    let isSelecting = false;
    let selectionStart = { x: 0, y: 0 };
    let selectionRect = null;
    
    // Create selection rectangle element
    const createSelectionRect = () => {
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('class', 'selection-rect');
        rect.setAttribute('fill', 'rgba(74, 111, 165, 0.2)');
        rect.setAttribute('stroke', 'rgba(74, 111, 165, 0.8)');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('pointer-events', 'none');
        return rect;
    };
    
    // Handle mousedown for both dragging and selection
    mapContainer.addEventListener('mousedown', (e) => {
        console.log('mousedown event', e.target);
        // Start selection if clicking on the SVG or scholars group
        if (e.target === svg || e.target.classList.contains('scholar-node') || e.target === scholarsGroup) {
            console.log('Starting selection');
            isSelecting = true;
            isDragging = false; // Ensure dragging is disabled when selecting
            
            // Get the exact cursor position relative to the SVG element
            const svgRect = svg.getBoundingClientRect();
            selectionStart = { 
                x: e.clientX - svgRect.left, 
                y: e.clientY - svgRect.top 
            };
            console.log('Selection start', selectionStart);
            
            // Create selection rectangle
            selectionRect = createSelectionRect();
            selectionRect.setAttribute('x', selectionStart.x);
            selectionRect.setAttribute('y', selectionStart.y);
            selectionRect.setAttribute('width', 0);
            selectionRect.setAttribute('height', 0);
            svg.appendChild(selectionRect);
            
            e.preventDefault();
        } else if (e.target === svg || e.target === scholarsGroup) {
            console.log('Starting dragging');
            isDragging = true;
            isSelecting = false; // Ensure selecting is disabled when dragging
            dragStart = { x: e.clientX, y: e.clientY };
            mapContainer.style.cursor = 'grabbing';
        }
    });
    
    // Handle mousemove for both dragging and selection
    document.addEventListener('mousemove', (e) => {
        if (isSelecting && selectionRect) {
            // Get the exact cursor position relative to the SVG element
            const svgRect = svg.getBoundingClientRect();
            const currentX = e.clientX - svgRect.left;
            const currentY = e.clientY - svgRect.top;
            
            const width = currentX - selectionStart.x;
            const height = currentY - selectionStart.y;
            
            // Update rectangle dimensions
            if (width < 0) {
                selectionRect.setAttribute('x', currentX);
                selectionRect.setAttribute('width', -width);
            } else {
                selectionRect.setAttribute('width', width);
            }
            
            if (height < 0) {
                selectionRect.setAttribute('y', currentY);
                selectionRect.setAttribute('height', -height);
            } else {
                selectionRect.setAttribute('height', height);
            }
        }
        else if (isDragging) {
            const dx = e.clientX - dragStart.x;
            const dy = e.clientY - dragStart.y;
            
            currentTranslate.x += dx;
            currentTranslate.y += dy;
            
            applyTransform();
            
            dragStart = { x: e.clientX, y: e.clientY };
        }
    });
    
    // Handle mouseup for both dragging and selection
    document.addEventListener('mouseup', (e) => {
        console.log('mouseup event', isSelecting, selectionRect);
        if (isSelecting && selectionRect) {
            // Get the selection rectangle dimensions
            const x = parseFloat(selectionRect.getAttribute('x'));
            const y = parseFloat(selectionRect.getAttribute('y'));
            const width = parseFloat(selectionRect.getAttribute('width'));
            const height = parseFloat(selectionRect.getAttribute('height'));
            
            console.log('Selection dimensions', x, y, width, height);
            
            // Only process if the selection has a meaningful size
            if (width > 10 && height > 10) {
                console.log('Processing selection');
                // Find scholars in the selected area
                showScholarsInSelectedArea(x, y, width, height);
            }
            
            // Remove the selection rectangle
            svg.removeChild(selectionRect);
            selectionRect = null;
        }
        
        isSelecting = false;
        isDragging = false;
        mapContainer.style.cursor = 'default';
    });

    // Function to show scholars in the selected area
    function showScholarsInSelectedArea(x, y, width, height) {
        console.log('Showing scholars in selected area', x, y, width, height);
        // Get all scholar nodes
        const scholarNodes = document.querySelectorAll('.scholar-node');
        const selectedScholars = [];
        
        // Calculate the selection bounds in SVG coordinates
        const x1 = x;
        const y1 = y;
        const x2 = x + width;
        const y2 = y + height;
        
        console.log('Selection bounds', x1, y1, x2, y2);
        
        // Find scholars within the selection rectangle
        scholarNodes.forEach(node => {
            const cx = parseFloat(node.getAttribute('cx'));
            const cy = parseFloat(node.getAttribute('cy'));
            const scholarId = node.getAttribute('data-id');
            
            // Check if the scholar is within the selection bounds
            if (cx >= x1 && cx <= x2 && cy >= y1 && cy <= y2) {
                // Find the scholar data
                const scholar = window.scholarsData.find(s => String(s.id) === String(scholarId));
                if (scholar) {
                    selectedScholars.push(scholar);
                }
            }
        });
        
        console.log('Found scholars in selected area', selectedScholars.length);
        
        // Display the selected scholars in the sidebar
        displaySelectedScholars(selectedScholars);
    }
    
    // Function to display selected scholars in the sidebar
    function displaySelectedScholars(scholars) {
        const detailsContainer = document.getElementById('scholar-details');
        
        if (!detailsContainer) {
            console.error('Scholar details container not found');
            return;
        }
        
        if (scholars.length === 0) {
            detailsContainer.innerHTML = `
                <div class="selected-scholars-list">
                    <h3>Selected Area</h3>
                    <p class="no-scholars">No scholars found in the selected area</p>
                </div>
            `;
            return;
        }
        
        // Sort scholars by name
        scholars.sort((a, b) => a.name.localeCompare(b.name));
        
        // Create HTML for the scholars list
        let scholarsListHtml = `
            <div class="selected-scholars-list">
                <h3>Selected Area (${scholars.length} scholars)</h3>
                <ul class="scholars-list">
        `;
        
        scholars.forEach(scholar => {
            scholarsListHtml += `
                <li class="scholar-list-item" data-id="${scholar.id}">
                    <div class="scholar-list-name">${scholar.name}</div>
                    <div class="scholar-list-institution">${scholar.institution || 'Unknown Institution'}</div>
                </li>
            `;
        });
        
        scholarsListHtml += `
                </ul>
            </div>
        `;
        
        // Update the sidebar content
        detailsContainer.innerHTML = scholarsListHtml;
        
        // Add click event listeners to the scholar list items
        document.querySelectorAll('.scholar-list-item').forEach(item => {
            item.addEventListener('click', () => {
                const scholarId = item.getAttribute('data-id');
                const scholar = window.scholarsData.find(s => String(s.id) === String(scholarId));
                if (scholar) {
                    showScholarDetails(scholar);
                }
            });
        });
    }
    
    // Update wheel zoom to be smoother
    mapContainer.addEventListener('wheel', (e) => {
        e.preventDefault();
        
        // Get mouse position relative to container
        const rect = mapContainer.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Calculate zoom factor - make it smoother by reducing the zoom step
        const zoomFactor = e.deltaY < 0 ? 1.05 : 0.95;
        
        // Calculate the point under the mouse in the current transformed space
        const pointBeforeZoom = {
            x: (mouseX - currentTranslate.x) / currentZoom,
            y: (mouseY - currentTranslate.y) / currentZoom
        };
        
        // Apply zoom
        currentZoom *= zoomFactor;
        
        // Limit zoom range for better user experience
        if (currentZoom < 0.2) currentZoom = 0.2;
        if (currentZoom > 8) currentZoom = 8;
        
        // Calculate the point under the mouse in the new transformed space
        const pointAfterZoom = {
            x: (mouseX - currentTranslate.x) / currentZoom,
            y: (mouseY - currentTranslate.y) / currentZoom
        };
        
        // Adjust translation to keep the point under the mouse fixed
        currentTranslate.x += (pointAfterZoom.x - pointBeforeZoom.x) * currentZoom;
        currentTranslate.y += (pointAfterZoom.y - pointBeforeZoom.y) * currentZoom;
        
        // Apply transform
        applyTransform();
    });
}

// Add a global variable to track the current view state
let currentViewState = 'profile'; // Can be 'profile' or 'vicinity'

/**
 * Show scholar details in the sidebar
 */
function showScholarDetails(scholar) {
    console.log(`Showing details for scholar: ${scholar.name}`);
    
    // Store the selected scholar globally
    selectedScholar = scholar;
    
    // Set the current view state to profile
    currentViewState = 'profile';
    
    // Get the sidebar and details container
    const sidebar = document.getElementById('sidebar');
    const detailsContainer = document.getElementById('scholar-details');
    
    // Show the sidebar
    sidebar.classList.add('active');
    
    // Show loading indicator
    detailsContainer.innerHTML = `
        <div class="loading-indicator">
            <div class="spinner"></div>
            <p>Loading scholar profile...</p>
        </div>
    `;
    
    // Fetch scholar profile data
    fetch(`/api/scholar/${scholar.id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch scholar profile: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Fetched scholar profile:', data);
            
            // Create HTML for the scholar profile
            const profileHtml = `
                <div class="scholar-profile">
                    <div class="profile-header">
                        <div class="profile-image">
                            <img src="${data.profile_pic}" alt="${data.name}" onerror="this.src='images/placeholder.jpg'">
                        </div>
                        <div class="profile-info">
                            <h3>${data.name}</h3>
                            <div class="institution">${data.institution || 'Unknown Institution'}</div>
                            <button id="show-vicinity-button" class="show-vicinity-button">
                                <i class="fas fa-users"></i> Show Vicinity
                            </button>
                        </div>
                    </div>
                    <div class="profile-content">
                        <div class="markdown-content">
                            ${formatMarkdown(data.markdown_content)}
                        </div>
                    </div>
                </div>
            `;
            
            // Update the sidebar content
            detailsContainer.innerHTML = profileHtml;
            
            // Set up markdown interactions
            setupMarkdownInteractions();
            
            // Add click event listener to the Show Vicinity button
            const vicinityButton = document.getElementById('show-vicinity-button');
            if (vicinityButton) {
                vicinityButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Show vicinity button clicked');
                    showVicinityScholars(scholar.id);
                });
            }
            
            // Highlight the scholar node on the map
            highlightScholarNode(scholar.id);
        })
        .catch(error => {
            console.error('Error fetching scholar profile:', error);
            
            // Show error message
            detailsContainer.innerHTML = `
                <div class="error-message">
                    <p>Failed to load scholar profile</p>
                    <div class="error-details">${error.message}</div>
                </div>
            `;
        });
}

/**
 * Center the map on a scholar
 */
function centerMapOnScholar(scholar) {
    // Get the map container and SVG
    const mapContainer = document.getElementById('scholar-map');
    const svg = mapContainer.querySelector('svg');
    
    if (!svg) {
        console.error('SVG not found in map container');
        return;
    }
    
    // Find the scholar node
    const scholarNode = svg.querySelector(`.scholar-node[data-id="${scholar.id}"]`);
    
    if (!scholarNode) {
        console.error(`Scholar node not found for ID: ${scholar.id}`);
        return;
    }
    
    // Get the scholar's position
    const scholarX = parseFloat(scholarNode.getAttribute('cx'));
    const scholarY = parseFloat(scholarNode.getAttribute('cy'));
    
    // Get the current transform values
    const transform = svg.__zoom || { k: 1, x: 0, y: 0 };
    
    // Calculate the center position
    const width = mapContainer.clientWidth;
    const height = mapContainer.clientHeight;
    
    // Calculate the new transform to center on the scholar
    const scale = Math.max(1.5, transform.k); // Zoom in a bit more than current level
    const x = width / 2 - scholarX * scale;
    const y = height / 2 - scholarY * scale;
    
    // Apply the transform with a smooth transition
    d3.select(svg)
        .transition()
        .duration(750)
        .call(
            d3.zoom().transform,
            d3.zoomIdentity.translate(x, y).scale(scale)
        );
}

/**
 * Highlight a scholar node on the map
 */
function highlightScholarNode(scholarId) {
    // Get the map container and SVG
    const mapContainer = document.getElementById('scholar-map');
    const svg = mapContainer.querySelector('svg');
    
    if (!svg) {
        console.error('SVG not found in map container');
        return;
    }
    
    // Remove highlight from all nodes
    svg.querySelectorAll('.scholar-node').forEach(node => {
        node.classList.remove('selected');
        node.classList.remove('highlight-pulse');
    });
    
    // Find the scholar node
    const scholarNode = svg.querySelector(`.scholar-node[data-id="${scholarId}"]`);
    
    if (!scholarNode) {
        console.error(`Scholar node not found for ID: ${scholarId}`);
        return;
    }
    
    // Add highlight to the scholar node
    scholarNode.classList.add('selected');
    scholarNode.classList.add('highlight-pulse');
    
    // Bring the node to the front
    scholarNode.parentNode.appendChild(scholarNode);
}

function formatMarkdown(markdown) {
    if (!markdown) return '';
    
    // Split the markdown into sections based on ## headers
    const sections = markdown.split(/^## /m);
    
    // Process the first part (if any) before any ## headers
    let formatted = '';
    if (sections[0] && !sections[0].startsWith('#')) {
        formatted = processMarkdownSection(sections[0]);
    }
    
    // Process each section with ## headers
    for (let i = 1; i < sections.length; i++) {
        const section = sections[i];
        const sectionLines = section.split('\n');
        const sectionTitle = sectionLines[0];
        const sectionContent = sectionLines.slice(1).join('\n');
        
        formatted += `<h4>${sectionTitle}</h4>`;
        formatted += `<div class="section-content">${processMarkdownSection(sectionContent)}</div>`;
    }
    
    return formatted;
}

function processMarkdownSection(content) {
    if (!content.trim()) return '';
    
    let processed = content;
    
    // Process ### headers
    processed = processed.replace(/^### (.*?)$/gm, '<h5>$1</h5>');
    
    // Process # headers
    processed = processed.replace(/^# (.*?)$/gm, '<h3>$1</h3>');
    
    // Process bold text (both ** and __ formats)
    processed = processed
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Process links
    processed = processed.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Improved bullet point processing
    // First, identify bullet point sections
    let lines = processed.split('\n');
    let inList = false;
    let listContent = '';
    let result = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Match both * and - at the beginning of a line with proper spacing
        const isBullet = line.match(/^[\*\-]\s+(.+)$/);
        
        // Also match single asterisks that are not part of bold/italic formatting
        const isSingleAsterisk = !isBullet && line.match(/^\*\s+(.+)$/);
        
        if (isBullet || isSingleAsterisk) {
            if (!inList) {
                inList = true;
                listContent = '<ul>';
            }
            // Extract the bullet content and add proper formatting
            const bulletContent = isBullet ? isBullet[1] : isSingleAsterisk[1];
            
            // Process any inline formatting within the bullet point
            let formattedBulletContent = bulletContent
                // Process bold within bullet
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/__(.*?)__/g, '<strong>$1</strong>')
                // Process highlight text (single asterisks that are part of inline formatting)
                .replace(/\*([^\*]+)\*/g, '<span class="highlight-text">$1</span>')
                .replace(/_([^_]+)_/g, '<span class="highlight-text">$1</span>');
                
            listContent += `<li>${formattedBulletContent}</li>`;
        } else {
            if (inList) {
                // Close the list and add it to the result
                listContent += '</ul>';
                result.push(listContent);
                inList = false;
                listContent = '';
            }
            
            // Process non-bullet lines
            if (line && !line.startsWith('<h')) {
                // Process italic text (both * and _ formats) for non-bullet lines
                let formattedLine = line
                    .replace(/\*([^\*]+)\*/g, '<span class="highlight-text">$1</span>')
                    .replace(/_([^_]+)_/g, '<span class="highlight-text">$1</span>');
                
                result.push(`<p>${formattedLine}</p>`);
            } else if (line) {
                result.push(line);
            }
        }
    }
    
    // Handle case where list is at the end of content
    if (inList) {
        listContent += '</ul>';
        result.push(listContent);
    }
    
    // Join all processed parts
    processed = result.join('\n');
    
    // Fix empty paragraphs
    processed = processed.replace(/<p>\s*<\/p>/g, '');
    
    // Fix consecutive paragraph tags
    processed = processed.replace(/<\/p>\s*<p>/g, '</p><p>');
    
    return processed;
}

function setupMarkdownInteractions() {
    const headers = document.querySelectorAll('.markdown-content h4');
    
    headers.forEach((header, index) => {
        // Check if toggle icon exists, if not, add it
        let toggleIcon = header.querySelector('.toggle-icon');
        if (!toggleIcon) {
            toggleIcon = document.createElement('span');
            toggleIcon.className = 'toggle-icon';
            toggleIcon.textContent = index === 0 ? '▼' : '▶';
            header.appendChild(toggleIcon);
        }
        
        // Get the next element after the header
        const content = header.nextElementSibling;
        
        // Skip if there's no content to toggle
        if (!content || !content.classList.contains('section-content')) return;
        
        // Make the first section (Lab/Research Area) open by default
        // and ensure all others are closed
        if (index === 0) {
            content.style.display = 'block';
            toggleIcon.textContent = '▼';
        } else {
            content.style.display = 'none';
            toggleIcon.textContent = '▶';
        }
        
        header.addEventListener('click', () => {
            const isVisible = content.style.display === 'block';
            content.style.display = isVisible ? 'none' : 'block';
            toggleIcon.textContent = isVisible ? '▶' : '▼';
        });
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

function setupFilters(scholars) {
    const filterToggle = document.getElementById('filter-toggle');
    const filterDropdown = document.querySelector('.filter-dropdown');
    const filterOptions = document.getElementById('filter-options');
    const applyButton = document.getElementById('apply-filters');
    const clearButton = document.getElementById('clear-filters');
    
    // Toggle filter dropdown
    if (filterToggle) {
        filterToggle.addEventListener('click', () => {
            filterDropdown.classList.toggle('active');
            filterToggle.classList.toggle('active');
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.filter-container') && filterDropdown) {
            filterDropdown.classList.remove('active');
            if (filterToggle) filterToggle.classList.remove('active');
        }
    });
    
    // Populate initial filter options (institution only)
    populateFilterOptions(scholars, 'institution');
    
    // Apply filters button
    if (applyButton) {
        applyButton.addEventListener('click', () => {
            applyFilters(scholars);
            filterDropdown.classList.remove('active');
            if (filterToggle) filterToggle.classList.remove('active');
        });
    }
    
    // Clear filters button
    if (clearButton) {
        clearButton.addEventListener('click', () => {
            // Uncheck all checkboxes
            const checkboxes = filterOptions.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            
            // Apply filters (will show all scholars)
            applyFilters(scholars);
        });
    }
    
    // Function to populate filter options
    function populateFilterOptions(scholars, type) {
        // Clear existing options
        filterOptions.innerHTML = '';
        
        // Get unique values for institutions
        const values = new Map();
        
        scholars.forEach(scholar => {
            const value = scholar.institution || 'Unknown';
            
            if (value) {
                if (values.has(value)) {
                    values.set(value, values.get(value) + 1);
                } else {
                    values.set(value, 1);
                }
            }
        });
        
        // Sort values by count (descending)
        const sortedValues = [...values.entries()].sort((a, b) => b[1] - a[1]);
        
        // Create filter options
        sortedValues.forEach(([value, count]) => {
            const option = document.createElement('div');
            option.className = 'filter-option';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `filter-${type}-${value.replace(/\s+/g, '-').toLowerCase()}`;
            checkbox.value = value;
            
            option.appendChild(checkbox);
            option.appendChild(document.createTextNode(value));
            filterOptions.appendChild(option);
        });
    }
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

// Function to show scholars in the vicinity of a selected scholar
function showVicinityScholars(scholarId) {
    console.log(`Showing scholars in vicinity of scholar ${scholarId}`);
    
    // Set the current view state to vicinity
    currentViewState = 'vicinity';
    
    // Get all scholars
    const scholars = window.scholarsData;
    if (!scholars) {
        console.error('Scholar data not available');
        return;
    }
    
    // Find the selected scholar
    const selectedScholar = scholars.find(s => String(s.id) === String(scholarId));
    if (!selectedScholar) {
        console.error('Selected scholar not found');
        return;
    }
    
    console.log(`Found selected scholar: ${selectedScholar.name}`);
    
    // Calculate Euclidean distance to all other scholars
    const scholarsWithDistance = scholars
        .filter(s => s.id !== selectedScholar.id) // Exclude the selected scholar
        .map(scholar => {
            // Calculate Euclidean distance between UMAP coordinates
            const dx = scholar.umap[0] - selectedScholar.umap[0];
            const dy = scholar.umap[1] - selectedScholar.umap[1];
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            return {
                scholar,
                distance
            };
        })
        .sort((a, b) => a.distance - b.distance); // Sort by distance (ascending)
    
    // Get the top 5 closest scholars
    const vicinityScholars = scholarsWithDistance.slice(0, 5).map(item => item.scholar);
    console.log(`Found ${vicinityScholars.length} scholars in vicinity of ${selectedScholar.name}`);
    
    // Display the vicinity scholars in the sidebar
    const sidebar = document.getElementById('sidebar');
    const detailsContainer = document.getElementById('scholar-details');
    const mapContainer = document.getElementById('map-container');
    
    if (!detailsContainer) {
        console.error('Scholar details container not found');
        return;
    }
    
    // Force the sidebar to be visible and maintain the same layout
    if (sidebar) {
        sidebar.style.display = 'flex';
        sidebar.style.width = '50%';
        sidebar.classList.add('active');
    }
    
    console.log('Updating sidebar with vicinity scholars');
    
    // Create HTML for the vicinity scholars list with more prominent styling
    let vicinityListHtml = `
        <div class="selected-scholars-list" style="width: 100%; box-sizing: border-box; margin-top: 0;">
            <h3 style="color: #4a6fa5; font-size: 20px; margin-bottom: 15px;">Scholars Near ${selectedScholar.name} (${vicinityScholars.length})</h3>
            <ul class="scholars-list" style="max-height: 400px; overflow-y: auto; margin-bottom: 15px; padding: 0;">
    `;
    
    vicinityScholars.forEach(scholar => {
        vicinityListHtml += `
            <li class="scholar-list-item" data-id="${scholar.id}" style="padding: 12px; margin-bottom: 10px; background-color: #f5f8ff; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; border: 1px solid #e0e0e0;">
                <div class="scholar-list-name" style="font-weight: 600; color: #333; margin-bottom: 5px;">${scholar.name}</div>
                <div class="scholar-list-institution" style="font-size: 13px; color: #666;">${scholar.institution || 'Unknown Institution'}</div>
            </li>
        `;
    });
    
    vicinityListHtml += `
            </ul>
            <button id="back-to-scholar" class="show-vicinity-button" style="width: 100%; margin-top: 15px; background-color: #4a6fa5; color: white; border: none; border-radius: 4px; padding: 10px; font-size: 14px; cursor: pointer;">
                <i class="fas fa-arrow-left"></i> Back to Scholar
            </button>
        </div>
    `;
    
    // Update the sidebar content with the vicinity scholars list
    detailsContainer.innerHTML = vicinityListHtml;
    console.log('Sidebar updated with vicinity scholars');
    
    // Add click event listeners to the scholar list items
    document.querySelectorAll('.scholar-list-item').forEach(item => {
        item.addEventListener('click', () => {
            const scholarId = item.getAttribute('data-id');
            const scholar = window.scholarsData.find(s => String(s.id) === String(scholarId));
            if (scholar) {
                showScholarDetails(scholar);
            }
        });
    });
    
    // Add click event listener to the back button
    const backButton = detailsContainer.querySelector('#back-to-scholar');
    if (backButton) {
        backButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Back to scholar button clicked');
            // Set the current view state back to profile before showing scholar details
            currentViewState = 'profile';
            showScholarDetails(selectedScholar);
        });
    }
    
    // Add a notification to indicate the vicinity view is active
    const notification = document.createElement('div');
    notification.className = 'vicinity-notification';
    notification.style.cssText = 'position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background-color: #4a6fa5; color: white; border-radius: 8px; padding: 10px 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000;';
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-info-circle"></i>
            <span>Showing scholars near ${selectedScholar.name}</span>
        </div>
    `;
    document.body.appendChild(notification);
    
    // Remove the notification after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

/**
 * Set up search functionality
 */
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.querySelector('.search-results');
    const searchTypeOptions = document.querySelectorAll('input[name="search-type"]');
    
    if (!searchInput || !searchButton || !searchResults) {
        console.error('Search elements not found in the DOM');
        return;
    }
    
    console.log('Setting up search functionality');
    
    // Track current search type
    let currentSearchType = 'name'; // Default to name search
    
    // Listen for search type changes
    searchTypeOptions.forEach(option => {
        option.addEventListener('change', (e) => {
            currentSearchType = e.target.value;
            console.log(`Search type changed to: ${currentSearchType}`);
            
            // Update placeholder text based on search type
            if (currentSearchType === 'name') {
                searchInput.placeholder = 'Search for scholars by name...';
                
                // Trigger instant search if there's already text in the input
                const query = searchInput.value.trim();
                if (query.length >= 3) {
                    performInstantSearch(query);
                }
            } else {
                searchInput.placeholder = 'Describe a research topic...';
                // Hide search results when switching to research search
                searchResults.classList.remove('active');
            }
        });
    });
    
    // Function to perform instant search for scholar names
    const performInstantSearch = async (query) => {
        if (currentSearchType !== 'name' || query.length < 3) return;
        
        console.log(`Performing instant name search for: ${query}`);
        
        try {
            // Show loading state
            searchResults.innerHTML = '<div class="search-no-results">Searching...</div>';
            searchResults.classList.add('active');
            
            // Get all scholars
            const scholars = window.scholarsData;
            if (!scholars || scholars.length === 0) {
                console.error('Scholar data not available for instant search');
                searchResults.innerHTML = '<div class="search-no-results">Scholar data not available</div>';
                return;
            }
            
            // Filter scholars by name (case-insensitive)
            const queryLower = query.toLowerCase();
            const matchingScholars = scholars
                .filter(scholar => scholar.name.toLowerCase().includes(queryLower))
                .slice(0, 10); // Limit to 10 results
            
            // Display results
            displayScholarSearchResults(matchingScholars, query);
            
        } catch (error) {
            console.error('Error performing instant search:', error);
            searchResults.innerHTML = `<div class="search-no-results">Error: ${error.message}</div>`;
        }
    };
    
    // Function to perform search
    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) return;
        
        console.log(`Performing ${currentSearchType} search for: ${query}`);
        
        // For name search with 3+ characters, we already have results from instant search
        if (currentSearchType === 'name' && query.length >= 3) {
            // Results are already displayed by instant search
            return;
        }
        
        try {
            // Show loading state
            searchResults.innerHTML = '<div class="search-no-results">Searching...</div>';
            searchResults.classList.add('active');
            
            // Prepare request data
            const requestData = {
                type: currentSearchType,
                query: query
            };
            
            console.log('Sending search request:', requestData);
            
            // Send search request to server
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Search request failed: ${response.status} ${response.statusText}`, errorText);
                throw new Error(`Search request failed: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Search results:', data);
            
            // Handle different types of search results
            if (currentSearchType === 'name') {
                displayScholarSearchResults(data.results, query);
            } else if (currentSearchType === 'research') {
                // Hide search results
                searchResults.classList.remove('active');
                
                // Display research pin on map
                displayResearchPin(data.coords, query);
            }
        } catch (error) {
            console.error('Error performing search:', error);
            searchResults.innerHTML = `<div class="search-no-results">Error: ${error.message}</div>`;
        }
    };
    
    // Add event listeners
    searchButton.addEventListener('click', (e) => {
        e.preventDefault();
        performSearch();
    });
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
    
    // Add input event listener for instant search
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        
        // Only perform instant search for name search with 3+ characters
        if (currentSearchType === 'name' && query.length >= 3) {
            performInstantSearch(query);
        } else if (query.length < 3) {
            // Hide search results if query is too short
            searchResults.classList.remove('active');
        }
    });
    
    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            searchResults.classList.remove('active');
        }
    });
    
    console.log('Search functionality set up successfully');
}

/**
 * Display scholar search results
 */
function displayScholarSearchResults(scholars, query) {
    const searchResults = document.querySelector('.search-results');
    
    if (!scholars || scholars.length === 0) {
        searchResults.innerHTML = '<div class="search-no-results">No scholars found</div>';
        return;
    }
    
    // Create HTML for search results
    let resultsHtml = '';
    
    scholars.forEach(scholar => {
        // Highlight the matching part of the name
        const name = scholar.name;
        const lowerName = name.toLowerCase();
        const lowerQuery = query.toLowerCase();
        const index = lowerName.indexOf(lowerQuery);
        
        let highlightedName = name;
        
        if (index !== -1) {
            const before = name.substring(0, index);
            const match = name.substring(index, index + query.length);
            const after = name.substring(index + query.length);
            highlightedName = `${before}<span class="search-result-highlight">${match}</span>${after}`;
        }
        
        resultsHtml += `
            <div class="search-result-item" data-id="${scholar.id}">
                <div class="search-result-image">
                    <img src="data/profile_pics/${scholar.id}.jpg" onerror="this.src='images/placeholder.jpg'" alt="${name}">
                </div>
                <div class="search-result-info">
                    <div class="search-result-name">${highlightedName}</div>
                    <div class="search-result-institution">${scholar.institution || 'Unknown Institution'}</div>
                </div>
            </div>
        `;
    });
    
    // Update search results
    searchResults.innerHTML = resultsHtml;
    searchResults.classList.add('active');
    
    // Add click event listeners to search results
    document.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
            const scholarId = item.getAttribute('data-id');
            const scholar = window.scholarsData.find(s => String(s.id) === String(scholarId));
            
            if (scholar) {
                // Hide search results
                searchResults.classList.remove('active');
                
                // Highlight the scholar on the map
                highlightScholar(scholar);
                
                // Show scholar details
                showScholarDetails(scholar);
            }
        });
    });
}

/**
 * Highlight a scholar on the map
 */
function highlightScholar(scholar) {
    // Get the map container and SVG
    const mapContainer = document.getElementById('scholar-map');
    const svg = mapContainer.querySelector('svg');
    
    if (!svg) {
        console.error('SVG not found in map container');
        return;
    }
    
    // Get the scholar node
    const scholarNode = svg.querySelector(`.scholar-node[data-id="${scholar.id}"]`);
    
    if (!scholarNode) {
        console.error(`Scholar node not found for ID: ${scholar.id}`);
        return;
    }
    
    // Calculate the position to center the map on the scholar
    const scholarX = parseFloat(scholarNode.getAttribute('cx'));
    const scholarY = parseFloat(scholarNode.getAttribute('cy'));
    
    // Get the current transform values
    const transform = svg.__zoom || { k: 1, x: 0, y: 0 };
    
    // Calculate the center position
    const width = mapContainer.clientWidth;
    const height = mapContainer.clientHeight;
    
    // Calculate the new transform to center on the scholar
    const scale = Math.max(1, transform.k); // Keep at least the current zoom level
    const x = width / 2 - scholarX * scale;
    const y = height / 2 - scholarY * scale;
    
    // Apply the transform with a smooth transition
    d3.select(svg)
        .transition()
        .duration(750)
        .call(
            d3.zoom().transform,
            d3.zoomIdentity.translate(x, y).scale(scale)
        );
    
    // Add a pulse animation to the scholar node
    scholarNode.classList.add('highlight-pulse');
    
    // Remove the pulse animation after it completes
    setTimeout(() => {
        scholarNode.classList.remove('highlight-pulse');
    }, 2000);
}

/**
 * Display a research pin on the map
 */
function displayResearchPin(coords, query) {
    console.log(`Displaying research pin at coordinates: [${coords[0]}, ${coords[1]}]`);
    
    // Get the map container and SVG
    const mapContainer = document.getElementById('scholar-map');
    const svg = mapContainer.querySelector('svg');
    
    if (!svg) {
        console.error('SVG not found in map container');
        return;
    }
    
    // Remove any existing research pins
    const existingPins = svg.querySelectorAll('.research-pin-group');
    existingPins.forEach(pin => pin.remove());
    
    // Create a group for the pin and label
    const pinGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    pinGroup.classList.add('research-pin-group');
    
    // Create the pin with a pulsing animation
    const pin = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    pin.classList.add('research-pin');
    pin.setAttribute('cx', coords[0]);
    pin.setAttribute('cy', coords[1]);
    pin.setAttribute('r', 10);
    pin.setAttribute('fill', 'var(--accent-color)');
    pin.setAttribute('stroke', 'white');
    pin.setAttribute('stroke-width', '2');
    
    // Add a pulsing animation to the pin
    const animateRadius = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateRadius.setAttribute('attributeName', 'r');
    animateRadius.setAttribute('values', '10;15;10');
    animateRadius.setAttribute('dur', '2s');
    animateRadius.setAttribute('repeatCount', 'indefinite');
    pin.appendChild(animateRadius);
    
    // Add a pulsing animation to the stroke width
    const animateStroke = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateStroke.setAttribute('attributeName', 'stroke-width');
    animateStroke.setAttribute('values', '2;4;2');
    animateStroke.setAttribute('dur', '2s');
    animateStroke.setAttribute('repeatCount', 'indefinite');
    pin.appendChild(animateStroke);
    
    // Add a pulsing animation to the opacity
    const animateOpacity = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateOpacity.setAttribute('attributeName', 'opacity');
    animateOpacity.setAttribute('values', '1;0.7;1');
    animateOpacity.setAttribute('dur', '2s');
    animateOpacity.setAttribute('repeatCount', 'indefinite');
    pin.appendChild(animateOpacity);
    
    // Create the label
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.classList.add('research-pin-label');
    label.setAttribute('x', coords[0]);
    label.setAttribute('y', coords[1] - 20);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('fill', 'var(--text-color)');
    label.setAttribute('font-size', '14px');
    label.setAttribute('font-weight', 'bold');
    label.setAttribute('pointer-events', 'none');
    label.textContent = query.length > 30 ? query.substring(0, 27) + '...' : query;
    
    // Add a white background to the label
    const labelBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    labelBg.setAttribute('fill', 'white');
    labelBg.setAttribute('rx', '6');
    labelBg.setAttribute('ry', '6');
    labelBg.setAttribute('opacity', '0.9');
    
    // Calculate the background size based on the text
    const labelWidth = Math.min(query.length * 8, 250);
    labelBg.setAttribute('width', labelWidth);
    labelBg.setAttribute('height', '24');
    labelBg.setAttribute('x', coords[0] - labelWidth / 2);
    labelBg.setAttribute('y', coords[1] - 38);
    
    // Add elements to the SVG
    pinGroup.appendChild(labelBg);
    pinGroup.appendChild(label);
    pinGroup.appendChild(pin);
    svg.appendChild(pinGroup);
    
    // Calculate the position to center the map on the pin
    const pinX = coords[0];
    const pinY = coords[1];
    
    // Get the current transform values
    const transform = svg.__zoom || { k: 1, x: 0, y: 0 };
    
    // Calculate the center position
    const width = mapContainer.clientWidth;
    const height = mapContainer.clientHeight;
    
    // Calculate the new transform to center on the pin
    const scale = Math.max(1.5, transform.k); // Zoom in a bit more than current level
    const x = width / 2 - pinX * scale;
    const y = height / 2 - pinY * scale;
    
    // Apply the transform with a smooth transition
    d3.select(svg)
        .transition()
        .duration(750)
        .call(
            d3.zoom().transform,
            d3.zoomIdentity.translate(x, y).scale(scale)
        );
    
    // Add a notification
    const notification = document.createElement('div');
    notification.className = 'vicinity-notification';
    notification.style.cssText = 'position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background-color: var(--accent-color); color: white; border-radius: 8px; padding: 10px 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000;';
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-search"></i>
            <span>Research topic projected: "${query}"</span>
        </div>
    `;
    document.body.appendChild(notification);
    
    // Remove the notification after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
    
    // Do not find closest scholars to the research pin
}

/**
 * Find the closest scholars to a research pin
 */
function findClosestScholarsToPin(coords) {
    console.log(`Finding closest scholars to coordinates: [${coords[0]}, ${coords[1]}]`);
    
    // Get all scholars
    const scholars = window.scholarsData;
    if (!scholars) {
        console.error('Scholar data not available');
        return;
    }
    
    // Calculate Euclidean distance to all scholars
    const scholarsWithDistance = scholars.map(scholar => {
        // Calculate Euclidean distance between UMAP coordinates
        const dx = scholar.umap[0] - coords[0];
        const dy = scholar.umap[1] - coords[1];
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        return {
            scholar,
            distance
        };
    }).sort((a, b) => a.distance - b.distance); // Sort by distance (ascending)
    
    // Get the top 5 closest scholars
    const closestScholars = scholarsWithDistance.slice(0, 5).map(item => item.scholar);
    console.log(`Found ${closestScholars.length} scholars closest to the research pin`);
    
    // Display the closest scholars in the sidebar
    const sidebar = document.getElementById('sidebar');
    const detailsContainer = document.getElementById('scholar-details');
    
    if (!detailsContainer) {
        console.error('Scholar details container not found');
        return;
    }
    
    // Force the sidebar to be visible
    if (sidebar) {
        sidebar.style.display = 'block';
        sidebar.style.width = '350px';
    }
    
    console.log('Updating sidebar with closest scholars');
    
    // Create HTML for the closest scholars list with prominent styling
    let scholarsListHtml = `
        <div class="selected-scholars-list" style="width: 100%; box-sizing: border-box; margin-top: 0;">
            <h3 style="color: var(--accent-color); font-size: 20px; margin-bottom: 15px;">Scholars Related to Research</h3>
            <p style="margin-bottom: 15px; font-size: 14px; color: #666;">These scholars work on topics related to your research query:</p>
            <ul class="scholars-list" style="max-height: 400px; overflow-y: auto; margin-bottom: 15px; padding: 0;">
    `;
    
    closestScholars.forEach(scholar => {
        scholarsListHtml += `
            <li class="scholar-list-item" data-id="${scholar.id}" style="padding: 12px; margin-bottom: 10px; background-color: #fff5f5; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; border: 1px solid #ffe0e0;">
                <div class="scholar-list-name" style="font-weight: 600; color: #333; margin-bottom: 5px;">${scholar.name}</div>
                <div class="scholar-list-institution" style="font-size: 13px; color: #666;">${scholar.institution || 'Unknown Institution'}</div>
            </li>
        `;
    });
    
    scholarsListHtml += `
            </ul>
            <button id="reset-view-button" class="show-vicinity-button" style="width: 100%; margin-top: 15px; background-color: var(--accent-color); color: white; border: none; border-radius: 4px; padding: 10px; font-size: 14px; cursor: pointer;">
                <i class="fas fa-sync-alt"></i> Reset View
            </button>
        </div>
    `;
    
    // Update the sidebar content with the closest scholars list
    detailsContainer.innerHTML = scholarsListHtml;
    console.log('Sidebar updated with closest scholars');
    
    // Add click event listeners to the scholar list items
    document.querySelectorAll('.scholar-list-item').forEach(item => {
        item.addEventListener('click', () => {
            const scholarId = item.getAttribute('data-id');
            const scholar = window.scholarsData.find(s => String(s.id) === String(scholarId));
            if (scholar) {
                showScholarDetails(scholar);
            }
        });
    });
    
    // Add click event listener to the reset button
    const resetButton = detailsContainer.querySelector('#reset-view-button');
    if (resetButton) {
        resetButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Reset view button clicked');
            
            // Reset the view
            resetView();
            
            // Reset the sidebar
            detailsContainer.innerHTML = `
                <div class="placeholder-message">
                    <i class="fas fa-user-circle"></i>
                    <p>Select a scholar to view their profile</p>
                    <small>Explore the map by clicking on scholar nodes</small>
                </div>
            `;
        });
    }
}

/**
 * Reset the map view to the default state
 */
function resetView() {
    console.log('Resetting view');
    
    // Get the map container and SVG
    const mapContainer = document.getElementById('scholar-map');
    const svg = mapContainer.querySelector('svg');
    
    if (!svg) {
        console.error('SVG not found in map container');
        return;
    }
    
    // Remove any existing research pins
    const existingPins = svg.querySelectorAll('.research-pin-group');
    existingPins.forEach(pin => pin.remove());
    
    // Reset the transform with a smooth transition
    d3.select(svg)
        .transition()
        .duration(750)
        .call(
            d3.zoom().transform,
            d3.zoomIdentity
        );
    
    // Reset any highlighted scholars
    const highlightedScholars = svg.querySelectorAll('.scholar-node.highlight-pulse');
    highlightedScholars.forEach(node => {
        node.classList.remove('highlight-pulse');
    });
}