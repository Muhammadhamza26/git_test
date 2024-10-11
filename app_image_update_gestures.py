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

    drag_and_drop_off = cv2.imread("static/icons/drag_and_drop/3.png")
    peace_sign_off = cv2.imread("static/icons/peace_sign/3.png")
    gesture_3_off = cv2.imread("static/icons/gesture_3/3.png")
    gesture_4_off = cv2.imread("static/icons/gesture_4/3.png")
    palm_off = cv2.imread("static/icons/palm/3.png")
    long_click_off = cv2.imread("static/icons/long_click/3.png")
    short_click_off = cv2.imread("static/icons/short_click/3.png")
    thumbs_up_off = cv2.imread("static/icons/thumbs_up/3.png")
    zoom_in_off = cv2.imread("static/icons/zoom_in/3.png")
    zoom_out_off = cv2.imread("static/icons/zoom_out/3.png")
    no_gesture_off = cv2.imread("static/icons/no_gesture/3.png")

    drag_and_drop = cv2.imread("static/icons/drag_and_drop/1.png")
    peace_sign = cv2.imread("static/icons/peace_sign/1.png")
    gesture_3 = cv2.imread("static/icons/gesture_3/1.png")
    gesture_4 = cv2.imread("static/icons/gesture_4/1.png")
    palm = cv2.imread("static/icons/palm/1.png")
    long_click = cv2.imread("static/icons/long_click/1.png")
    short_click = cv2.imread("static/icons/short_click/1.png")
    thumbs_up = cv2.imread("static/icons/thumbs_up/1.png")
    zoom_in = cv2.imread("static/icons/zoom_in/1.png")
    zoom_out = cv2.imread("static/icons/zoom_out/1.png")
    no_gesture = cv2.imread("static/icons/no_gesture/1.png")

    h, w, _ = drag_and_drop.shape

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
        img[0*h:h*1, 0:w] = drag_and_drop_off  # Drag and drop gesture
        img[1*h:h*2, 0:w] = peace_sign_off  # Peace sign
        img[2*h:h*3, 0:w] = gesture_3_off      # Gesture 3
        img[3*h:h*4, 0:w] = gesture_4_off      # Gesture 4
        img[4*h:h*5, 0:w] = palm_off            # Palm
        img[5*h:h*6, 0:w] = long_click_off     # Long Click
        img[6*h:h*7, 0:w] = short_click_off    # Short Click
        img[7*h:h*8, 0:w] = thumbs_up_off      # Thumbs Up
        img[8*h:h*9, 0:w] = zoom_in_off        # Zoom In
        img[9*h:h*10, 0:w] = zoom_out_off      # Zoom Out
        img[10*h:h*11, 0:w] = no_gesture_off   # No Gesture
        
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
                    gesture = zoom_in
                    text = "zoom_in"
                    p = 8
                else: 
                    gesture = zoom_out
                    text = "zoom_out"
                    p = 9
                gesture_active = True
                
            else:
                if fingers == [0,1,1,0,0]:
                    text = "Peace sign"
                    gesture = peace_sign
                    p = 1
                    gesture_active = True
                    
                if fingers == [0,1,1,1,0]:
                    text = "Gesture 3"
                    gesture = gesture_3
                    p = 2
                    gesture_active = True
                    
                if fingers == [0,1,1,1,1]:
                    text = "Gesture 4"
                    gesture = gesture_4
                    p = 3
                    gesture_active = True
                
                if fingers == [1,1,1,1,1]:
                    text = "Palm"
                    gesture = palm
                    p = 4
                    gesture_active = True
                    
                if fingers == [1, 0, 0, 0, 0]:
                    angle = detector.calculate_angle(lmList, 0, 4)  # Calculate angle between palm base and thumb
                    if -180 <= angle <= -170:
                        text = "Thumbs Up"
                        gesture = thumbs_up  # Assign the thumbs-up image
                        p = 7
                        gesture_active = True
                
                if fingers[1:] == [0,0,0,0] and all_previously_up:
                    text = "Drag and drop"
                    gesture = drag_and_drop
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
                        gesture = long_click
                        p = 5
                    else: 
                        # cv2.putText(img, "short click", (90, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                        text = "Short click"
                        gesture = short_click
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
                
            
            cv2.putText(img, text, (100, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
            # print(previously_up, previously_up_two, click_timer, timer_run)
        
        if not gesture_active:
            if no_gesture_timer >= no_gesture_timeout:
                text = "No Gesture"
                gesture = no_gesture
                p = 10
                # Display "no gesture" UI here
            else:
                no_gesture_timer += 1 / 30  # Increment timer based on frame rate
        else:
            no_gesture_timer = 0  # Reset timer when gesture is detected
        
        # else: text = ""
        try: img[p*h:h*(p+1), 0:w] = gesture
        except: pass
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