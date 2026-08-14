Meters rows are broken up as follows:

- **Meter** First Frame: width = w
- **Marker** Second Frame: width = 0.25w, fill = 100%
- **Marker** Third Frame: width = 0.25w, fill = 75%
- **Marker** Fourth Frame: width = 0.25w, fill = 50%
- **Marker** Fifth Frame: width = 0.25w, fill = 25%

So the total width of a Meter Asset is 2w. 

The first frame of the Meter is the Meter itself. Each subsequent frame is a *Marker*. Each Marker's width is 25% of the width of Meter. The second frame is Marker width completely filled. The third frame is the Marker width 75% filled. The fourth frame is the Marker width 50% filled. The fifth frame is Marker width 25% filled. This division of the Meter and Marker frames allows a Meter to resolve an ingame attribute down to increments of 1/16. If `measurement / unit % 16 != 0`, then the increment displayed is rounded to the nearest 1/16th.

In other words, a Meter is broken up into four `markers` whose frames that are superimposed over the Meter itself, which is at frame index 0. Each Marker maps to a frame index (1 - 4). 

For example, if `player.state.meters.health.current == 75`, so that `measurement / unit = 0.625`, then

- marker 1: frame = 1
- marker 2: frame = 1
- marker 3: frame = 3
- marker 4: frame = None

The sequence to frames (1, 1, 3, None) would be superimposed over frame 0 at the positions (0, 0.25w, 0.5w, 0.75w).