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
    
    // Create a tooltip element
    const tooltip = document.createElement('div');
    tooltip.setAttribute('class', 'map-tooltip');
    tooltip.style.display = 'none';
    mapContainer.appendChild(tooltip);
    
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
    
    // Add scholar nodes to the map
    shuffledScholars.forEach(scholar => {
        if (!scholar.umap) return;
        
        const [x, y] = scholar.umap;
        const scaledX = scaleX(x);
        const scaledY = scaleY(y);
        
        // Get color based on cluster
        const clusterId = scholar.cluster_id || 0;
        const color = clusterColors[clusterId] || '#4a6fa5';
        
        // Create circle for scholar
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', scaledX);
        circle.setAttribute('cy', scaledY);
        circle.setAttribute('r', '6'); // Fixed size for all dots
        circle.setAttribute('fill', color);
        circle.setAttribute('class', 'scholar-node');
        circle.setAttribute('data-id', scholar.id);
        circle.setAttribute('data-name', scholar.name);
        circle.setAttribute('data-institution', scholar.institution || '');
        circle.setAttribute('data-country', scholar.country || '');
        circle.setAttribute('data-cluster', clusterId);
        
        // Add event listeners
        circle.addEventListener('click', () => {
            // Highlight selected scholar
            document.querySelectorAll('.scholar-node').forEach(node => {
                node.classList.remove('selected');
            });
            circle.classList.add('selected');
            
            // Show scholar details in the details panel
            showScholarDetails(scholar);
        });
        
        circle.addEventListener('mouseenter', (e) => {
            // Show tooltip
            tooltip.innerHTML = `
                <strong>${scholar.name}</strong>
                <span>${scholar.institution || ''}</span>
                <span>${scholar.country || ''}</span>
            `;
            tooltip.style.display = 'block';
            updateTooltipPosition(e);
            
            // Highlight node - keep same size but add stroke
            circle.setAttribute('stroke', '#fff');
            circle.setAttribute('stroke-width', '2');
        });
        
        circle.addEventListener('mouseleave', () => {
            // Hide tooltip
            tooltip.style.display = 'none';
            
            // Reset node appearance
            if (!circle.classList.contains('selected')) {
                circle.setAttribute('stroke', 'none');
                circle.setAttribute('stroke-width', '0');
            }
        });
        
        circle.addEventListener('mousemove', (e) => {
            updateTooltipPosition(e);
        });
        
        scholarsGroup.appendChild(circle);
        
        // Create label for scholar
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', scaledX);
        label.setAttribute('y', scaledY - 15);
        label.setAttribute('text-anchor', 'middle');
        label.setAttribute('class', 'scholar-label');
        label.setAttribute('data-id', scholar.id);
        label.style.display = 'none'; // Hide by default
        label.textContent = scholar.name;
        labelsGroup.appendChild(label);
    });
    
    // Function to update tooltip position
    function updateTooltipPosition(e) {
        const rect = mapContainer.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Position tooltip near cursor but not under it
        tooltip.style.left = `${x + 15}px`;
        tooltip.style.top = `${y - 15}px`;
        
        // Ensure tooltip stays within container
        const tooltipRect = tooltip.getBoundingClientRect();
        if (tooltipRect.right > rect.right) {
            tooltip.style.left = `${x - tooltipRect.width - 10}px`;
        }
        if (tooltipRect.bottom > rect.bottom) {
            tooltip.style.top = `${y - tooltipRect.height - 10}px`;
        }
    }
    
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
        const labels = document.querySelectorAll('.scholar-label');
        
        // Show labels only when zoomed in enough
        if (currentZoom > 2.5) {
            labels.forEach(label => {
                label.style.display = 'block';
            });
        } else {
            labels.forEach(label => {
                label.style.display = 'none';
            });
        }
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
    
    mapContainer.addEventListener('mousedown', (e) => {
        if (e.target === svg || e.target === scholarsGroup) {
            isDragging = true;
            dragStart = { x: e.clientX, y: e.clientY };
            mapContainer.style.cursor = 'grabbing';
        }
    });
    
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            const dx = e.clientX - dragStart.x;
            const dy = e.clientY - dragStart.y;
            
            currentTranslate.x += dx;
            currentTranslate.y += dy;
            
            applyTransform();
            
            dragStart = { x: e.clientX, y: e.clientY };
        }
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
        mapContainer.style.cursor = 'default';
    });
    
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

function showScholarDetails(scholar) {
    const sidebar = document.getElementById('sidebar');
    const detailsContainer = document.getElementById('scholar-details');
    
    if (!sidebar || !detailsContainer) {
        console.error('Sidebar or details container not found');
        return;
    }
    
    // Show loading state
    detailsContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading scholar profile...</div>';
    
    console.log(`Loading profile for scholar ${scholar.id}: ${scholar.name}`);
    
    // Create a basic profile with the data we already have
    const basicProfileHtml = `
        <div class="scholar-profile">
            <div class="profile-header">
                <div class="profile-image">
                    <img src="images/placeholder.jpg" alt="${scholar.name}" onerror="this.src='images/placeholder.jpg'">
                </div>
                <div class="profile-info">
                    <h3>${scholar.name}</h3>
                    <div class="institution">${scholar.institution || 'Unknown Institution'}</div>
                </div>
            </div>
            <div class="profile-content">
                <div class="loading-indicator">Loading scholar profile...</div>
            </div>
        </div>
    `;
    
    // Update with basic profile immediately
    detailsContainer.innerHTML = basicProfileHtml;
    
    // Fetch additional scholar details
    fetch(`/api/scholar/${scholar.id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load scholar profile');
            }
            return response.json();
        })
        .then(data => {
            console.log('Loaded scholar profile:', data);
            
            // Update profile image if available
            if (data.profile_pic) {
                const profileImg = detailsContainer.querySelector('.profile-image img');
                if (profileImg) {
                    profileImg.src = data.profile_pic;
                    profileImg.onerror = () => {
                        profileImg.src = 'images/placeholder.jpg';
                    };
                }
            }
            
            // Format and display markdown content
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
                    
                    // Setup interactive elements in the markdown
                    setupMarkdownInteractions();
                } else {
                    profileContent.innerHTML = `
                        <div class="research-info">
                            <div class="research-text">
                                <p>No detailed information available for this scholar.</p>
                            </div>
                        </div>
                    `;
                }
            }
        })
        .catch(error => {
            console.error('Error loading scholar profile:', error);
            const profileContent = detailsContainer.querySelector('.profile-content');
            if (profileContent) {
                profileContent.innerHTML = `
                    <div class="error-message">
                        <p>Failed to load scholar profile. Please try again later.</p>
                        <p class="error-details">${error.message}</p>
                    </div>
                `;
            }
        });
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
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.filter-container') && filterDropdown) {
            filterDropdown.classList.remove('active');
        }
    });
    
    // Populate initial filter options (institution only)
    populateFilterOptions(scholars, 'institution');
    
    // Apply filters button
    if (applyButton) {
        applyButton.addEventListener('click', () => {
            applyFilters(scholars);
            filterDropdown.classList.remove('active');
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

function setupSearch(scholars) {
    const searchInput = document.getElementById('scholar-search');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput || !searchButton || !searchResults) {
        console.error('Search elements not found');
        return;
    }
    
    // Function to perform search
    function performSearch(query) {
        if (!query || query.length < 2) return [];
        
        query = query.toLowerCase();
        
        return scholars.filter(scholar => {
            const name = scholar.name.toLowerCase();
            const institution = (scholar.institution || '').toLowerCase();
            
            return name.includes(query) || institution.includes(query);
        });
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
                    <img src="data/profile_pics/${scholar.id}.jpg" alt="${scholar.name}" onerror="this.src='images/placeholder.jpg'">
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
        document.querySelectorAll('.scholar-node').forEach(node => {
            node.classList.remove('selected');
        });
        
        // Add highlight to the matching scholar dot
        const node = document.querySelector(`.scholar-node[data-id="${scholarId}"]`);
        if (node) {
            node.classList.add('selected');
            
            // Scroll to the scholar node
            const mapContainer = document.getElementById('scholar-map');
            if (mapContainer) {
                // Get the position of the node
                const x = parseFloat(node.getAttribute('cx'));
                const y = parseFloat(node.getAttribute('cy'));
                
                // Calculate the center of the map container
                const rect = mapContainer.getBoundingClientRect();
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                // Update the translation to center the node
                const scholarsGroup = document.querySelector('.scholars-group');
                if (scholarsGroup) {
                    currentTranslate.x = centerX - x * currentZoom;
                    currentTranslate.y = centerY - y * currentZoom;
                    
                    // Apply the transform
                    scholarsGroup.style.transform = `translate(${currentTranslate.x}px, ${currentTranslate.y}px) scale(${currentZoom})`;
                }
            }
        }
    }
    
    // Handle search input
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        
        if (query.length >= 2) {
            const results = performSearch(query);
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
            const results = performSearch(query);
            displaySearchResults(results, query);
            searchResults.classList.add('active');
        }
    });
    
    // Handle Enter key in search input
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            
            if (query.length >= 2) {
                const results = performSearch(query);
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