import cv2
import os
import tornado.ioloop
import tornado.web
import tornado.websocket
import optical
import numpy as np
import StringIO
import Image
import base64

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class FooHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("hi")

class EchoWebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print "Websocket opened"
        self.prev = None

    def on_message(self, message):
        newim = self.parse_image(message)
        if self.prev == None:
            self.prev = newim
        else:
            retim = optical.detect_and_display(self.prev, newim)
            cv2.imwrite("yes.png", retim)
            self.prev = newim
            #retval, encodedim = cv2.imencode(".png", retim)
            #self.write_message(encodedim)
            file = open("yes.png", "r")
            self.write_message(str(file.read()), binary=True)

    def on_close(self):
        print "Websocket closed"

    def parse_image(self, buf):
        #print(type(buf))
        #print(dir(buf))
        #print(np.fromstring(buf, dtype=np.uint8))
        #print(np.asarray(buf.decode("base64")))
        #im = cv2.imdecode(np.asarray(buf.decode("base64")), 1)
        #im = cv2.cv.fromarray(np.fromstring(buf, dtype=np.uint8), True)
        #im = np.fromstring(buf, dtype=np.uint8)
        #pilImage = Image.open(StringIO.StringIO(buf));
        #npImage = np.array(pilImage)
        #im = cv2.cv.fromarray(npImage)
        #im = cv2.imdecode(buf.decode("base64"))
        img_str = base64.b64decode(buf)
        g = open("out.jpeg", "w");
        g.write(base64.b64decode(buf))
        #g.flush()
        #img = Image.open(StringIO.StringIO(img_str))
        #img.save("test2.jpeg")
        #npImage = np.array(img)
        #im = cv2.cv.fromarray(npImage)
        #im = cv2.imdecode(np.asarray(base64.b64decode(buf)), 1)
        npImage = cv2.imread("out.jpeg")
        #print(npImage)
        cv2.imwrite("test.jpeg", npImage)
        return npImage

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/foo", FooHandler),
    (r"/websocket", EchoWebSocketHandler),
    (r"/static", tornado.web.StaticFileHandler,
     dict(path=settings['static_path'])),
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()