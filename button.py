import cv2
import numpy as np

def on_mouse(event, x, y, flags, param):
    global button
    if event == cv2.EVENT_LBUTTONDBLCLK:
        button.on_mouse(x, y)


class Button:
    values = ['NO_LABEL', 'NONE', '2C', '3C', '4C', 'PTS_S', 'PTS_L']
    mapping = {'NO_LABEL':0, 'NONE':1, '2C':2, '3C':3, '4C':4, 'PTS_S':5, 'PTS_L':5}
    def __init__(self):
        self.state = None
        self.width = 128
        self.height = 128
        self.margin = 3
        self.nrows = len(self.values)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.value = self.values[0]

        self.__draw_button()

    def __draw_button(self):
        self.image = np.zeros((self.nrows*self.height, self.width, 3), dtype=np.uint8)
        for i in range(self.nrows):
            x1, y1 = 0, i*self.height
            x2, y2 = x1+self.width, y1+self.height
            cv2.rectangle(self.image, (x1, y1), (x2, y2), (0, 0, 150), self.margin)

            # draw text
            label = self.values[i]
            textsize = cv2.getTextSize(label, self.font, 1, 2)[0]
            xm, ym = (x1+x2-textsize[0])//2, (y1+y2+textsize[1])//2
            cv2.putText(self.image, label, (xm, ym),
                        self.font, 1.0, (0, 255, 0), 2)
        self.tmp = self.image

    def reset(self):
        self.__draw_button()
        self.value = self.values[0]

    def __update(self, row):
        self.image = self.tmp.copy()
        x1, y1 = 0, row*self.height
        x2, y2 = x1+self.width, y1+self.height
        cv2.rectangle(self.image, (x1, y1), (x2, y2), (150, 50, 225), -1)

        # draw text
        label = self.values[row]
        textsize = cv2.getTextSize(label, self.font, 1, 2)[0]
        xm, ym = (x1+x2-textsize[0])//2, (y1+y2+textsize[1])//2
        cv2.putText(self.image, label, (xm, ym),
                    self.font, 1.0, (255, 255, 0), 2)

    def on_change(self, label):
        label = label.upper()
        if label in self.values:
            row = self.mapping[label]
            self.__update(row)
            self.value = self.values[row]
        else:
            self.reset()

    def on_mouse(self, x, y):
        yy = y // self.height
        self.__update(yy)
        self.value = self.values[yy]
        print('CHAMBER UPDATED:', self.value)
        return self.value

    def get_ui(self):
        return self.image

    def get_value(self):
        return self.value

if __name__ == '__main__':
    cv2.namedWindow("bla")
    cv2.namedWindow("blo")
    cv2.setMouseCallback("bla", on_mouse)

    button = Button()
    img = np.ones((512, 512, 3), dtype=np.uint8) * 255
    while True:
        img = button.get_ui()
        text = button.get_value()
        cv2.imshow('bla', img)

        img = img*0
        cv2.putText(img, str(text), (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
        cv2.imshow('blo', img)

        key = cv2.waitKey(30)
        if key == ord("q"):
            cv2.destroyAllWindows()
            exit(0)
