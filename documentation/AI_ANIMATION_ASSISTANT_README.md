# LightBox AI Animation Assistant

## Overview

The LightBox AI Animation Assistant is a background agent that helps optimize and create LED matrix animations. It analyzes existing animations for performance characteristics and suggests optimizations to improve rendering speed and visual quality.

## Features

- **Animation Analysis**: Automatically analyzes animations for performance metrics like rendering time, pixel change rate, and color diversity
- **Optimization Suggestions**: Provides specific suggestions to improve animation performance
- **Complexity Estimation**: Calculates a complexity score based on code patterns to identify animations that might need refactoring
- **Animation Generation**: (Concept) Uses patterns from existing animations to generate new variations

## How It Works

The assistant works by:

1. Loading all animations from the scripts directory
2. Running each animation through a performance analysis
3. Identifying potential bottlenecks or inefficiencies
4. Suggesting specific optimizations
5. (Future) Generating new animations based on existing ones

## Usage

To use the AI Animation Assistant:

```bash
python3 ai_animation_assistant.py
```

This will analyze all animations in the `scripts` directory and provide optimization suggestions.

## Example Output

```
Starting LightBox AI Animation Assistant

Analyzing animations:

--- rainbow_wave ---
  Average frame time: 0.45ms
  Complexity score: 42.5

  Optimization suggestions:
  - [LOW] Only 3.2% of pixels change per frame. Consider partial updates or frame skipping.

--- fire_effect ---
  Average frame time: 2.75ms
  Complexity score: 87.3

  Optimization suggestions:
  - [MEDIUM] Animation is slow (2.75ms/frame). Consider optimizing loops or math operations.
  - [MEDIUM] Animation has high complexity score (87.3). Consider simplifying or breaking into helper functions.

AI Animation Assistant is ready.
```

## Future Enhancements

- Real-time monitoring of animations as they run
- Integration with a more advanced AI model for animation generation
- Web interface for visualization of performance metrics
- Automatic code refactoring suggestions with implementation
- Animation blending and transition suggestions

## Requirements

- Python 3.6+
- Access to animation scripts with standard `animate(pixels, config, frame)` function

## Integration with LightBox

This assistant is designed to work alongside the main LightBox application, analyzing animations in the background and providing optimization suggestions without interrupting the normal operation of the LED matrix. 