const fs = require('fs');
const path = require('path');

const filePath = path.join(process.cwd(), 'public/Data/key_stocks_to_watch.txt');
const text = fs.readFileSync(filePath, 'utf-8');

console.log("--- File Content Start ---");
console.log(text);
console.log("--- File Content End ---");

const lines = text.split('\n').filter(line => line.trim() !== '');

const allStocks = [];
const lineRegex = /^(.*?)\s*(\([+-][\d.]+%?\))/;

console.log("--- Parsing ---");
for (const line of lines) {
    const match = line.match(lineRegex);
    if (match && match.length > 2) {
        const name = match[1].trim();
        const change = match[2].trim().replace(/[()]/g, '');
        console.log(`Matched: Name='${name}', Change='${change}'`);
        allStocks.push({ name, change });
    } else {
        console.log(`Failed to match line: '${line}'`);
    }
}

const positive = allStocks.filter(s => s.change.startsWith('+')).slice(0, 5);
const negative = allStocks.filter(s => s.change.startsWith('-')).slice(0, 5);

console.log("--- Results ---");
console.log("Positive:", positive);
console.log("Negative:", negative);
