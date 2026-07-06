# One target produced by the camera detector and distance provider.
#
# The current YOLO branch uses bearing_deg where positive means image-right.
# Consumers can convert that convention with their own parameters.

string object_kind
string fruit_kind

float32 confidence

float32 bbox_x1
float32 bbox_y1
float32 bbox_x2
float32 bbox_y2

float32 bearing_deg

bool has_distance
float32 distance_m

bool pick_allowed
bool target_confirmed
