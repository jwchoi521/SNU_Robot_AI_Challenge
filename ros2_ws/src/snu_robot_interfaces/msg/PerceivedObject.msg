# One camera-visible object enriched with distance and navigation role.
#
# The detector should publish every relevant object, not only the current target.
# Mission logic or perception post-processing assigns navigation_role:
# target objects become approach goals, non-target objects become obstacles.

uint8 ROLE_UNKNOWN=0
uint8 ROLE_TARGET=1
uint8 ROLE_OBSTACLE=2
uint8 ROLE_IGNORE=3

string object_kind
string fruit_kind

uint8 navigation_role
float32 confidence

float32 bbox_x1
float32 bbox_y1
float32 bbox_x2
float32 bbox_y2

# Current YOLO convention: positive means image-right.
float32 bearing_deg

bool has_distance
float32 distance_m

# Optional physical radius used when expanding semantic obstacles.
# If this is 0, consumers use their configured default radius.
float32 obstacle_radius_m

bool pick_allowed
bool target_confirmed
