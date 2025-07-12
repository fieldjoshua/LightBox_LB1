# COMPLETE LIST OF ALL LIGHTBOX PARAMETERS

## ANIMATION PARAMETERS (Global)

### Core Animation Controls:
1. **brightness** (0.0-1.0) - Overall brightness multiplier
2. **speed** (0.1-10.0) - Animation speed multiplier
3. **color_palette** - Active color scheme ("rainbow", "fire", "ocean", "forest", custom)
4. **animation_program** - Current animation name
5. **target_fps** - Frame rate target (15-60)

### Color & Visual Parameters:
6. **gamma** (1.0-3.0) - Gamma correction curve (typically 2.2)
7. **intensity** (0.0-2.0) - Color intensity multiplier
8. **saturation** (0.0-1.0) - Global saturation adjustment
9. **hue_shift** (0.0-1.0) - Global hue rotation
10. **contrast** (0.5-2.0) - Contrast adjustment
11. **color_temperature** (2000-10000) - Kelvin color temp

### Animation-Specific Parameters:
12. **scale** (0.1-10.0) - Pattern scale/zoom
13. **wave_speed** (0.01-1.0) - Wave animation speed
14. **color_speed** (0.001-0.1) - Color cycling speed
15. **wave_scale** (0.1-2.0) - Wave pattern size
16. **transition_speed** (0.1-5.0) - Transition between states
17. **complexity** (1-10) - Pattern complexity
18. **density** (0.1-1.0) - Effect density
19. **fade_rate** (0.01-1.0) - Fade/decay speed

### Advanced Animation:
20. **motion_blur** (0.0-1.0) - Motion blur amount
21. **strobe_rate** (0-30) - Strobe frequency (0=off)
22. **pulse_speed** (0.1-10.0) - Pulsing effects
23. **rotation_speed** (-5.0-5.0) - Pattern rotation
24. **zoom_speed** (0.5-2.0) - Zoom in/out speed
25. **kaleidoscope_segments** (2-16) - Symmetry count

## MATRIX-SPECIFIC PARAMETERS

### WS2811 (NeoPixel) Settings:
26. **ws2811.width** (10) - Matrix width
27. **ws2811.height** (10) - Matrix height  
28. **ws2811.num_pixels** (100) - Total pixel count
29. **ws2811.serpentine** (true/false) - Zigzag wiring
30. **ws2811.data_pin** ("D12") - GPIO pin
31. **ws2811.gamma** (2.2) - Per-strip gamma

### HUB75 RGB Panel Settings:
32. **hub75.rows** (32/64) - Panel rows
33. **hub75.cols** (32/64) - Panel columns
34. **hub75.chain_length** (1-8) - Chained panels
35. **hub75.parallel** (1-3) - Parallel chains
36. **hub75.pwm_bits** (1-11) - Color depth
37. **hub75.pwm_lsb_nanoseconds** (50-3000) - PWM timing
38. **hub75.gpio_slowdown** (1-5) - GPIO speed
39. **hub75.hardware_pwm** (auto/true/false) - Hardware PWM
40. **hub75.cpu_isolation** (true/false) - Dedicate CPU
41. **hub75.limit_refresh** (0-1000) - FPS limit
42. **hub75.scan_mode** (0/1) - Scan pattern
43. **hub75.row_address_type** (0-3) - Addressing
44. **hub75.multiplexing** (0-17) - Mux type
45. **hub75.panel_type** ("FM6126A", etc) - Panel chip
46. **hub75.led_rgb_sequence** ("RGB", "RBG", etc)
47. **hub75.pixel_mapper_config** - Custom mapping
48. **hub75.brightness** (0-100) - Hardware brightness
49. **hub75.pwm_dither_bits** (0-2) - Dithering
50. **hub75.show_refresh_rate** (true/false) - Show FPS

## PERFORMANCE PARAMETERS

51. **performance.enable_caching** (true/false) - Use caches
52. **performance.cache_size** (100-10000) - Cache entries
53. **performance.buffer_pool_size** (2-10) - Frame buffers
54. **performance.stats_interval** (1-60) - Stats frequency
55. **performance.enable_profiling** (true/false) - Profiling
56. **performance.show_refresh_rate** (true/false) - FPS display
57. **performance.frame_skip** (0-5) - Skip frames if slow
58. **performance.adaptive_fps** (true/false) - Auto-adjust FPS

## COLOR PALETTE PARAMETERS

59. **palette.interpolation** ("linear", "cubic", "sine") - Blend mode
60. **palette.size** (2-256) - Palette colors
61. **palette.cycling** (true/false) - Auto-cycle colors
62. **palette.cycle_speed** (0.001-0.1) - Cycle rate
63. **palette.custom_colors** - User-defined colors

## EFFECT MODIFIERS

64. **effects.blur_radius** (0-10) - Blur amount
65. **effects.edge_fade** (0.0-1.0) - Edge fading
66. **effects.center_focus** (0.0-1.0) - Center brightness
67. **effects.vignette** (0.0-1.0) - Vignette strength
68. **effects.noise_amount** (0.0-1.0) - Noise/grain
69. **effects.color_shift_amount** (0.0-1.0) - Chromatic aberration

## PLATFORM-SPECIFIC OPTIMIZATIONS

### Pi Zero W Defaults:
- Lower target_fps (15-20)
- Reduced pwm_bits (7-8)
- Smaller cache_size
- Disabled profiling

### Pi 3B+ Defaults:
- Full optimizations enabled
- CPU isolation available
- Hardware PWM support
- Higher FPS targets

### Pi 4 Defaults:
- Maximum performance
- All features enabled
- Highest FPS possible
- Full color depth

## USAGE IN ANIMATIONS

```python
# Direct access (with compatibility layer)
brightness = config.BRIGHTNESS
width = config.MATRIX_WIDTH

# Optimized access
brightness = config.get("brightness", 0.8)
width = config.get("hub75.cols", 64)

# Performance-optimized methods
r, g, b = config.hsv_to_rgb(h, s, v)  # Cached + gamma
value = config.gamma_correct(value)    # Lookup table
idx = config.xy_to_index(x, y)        # Cached mapping
```

## CONFIGURATION PRECEDENCE

1. Command-line arguments (highest)
2. Environment variables
3. settings.json file
4. Preset files
5. Default values (lowest)

## REAL-TIME ADJUSTABLE

Via Web Interface API:
- brightness
- speed  
- color_palette
- All animation-specific params
- Performance settings

Via GPIO Buttons:
- brightness (up/down)
- speed (up/down)
- animation_program (next/prev)
- presets (load)