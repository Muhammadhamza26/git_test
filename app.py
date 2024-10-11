import cv2
import os
import threading
import signal

from flask import Flask, render_template, Response, jsonify

import hand_tracking as htm


app = Flask(__name__)
stop_stream = threading.Event()

def gen_frames():
    wCam, hCam = 640, 480
    cap = cv2.VideoCapture(1)
    cap.set(3, wCam)
    cap.set(4, hCam)
    detector = htm.handDetector(maxHands=1)

    previously_up = True
    all_previously_up = True
    previously_up_two = True
    previously_down_two = True
    click_timer = 0
    timer_run = False

    # no-gesture
    no_gesture_timer = 0
    gesture_active = False
    no_gesture_timeout = 0.5  # 2 seconds timeout

    vol = 0
    volBar = 400
    volPer = 0
    area = 0
    colorVol = (255, 0, 0)
    text = ""
    length = 0
    global current_gesture
    current_gesture = "new_gesture"

    save_video = False
    if save_video:
        result = cv2.VideoWriter('output/all_in_one_icon.mp4',
                            0x00000021, 24, (wCam, hCam))

    while not stop_stream.is_set():
    # while True:
        # 1. Find hand Landmarks
        
        success, img = cap.read()
        img = cv2.flip(img, 1)
        hands, img = detector.findHands_two(img)
        
        gesture_active = False
        
        if hands:
            lmList = hands[0]['lmList']
            fingers = detector.fingersUp_two(hands[0])
            
            if fingers == [1,1,0,0,0]:          # zoom
                lmList, bbox = detector.findPosition(img, draw=False)
                if len(lmList) != 0:
                    area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
                    if 50 < area < 1000:
                        # Find Distance between index and Thumb
                        length, img, lineInfo = detector.findDistance(4, 8, img, draw=False)
                        # print(length)
                        
                if length > 110: 
                    text = "zoom_in"
                    p = 8
                else: 
                    text = "zoom_out"
                    p = 9
                gesture_active = True
                
            else:
                if fingers == [0,1,1,0,0]:
                    text = "Peace sign"
                    p = 1
                    gesture_active = True
                    
                if fingers == [0,1,1,1,0]:
                    text = "Gesture 3"
                    p = 2
                    gesture_active = True
                    
                if fingers == [0,1,1,1,1]:
                    text = "Gesture 4"
                    p = 3
                    gesture_active = True
                
                if fingers == [1,1,1,1,1]:
                    text = "Palm"
                    p = 4
                    gesture_active = True
                    
                if fingers == [1, 0, 0, 0, 0]:
                    angle = detector.calculate_angle(lmList, 0, 4)  # Calculate angle between palm base and thumb
                    if -180 <= angle <= -170:
                        text = "Thumbs Up"
                        p = 7
                        gesture_active = True
                
                if fingers[1:] == [0,0,0,0] and all_previously_up:
                    text = "Drag and drop"
                    p = 0
                    gesture_active = True
                
                if fingers == [0,0,0,0,0] and previously_up and not previously_up_two:
                    timer_run = True
                
                if timer_run: click_timer += 1
                
                if fingers == [0,1,0,0,0] and not previously_up:
                    timer_run = False
                    cv2.circle(img, (lmList[8][1:]), 15, (0, 255, 0), cv2.FILLED)
                    if click_timer >= 10:
                        # cv2.putText(img, "long click", (400, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
                        text = "Long click"
                        p = 5
                    else: 
                        # cv2.putText(img, "short click", (90, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                        text = "Short click"
                        p = 6
                    click_timer = 0
                    gesture_active = True
                                   
                if fingers[1:3] == [1,1]: 
                    previously_up_two = True
                    previously_down_two = False
                else: previously_up_two = False
                if fingers == [0,0,0,0,0]:
                    previously_down_two = True
                
                if fingers[1:] == [1,1,1,1]: all_previously_up = True
                else: all_previously_up = False
                
                previously_up = fingers[1]
                
            
            # cv2.putText(img, text, (100, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
            # print(previously_up, previously_up_two, click_timer, timer_run)
        
        if not gesture_active:
            if no_gesture_timer >= no_gesture_timeout:
                text = "No Gesture"
                p = 10
                # Display "no gesture" UI here
            else:
                no_gesture_timer += 1 / 30  # Increment timer based on frame rate
        else:
            no_gesture_timer = 0  # Reset timer when gesture is detected
        
        current_gesture = text.lower().replace(" ", "_")
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
        
        
    cap.release()

@app.route('/get_gesture')
def get_gesture():
    # Returns the current gesture as JSON
    return jsonify(gesture=current_gesture)
    
@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/shutdown', methods=['POST'])
def shutdown():
    stop_stream.set()
    # Shutdown the server
    os.kill(os.getpid(), signal.SIGINT)
    return 'Server shutting down...'

# @app.route("/", methods=['GET', 'POST'])
@app.route("/")
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # threading.Thread(target=detect_gesture).start()
    app.run(debug=True, port=8080)