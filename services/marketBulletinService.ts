export const fetchAndParseMarketBulletinData = async (): Promise<string[]> => {
  const response = await fetch('https://raw.githubusercontent.com/Prasannapriyan/Generator/refs/heads/main/Data/market_bulletin.txt');
  if (!response.ok) {
    throw new Error(`Failed to fetch market bulletin data: ${response.statusText}`);
  }
  const text = await response.text();
  // Split by newline, filter out empty lines, and trim whitespace
  return text.split('\n').filter(line => line.trim() !== '').map(line => line.trim());
};