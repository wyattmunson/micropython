class Lynx:
    def __init__(self, oled):
        self.oled = oled
    
    
    def renderEnterArrow(self, x, y):
        line1 = [x, y, x, y + 3] 
        line2 = [x, y + 3, x + 7, y + 3]
        line3 = [x + 4, y, x + 7, y + 3]
        line4 = [x + 4, y + 6, x + 7, y + 3]
        self.oled.line(line1[0], line1[1], line1[2], line1[3], 1)
        self.oled.line(line2[0], line2[1], line2[2], line2[3], 1)
        self.oled.line(line3[0], line3[1], line3[2], line3[3], 1)
        self.oled.line(line4[0], line4[1], line4[2], line4[3], 1)
    

    def renderScrollArrow(self, x, y):
        line1 = [x + 3, y, x + 3, y + 7]
        line2 = [x, y + 4, x + 3, y + 7]
        line3 = [x + 7, y + 4, x + 3, y + 7]
        self.oled.line(line1[0], line1[1], line1[2], line1[3], 1)
        self.oled.line(line2[0], line2[1], line2[2], line2[3], 1)
        self.oled.line(line3[0], line3[1], line3[2], line3[3], 1)