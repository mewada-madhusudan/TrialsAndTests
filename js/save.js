const outputPath = path.join(__dirname, 'reconstructed_sources');
if (!fs.existsSync(outputPath)) {
  fs.mkdirSync(outputPath);
}

smc.sources.forEach(sourceFile => {
  const sourceFilePath = path.join(__dirname, 'sources', sourceFile);  // Adjust path as needed
  
  if (fs.existsSync(sourceFilePath)) {
    const fileContent = fs.readFileSync(sourceFilePath, 'utf8');
    
    // Save each source file to disk
    const outputFile = path.join(outputPath, sourceFile);
    fs.writeFileSync(outputFile, fileContent);
    console.log(`Saved: ${outputFile}`);
  } else {
    console.log(`Source file not found: ${sourceFile}`);
  }
});

smc.destroy();
