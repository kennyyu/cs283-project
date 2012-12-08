import base64
import cv2
import optical
import os
import threading
import tornado.ioloop
import tornado.web
import tornado.websocket

# Directory for temporary files
DIRECTORY = os.path.join(os.path.dirname(__file__), "tmp")

class MainHandler(tornado.web.RequestHandler):
    """
    Handles the request for the default index.html web page.
    """
    def get(self):
        self.render("index.html")

class VideoWebSocketHandler(tornado.websocket.WebSocketHandler):
    """
    Creates a web socket connection to the client for receiving frames
    and sending back the annotated frame and overall motion of the scene.
    """

    # Create a unique id per websocket
    id = 0
    lock = threading.Lock()

    def open(self):
        with self.__class__.lock:
            self.__class__.id += 1
            self.id = self.__class__.id
        self.file_in = DIRECTORY + "/in" + str(self.id) + ".jpeg"
        self.file_out = DIRECTORY + "/out" + str(self.id) + ".png"
        self.prev = None
        if not os.path.exists(DIRECTORY):
            os.makedirs(DIRECTORY)
        print "Websocket " + str(self.id) + " opened"

    def on_message(self, message):
        newim = self.parse_image(message)
        if self.prev == None:
            self.prev = newim
        else:
            direction, retim = optical.detect_and_display(self.prev, newim)
            cv2.imwrite(self.file_out, retim)
            self.prev = newim
            file = open(self.file_out, "r")
            self.write_message(direction + str(file.read()), binary=True)
            file.close()

    def on_close(self):
        os.remove(self.file_in)
        os.remove(self.file_out)
        print "Websocket " + str(self.id) + " closed"

    def parse_image(self, buf):
        img_str = base64.b64decode(buf)
        img = open(self.file_in, "w+");
        img.write(base64.b64decode(buf))
        img.close()
        return cv2.imread(self.file_in)

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/websocket", VideoWebSocketHandler),
    (r"/static", tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
], **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()