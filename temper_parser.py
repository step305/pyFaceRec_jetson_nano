from enum import Enum

# string to parse
# Event: TA = %0.1fdeg To1 = %0.1fdeg, DIST = %0.2fcm, HANDS = 1\r\n


def convert_temper_string(strval):
    (_, _, _, TA, _, _, To1, _, _, dist, _, _, hands) = \
        [t(s) for t, s in zip((str, str, str, str, str, str, str, str, str, str, str, str, int), strval.split())]
    TA = float(TA[:-3])
    To1 = float(To1[:-4])
    dist = float(dist[:-3])
    return TA, To1, dist, hands


DLE1 = 'E'
DLE2 = 'v'
ETX1 = '\r'
ETX2 = '\n'


class ParserStates(Enum):
    WAIT_DLE1 = 1
    WAIT_DLE2 = 2
    WAIT_DATA = 3
    WAIT_ETX1 = 4
    WAIT_ETX2 = 5


class TemperParserState:
    def __init__(self):
        self.state = ParserStates.WAIT_DLE1
        self.packet = ''
        self.code = 0
        self.len = 0
        self.buffer = []
        self.data = []
        self.data_ready = False

    def parse_byte(self, new_byte):
        self.data_ready = False
        self.packet = ()
        if self.state == ParserStates.WAIT_DLE1:
            if chr(new_byte) == DLE1:
                self.len = 1
                self.buffer = chr(new_byte)
                self.state = ParserStates.WAIT_DLE2
        elif self.state == ParserStates.WAIT_DLE2:
            if chr(new_byte) == DLE2:
                self.len += 1
                self.buffer += chr(new_byte)
                self.state = ParserStates.WAIT_DATA
        elif self.state == ParserStates.WAIT_DATA:
            if chr(new_byte) == ETX1:
                self.state = ParserStates.WAIT_ETX1
            else:
                self.buffer += chr(new_byte)
                self.len += 1
        elif self.state == ParserStates.WAIT_ETX1:
            if chr(new_byte) == ETX2:
                TA, To1, dist, hands = convert_temper_string(self.buffer[0:self.len])
                if hands == 1:
                    self.data_ready = True
                    self.packet = (TA, To1)
                self.state = ParserStates.WAIT_DLE1
                self. len = 0
                self.buffer = ''
            else:
                self.state = ParserStates.WAIT_DLE1
                self.len = 0
                self.buffer = ''
                self.buffer = ''
