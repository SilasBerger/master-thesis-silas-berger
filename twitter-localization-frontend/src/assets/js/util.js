export function formatLargeNumber(number) {
  if (number < 1000) {
    return "" + number;
  } else if (number < 1000000) {
    return "" + (number / 1000).toFixed(2) + "K";
  }
  return "" + (number / 1000000).toFixed(2) + "M";
}
