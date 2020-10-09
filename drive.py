# flask is a framework used to build webapps
from flask import Flask
import socketio
import eventlet
import numpy as np
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2

# web sockets are used to perform real-time communication between a client
# and a server
sio = socketio.Server()
app = Flask(__name__) #'__main__'
speed_limit = 10
# this decorator tells flask wich route to use
# if the user navigates to localhost:3000/home
# @app.route('/home')
# def greeting():
#     return 'Welcome!'
#
# if you go to loalhost:3000/home you will see 'Welcome!'
# if __name__ == '__main__':
#     app.run(port=3000)


def img_preprocess(img):
  # crop useless bottom and top of img
  img = img[60:135,:,:]
  #YUV is the suggested color palette from Nvidia. Y = luminosity, UV = image chromium
  img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
  #reduce noise and smoothing img
  img = cv2.GaussianBlur(img, (3,3), 0)
  # resize image
  img = cv2.resize(img, (200,66))
  #normalize
  img = img/255
  return img


@sio.on('telemetry')
def telemetry(sid, data):
    speed = float(data['speed'])
    # this is the image that will be use for prediction in the model
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])
    # predict the steering angle to take, given the image
    steering_angle = float(model.predict(image))
    throttle = 1.0 - speed/speed_limit
    print(f'{steering_angle} {throttle} {speed}')
    send_control(steering_angle, throttle)


#upon a connection, this method is fired
@sio.on('connect') #message, disconnect <-- possible event actions
def connect(sid, env):
    print('Connected')
    # the steering will be indicated by the model prediction
    send_control(0,0)


def send_control(steering_angle, throttle):
    # emit this event to the simulator
    sio.emit('steer', data={
        'steering_angle' : steering_angle.__str__(),
        'throttle' : throttle.__str__()
    })

if __name__ == '__main__':
    model = load_model('model/model_nvidia_aug.h5')
    app = socketio.Middleware(sio, app)
    # wsgi is the web interface, it takes the client requests
    #the tuple represents (ip,port). EMpty ip means that everyone is accepted
    eventlet.wsgi.server(eventlet.listen(('',4567)), app)
