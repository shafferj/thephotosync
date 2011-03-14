
def get_bandwidth_cost(bytes_in, bytes_out, round_to=3):
    # cost is $0.10 per GB transferred in and
    # $0.15 per GB transferred out
    return round(int(bytes_in)/1024.**3 * 0.1 + int(bytes_out)/1024.**3 * 0.15, round_to)

