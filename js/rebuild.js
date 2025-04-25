const fs = require('fs');
const path = require('path');
const sourceMap = require('source-map');

const mapFilePath = path.join(__dirname, 'app.js.map');  // Path to your .map file
const mapFileContent = JSON.parse(fs.readFileSync(mapFilePath, 'utf8'));

// Create a new SourceMapConsumer
const smc = new sourceMap.SourceMapConsumer(mapFileContent);

// Iterate over each source file and get its content
smc.sources.forEach(sourceFile => {
  console.log(`Fetching source file: ${sourceFile}`);
  
  // Use this to fetch the actual content (from a local directory or a URL)
  // Example: You could fetch from a URL or local directory
  // Let's assume it's stored in a "sources" folder
  
  const sourceFilePath = path.join(__dirname, 'sources', sourceFile);  // Adjust path as needed
  
  if (fs.existsSync(sourceFilePath)) {
    const fileContent = fs.readFileSync(sourceFilePath, 'utf8');
    console.log(`Source content for ${sourceFile}:`);
    console.log(fileContent);
  } else {
    console.log(`Source file not found: ${sourceFile}`);
  }
});

smc.destroy(); // Clean up
