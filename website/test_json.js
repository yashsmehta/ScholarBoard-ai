// Test script to load and process scholars.json
const fs = require('fs');

try {
    // Load the JSON file
    const data = fs.readFileSync('./data/scholars.json', 'utf8');
    console.log('File loaded successfully');
    
    // Parse the JSON
    const scholarsData = JSON.parse(data);
    console.log(`Number of scholars: ${Object.keys(scholarsData).length}`);
    
    // Convert to array format (same as in script.js)
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
    
    // Check for valid UMAP coordinates
    const validScholars = scholars.filter(scholar => {
        const hasUMAP = scholar.umap && Array.isArray(scholar.umap) && scholar.umap.length === 2;
        return scholar.id && scholar.name && hasUMAP;
    });
    
    console.log(`Found ${validScholars.length} valid scholars out of ${scholars.length}`);
    
    if (validScholars.length > 0) {
        console.log('Sample valid scholar:', validScholars[0]);
    }
    
} catch (error) {
    console.error('Error processing JSON:', error);
}
