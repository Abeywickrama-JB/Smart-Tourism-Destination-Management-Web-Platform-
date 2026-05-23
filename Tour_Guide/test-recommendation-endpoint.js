// Simple test to verify the recommendation endpoint structure
const testRecommendationRequest = {
  destinationType: "beach",
  budget: "medium",
  bestTimeToVisit: "summer",
  difficultyLevel: "easy",
  groupSize: "couple"
};

console.log("Testing recommendation request structure:");
console.log(JSON.stringify(testRecommendationRequest, null, 2));

// This shows what the frontend will send to the backend
console.log("\nFrontend will send this to: http://localhost:8080/api/destinations/recommendations/preferences");
console.log("Method: POST");
console.log("Content-Type: application/json");
