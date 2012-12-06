import base64
import cv2
import optical
import os
import tornado.ioloop
import tornado.web
import tornado.websocket

DIRECTORY = "tmp"

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class VideoWebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print "Websocket opened"
        self.prev = None
        if not os.path.exists(DIRECTORY):
            os.makedirs(DIRECTORY)

    def on_message(self, message):
        newim = self.parse_image(message)
        if self.prev == None:
            self.prev = newim
        else:
            retim = optical.detect_and_display(self.prev, newim)
            cv2.imwrite(DIRECTORY + "/out.png", retim)
            self.prev = newim
            file = open(DIRECTORY + "/out.png", "r")
            self.write_message(str(file.read()), binary=True)

    def on_close(self):
        print "Websocket closed"

    def parse_image(self, buf):
        img_str = base64.b64decode(buf)
        img = open(DIRECTORY + "/in.jpeg", "w+");
        img.write(base64.b64decode(buf))
        return cv2.imread(DIRECTORY + "/in.jpeg")

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/websocket", VideoWebSocketHandler),
    (r"/static", tornado.web.StaticFileHandler,
     dict(path=settings['static_path'])),
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()