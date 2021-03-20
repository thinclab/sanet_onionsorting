#!/usr/bin/env python3
# coding: utf8
import sys
from time import time

# append py2 in order to import rospy
sys.path.append('/usr/lib/python2.7/dist-packages')
import rospy
from rospy.numpy_msg import numpy_msg
from sensor_msgs.msg import Image, CameraInfo
# in order to import yolov5 under python3
sys.path.remove('/usr/lib/python2.7/dist-packages')
from sanet_onionsorting.srv import yolo_srv
import numpy as np
import copy
import rospkg

rospack = rospkg.RosPack()  # get an instance of RosPack with the default search paths
path = rospack.get_path('sanet_onionsorting')   # get the file path for sanet_onionsorting
sys.path.append(path + '/thirdparty/')
from yolov5.detect import YOLO

same_flag = 0
rgb_mem = None
depth_mem = None
weights = None

def grabrgb(msg):

    global rgb_mem
    if msg is not None:
        rgb_mem = copy.copy(msg)
    else:
        return

def getpred(msg):
    global weights, rgb_mem, depth_mem
    # print("Entered getpred func")
    start_time = time()
    bound_box_xy = []
    centxs = []
    centys = []
    colors = []
    y = YOLO(weights, conf_thres = 0.6)
    if rgb_mem is not None: 
        # thisimage = np.frombuffer(rgb_mem.data, dtype=np.uint8).reshape(rgb_mem.height, rgb_mem.width, -1).astype('float32')
        # print("\nThis image shape: \n",np.shape(thisimage))
        output = y.detect(rgb_mem)
        # print('output:   ',output)
        if output is not None:
            if len(output) > 0:   
                for det in output:
                    for *xyxy, conf, cls in det:
                        ''' 
                        NOTE: Useful link: https://miro.medium.com/max/597/1*85uPFWLrdVejJkWeie7cGw.png
                        Kinect image resolution is (1920,1080)
                        But numpy image shape is (1080,1920) becasue np takes image in the order height x width.
                        '''
                        tlx, tly, brx, bry = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                        centx, centy = int((tlx+brx)/2), int((tly+bry)/2)
                        if int(cls) == 0 or int(cls) == 1: 
                            # print("\ntlx, tly, brx, bry, cls: ",tlx, tly, brx, bry, int(cls))
                            # print(f"\nCentroid: {centx}, {centy}")
                            centxs.append(centx)
                            centys.append(centy)
                            colors.append(cls)
                        else:   pass
            else: pass   
        else: print("\nNo output from yolo received yet\n")
        rgb_mem = None
        print("\nTime taken by yolo is: ", time() - start_time)
        if len(centxs) > 0:
            print(f"\nFound {len(centxs)} onions\n")
            return centxs,centys,colors
        else:
            print("\nNo onions detected in frame\n")
            return [-1], [-1], [-1]
    else:
        print("\nNo RGB image received yet\n")
        return None, None, None


def main():
    global weights
    try:
        rospy.init_node("yolo_service")
        rospy.loginfo("Yolo service started")
        if len(sys.argv) < 2:
            weights = "best_gazebokinect.pt"   # Default weights
            print("Default weights chosen as gazebo weights")
        else:
            choice = sys.argv[1]

        if (choice == "real"):
            weights = "best_realkinect.pt"
            # for kinect v2
            print(f"{weights} weights selected with real kinect")
            rospy.Subscriber("/kinect2/hd/image_color", Image, grabrgb)
            # for kinect v2
            # rospy.Subscriber("/kinect2/hd/points", Image, grabdepth)
        elif (choice == "gazebo"):
            weights = "best_gazebokinect.pt"
            # for kinect gazebo
            print(f"{weights} weights selected with gazebo kinect")
            rospy.Subscriber("/kinect_V2/rgb/image_raw", Image, grabrgb)
            # for kinect gazebo
            # rospy.Subscriber("/kinect_V2/depth/points", Image, grabdepth)
        else:
            print(f"Unknown choice: {choice}. Please choose between real and gazebo.")

        service = rospy.Service("/get_predictions", yolo_srv, getpred)

    except rospy.ROSInterruptException:
        print(rospy.ROSInterruptException)
        return
    except KeyboardInterrupt:
        return
    rospy.spin()



if __name__ == '__main__':    
    main()