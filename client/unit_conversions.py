


MPS_TO_MPH = 2.23694
MM_TO_INCH = 0.0393701

def millimeters_to_inches(mm):
    return mm * MM_TO_INCH

def meters_per_second_to_miles_per_hour(mps):
    return mps * MPS_TO_MPH

# takes and returns wind direction in degrees
def wind_dir_correction(dir):
    # House off by 11.251 and flipped
    return (dir - 11 + 180) % 360