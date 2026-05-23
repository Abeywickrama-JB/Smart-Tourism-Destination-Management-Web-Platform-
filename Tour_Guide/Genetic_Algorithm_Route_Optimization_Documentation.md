# Genetic Algorithm Route Optimization Documentation

## Overview

This document explains the implementation and usage of the Genetic Algorithm (GA) for route optimization in the Tour Guide AIML project. The system uses a genetic algorithm to solve the Traveling Salesman Problem (TSP), finding the most efficient route that visits all selected tourist destinations while minimizing total travel distance.

## Table of Contents

1. [Algorithm Architecture](#algorithm-architecture)
2. [Implementation Details](#implementation-details)
3. [Genetic Algorithm Components](#genetic-algorithm-components)
4. [Integration with Tour Guide System](#integration-with-tour-guide-system)
5. [User Interface Components](#user-interface-components)
6. [Performance Analysis](#performance-analysis)
7. [Usage Examples](#usage-examples)
8. [Configuration and Tuning](#configuration-and-tuning)

## Algorithm Architecture

### Problem Definition
The route optimization system solves the **Traveling Salesman Problem (TSP)** for tourist destinations:
- **Input**: List of destinations with GPS coordinates
- **Output**: Optimized route order minimizing total distance
- **Objective**: Find shortest possible path visiting all destinations exactly once

### Genetic Algorithm Approach
The implementation uses a classic genetic algorithm with the following characteristics:
- **Population-based evolution**: Multiple candidate solutions evolve simultaneously
- **Fitness-driven selection**: Better solutions have higher survival probability
- **Genetic operations**: Crossover and mutation create new solutions
- **Elitism preservation**: Best solutions are guaranteed to survive

## Implementation Details

### File Location
```
/frontend/src/utils/geneticRouteOptimizer.js
```

### Core Class Structure
```javascript
class GeneticRouteOptimizer {
  constructor(options = {}) {
    this.populationSize = options.populationSize || 100;
    this.generations = options.generations || 500;
    this.mutationRate = options.mutationRate || 0.02;
    this.eliteSize = options.eliteSize || 20;
    this.tournamentSize = options.tournamentSize || 5;
  }
}
```

### Distance Calculation
The system uses the **Haversine formula** for accurate GPS distance calculations:

```javascript
calculateDistance(point1, point2) {
  const R = 6371; // Earth's radius in kilometers
  const dLat = this.toRad(point2.lat - point1.lat);
  const dLon = this.toRad(point2.lng - point1.lng);
  const lat1 = this.toRad(point1.lat);
  const lat2 = this.toRad(point2.lat);

  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.sin(dLon/2) * Math.sin(dLon/2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}
```

**Key Features:**
- Accounts for Earth's curvature
- Provides accurate real-world distances
- Essential for practical route optimization

## Genetic Algorithm Components

### 1. Initial Population Creation
```javascript
createInitialPopulation(locationCount) {
  const population = [];
  for (let i = 0; i < this.populationSize; i++) {
    const individual = Array.from({length: locationCount}, (_, i) => i);
    // Shuffle the array to create random route
    for (let j = individual.length - 1; j > 0; j--) {
      const k = Math.floor(Math.random() * (j + 1));
      [individual[j], individual[k]] = [individual[k], individual[j]];
    }
    population.push(individual);
  }
  return population;
}
```

**Purpose:** Generate diverse starting solutions
- Each individual is a permutation of destination indices
- Random initialization ensures exploration of solution space
- Population size affects solution diversity and convergence speed

### 2. Fitness Function
```javascript
calculateRouteDistance(route, locations) {
  let totalDistance = 0;
  for (let i = 0; i < route.length - 1; i++) {
    totalDistance += this.calculateDistance(
      locations[route[i]], 
      locations[route[i + 1]]
    );
  }
  // Add distance from last point back to first (for circular routes)
  if (route.length > 2) {
    totalDistance += this.calculateDistance(
      locations[route[route.length - 1]], 
      locations[route[0]]
    );
  }
  return totalDistance;
}
```

**Fitness = Total Route Distance** (lower is better)
- Calculates cumulative distance between consecutive destinations
- Includes return to starting point for complete tours
- Direct optimization objective

### 3. Selection: Tournament Selection
```javascript
tournamentSelection(population, fitnessScores) {
  let best = null;
  let bestFitness = Infinity;

  for (let i = 0; i < this.tournamentSize; i++) {
    const randomIndex = Math.floor(Math.random() * population.length);
    const fitness = fitnessScores[randomIndex];
    
    if (fitness < bestFitness) {
      bestFitness = fitness;
      best = population[randomIndex];
    }
  }
  
  return best;
}
```

**Advantages:**
- Maintains selection pressure
- Preserves some diversity
- Simple and efficient implementation
- Adjustable tournament size controls selection intensity

### 4. Crossover: Ordered Crossover (OX1)
```javascript
crossover(parent1, parent2) {
  const size = parent1.length;
  const start = Math.floor(Math.random() * size);
  const end = Math.floor(Math.random() * (size - start)) + start;
  
  const child = new Array(size).fill(-1);
  
  // Copy segment from parent1
  for (let i = start; i <= end; i++) {
    child[i] = parent1[i];
  }
  
  // Fill remaining from parent2
  let currentPos = 0;
  for (let i = 0; i < size; i++) {
    const city = parent2[i];
    if (!child.includes(city)) {
      while (child[currentPos] !== -1) {
        currentPos++;
      }
      child[currentPos] = city;
    }
  }
  
  return child;
}
```

**OX1 Benefits:**
- Preserves relative ordering from parents
- Guarantees valid offspring (no duplicates)
- Maintains route continuity
- Well-suited for permutation problems

### 5. Mutation: Swap Mutation
```javascript
mutate(individual) {
  if (Math.random() < this.mutationRate) {
    const size = individual.length;
    const i = Math.floor(Math.random() * size);
    const j = Math.floor(Math.random() * size);
    [individual[i], individual[j]] = [individual[j], individual[i]];
  }
  return individual;
}
```

**Purpose:**
- Introduces genetic diversity
- Prevents premature convergence
- Helps escape local optima
- Low mutation rate preserves good solutions

### 6. Elitism Strategy
```javascript
// Keep elite individuals
const eliteIndices = fitnessScores
  .map((fitness, index) => ({ fitness, index }))
  .sort((a, b) => a.fitness - b.fitness)
  .slice(0, this.eliteSize)
  .map(item => item.index);

eliteIndices.forEach(index => {
  newPopulation.push([...population[index]]);
});
```

**Benefits:**
- Guarantees monotonic improvement
- Preserves best found solutions
- Accelerates convergence
- Prevents loss of optimal solutions

## Integration with Tour Guide System

### System Architecture
```
TourRoutePlanningPage.jsx
    ↓
RouteOptimizer.jsx
    ↓
GeneticRouteOptimizer.js
    ↓
Optimized Route Results
```

### Data Flow
1. **Input**: Tourist destinations with GPS coordinates
2. **Processing**: GA optimizes route order
3. **Output**: Optimized route with distance and time estimates
4. **Integration**: Seamlessly connects to package creation system

### Key Integration Points

#### Route Planning Page (`TourRoutePlanningPage.jsx`)
- Loads destinations from user selections
- Manages tour information and naming
- Handles route optimization workflow
- Integrates with package creation

#### Route Optimizer Component (`RouteOptimizer.jsx`)
- Provides user interface for GA execution
- Displays real-time progress monitoring
- Shows optimization results and statistics
- Handles user interactions

#### Genetic Route Optimizer (`geneticRouteOptimizer.js`)
- Core GA implementation
- Distance calculations using Haversine formula
- Route optimization algorithms
- Time estimation calculations

## User Interface Components

### Route Optimizer Component Features
- **Optimization Control**: Start/stop optimization process
- **Progress Monitoring**: Real-time generation and fitness tracking
- **Results Display**: Optimized route with distance and time
- **Visual Feedback**: Progress bars and statistics

### Progress Monitoring
```javascript
const optimizationResult = optimizer.optimizeRoute(
  locations,
  (progressData) => {
    setProgress(progressData);
  }
);
```

**Displayed Information:**
- Current generation number
- Best distance found so far
- Current generation's best distance
- Progress bar showing completion percentage

### Results Presentation
- **Total Distance**: Optimized route length in kilometers
- **Estimated Time**: Travel time with 20% buffer for stops
- **Route Order**: Sequential list of optimized destinations
- **Coordinates**: GPS coordinates for each destination

## Performance Analysis

### Algorithm Characteristics

#### Convergence Behavior
- **Early Generations**: Rapid improvement as good solutions are found
- **Middle Generations**: Gradual refinement of existing solutions
- **Late Generations**: Fine-tuning and local optimization

#### Solution Quality
- **Small Tours (2-5 destinations)**: Often finds optimal solutions quickly
- **Medium Tours (6-10 destinations)**: High-quality near-optimal solutions
- **Large Tours (11+ destinations)**: Good solutions with room for improvement

#### Computational Performance
- **Time Complexity**: O(generations × population_size × destination_count²)
- **Space Complexity**: O(population_size × destination_count)
- **Typical Execution**: 1-5 seconds for 5-15 destinations

### Optimization Parameters

#### Default Configuration
```javascript
{
  populationSize: 100,    // Balance between diversity and speed
  generations: 500,       // Sufficient for convergence
  mutationRate: 0.02,    // Low mutation to preserve good solutions
  eliteSize: 20,         // 20% elitism for guaranteed improvement
  tournamentSize: 5      // Moderate selection pressure
}
```

#### Parameter Tuning Guidelines
- **Population Size**: Increase for larger destination sets
- **Generations**: More generations for better solutions
- **Mutation Rate**: Adjust based on convergence behavior
- **Elite Size**: Higher elitism for faster convergence

## Usage Examples

### Basic Route Optimization
```javascript
// Initialize optimizer
const optimizer = new GeneticRouteOptimizer({
  populationSize: 100,
  generations: 300,
  mutationRate: 0.02,
  eliteSize: 20
});

// Define destinations
const locations = [
  { name: "Sigiriya", lat: 8.5234, lng: 80.7543 },
  { name: "Kandy", lat: 7.2906, lng: 80.6337 },
  { name: "Galle", lat: 6.0535, lng: 80.2200 }
];

// Optimize route
const result = optimizer.optimizeRoute(locations);

// Get detailed route information
const routeDetails = optimizer.getOptimizedRouteDetails(locations, result);
const estimatedTime = optimizer.calculateEstimatedTime(result.distance);
```

### Integration with React Components
```javascript
const handleOptimize = () => {
  const optimizer = new GeneticRouteOptimizer({
    populationSize: 100,
    generations: 300,
    mutationRate: 0.02,
    eliteSize: 20
  });

  const optimizationResult = optimizer.optimizeRoute(
    locations,
    (progressData) => {
      setProgress(progressData);
    }
  );

  const routeDetails = optimizer.getOptimizedRouteDetails(locations, optimizationResult);
  const estimatedTime = optimizer.calculateEstimatedTime(optimizationResult.distance);
  
  setResult({
    ...optimizationResult,
    routeDetails,
    estimatedTime
  });
};
```

## Configuration and Tuning

### Parameter Optimization

#### For Small Tours (2-5 destinations)
```javascript
{
  populationSize: 50,
  generations: 200,
  mutationRate: 0.01,
  eliteSize: 10
}
```

#### For Medium Tours (6-10 destinations)
```javascript
{
  populationSize: 100,
  generations: 500,
  mutationRate: 0.02,
  eliteSize: 20
}
```

#### For Large Tours (11+ destinations)
```javascript
{
  populationSize: 200,
  generations: 1000,
  mutationRate: 0.03,
  eliteSize: 40
}
```

### Performance Optimization Tips

1. **Adaptive Parameters**: Adjust parameters based on destination count
2. **Early Termination**: Stop if no improvement for 50 generations
3. **Multi-threading**: Consider Web Workers for large optimization tasks
4. **Caching**: Cache distance calculations for repeated optimizations

### Monitoring and Debugging

#### Progress Tracking
```javascript
optimizer.optimizeRoute(locations, (progressData) => {
  console.log(`Generation ${progressData.generation}: ${progressData.bestDistance.toFixed(2)} km`);
});
```

#### Solution Validation
```javascript
// Verify route validity
function validateRoute(route, locationCount) {
  if (route.length !== locationCount) return false;
  const sorted = [...route].sort();
  for (let i = 0; i < locationCount; i++) {
    if (sorted[i] !== i) return false;
  }
  return true;
}
```

## Conclusion

The genetic algorithm implementation provides an intelligent, automated solution for tour route optimization in the Tour Guide AIML project. Key strengths include:

- **Global Optimization**: Avoids local optima through population-based search
- **Scalability**: Handles varying numbers of destinations efficiently
- **Real-time Feedback**: Progress monitoring enhances user experience
- **Practical Application**: Uses real GPS coordinates and accurate calculations
- **Seamless Integration**: Works smoothly with existing tour guide system

The system successfully transforms the complex Traveling Salesman Problem into a user-friendly feature that helps tourists plan efficient, enjoyable tours of Sri Lankan destinations.

## Files and Locations

### Core Implementation
- `/frontend/src/utils/geneticRouteOptimizer.js` - Main GA implementation
- `/frontend/src/components/route/RouteOptimizer.jsx` - UI component
- `/frontend/src/pages/TourRoutePlanningPage.jsx` - Main page integration

### Supporting Files
- `/frontend/src/components/route/DestinationInput.jsx` - Destination selection
- `/frontend/src/styles/routeOptimizer.css` - Styling for route optimizer
- `/frontend/src/styles/tourRoutePlanningPage.css` - Page styling

### Integration Points
- Package creation system
- Session storage for data persistence
- Navigation system for tour workflow

This documentation provides a comprehensive understanding of the genetic algorithm implementation and its role in creating intelligent tour planning solutions.
